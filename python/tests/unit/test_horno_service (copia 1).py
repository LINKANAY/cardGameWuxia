"""Servicio del Horno — casos de uso sobre `SessionStore`.

El azar se inyecta con un callable fijo; los valores esperados están
calculados a mano siguiendo las fórmulas de `js/11-horno.js` (ver
`test_horno_nucleo` para la paridad pura). La vida máxima del reino 0 es 30
(`VIDA_BASE_HROE`).
"""

from __future__ import annotations

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.data.hierbas import INVENTARIO_INICIAL
from app.services.horno_service import HornoService
from app.state.session_store import SessionStore


def _tienda(tmp_path, monkeypatch, slot: str = "h1") -> SessionStore:
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    from app.config import reset_settings

    reset_settings()
    store = SessionStore()
    store.create(slot)
    return store


def _sembrar(store: SessionStore, slot: str, **cambios) -> None:
    """Aplica cambios directos a la partida (hierbas, vida, reino…)."""

    def mutador(partida):
        horno = partida.horno
        for clave, valor in cambios.items():
            if clave == "hierbas":
                horno["hierbas"].update(valor)
            elif clave == "pildoras":
                horno["pildoras"].update(valor)
            elif clave == "vida":
                partida.vida_hroe = valor
            elif clave == "reino":
                partida.nivel_reino = valor

    store.mutate(slot, mutador)


def _rngs(valores):
    it = iter(valores)
    return lambda: next(it)


class TestEstado:
    def test_inventario_inicial(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        estado = HornoService(store).estado("h1")
        assert estado["hierbas"] == dict(INVENTARIO_INICIAL)
        assert estado["pildoras"] == {}
        assert estado["refinadas"] == 0
        assert estado["fallos"] == 0
        assert estado["vida"] is None
        assert estado["vida_max"] == 30

    def test_partida_inexistente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(NotFoundError):
            HornoService(store).estado("nope")


class TestResumen:
    def test_usa_reino_de_la_partida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", reino=3)
        r = HornoService(store).resumen("h1", ["hs", "hs"])
        assert r["prob"] == 50  # 47 base + 3 de reino
        assert r["desglose"][-1] == ["Reino", 3]


class TestRefinar:
    def test_exito_consume_y_produce(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        # hs+hn: prob 39, puntos 3; rng: tirada 0, margen 1, ruido +4
        datos = HornoService(store).refinar(
            "h1", ["hs", "hn"], _rngs([0.0, 1.0, 1.0])
        )
        resultado = datos["resultado"]
        assert resultado["exito"] is True
        assert resultado["puntos"] == 10.0
        assert resultado["clave"] == "shield.media"
        assert datos["hierbas"]["hs"] == INVENTARIO_INICIAL["hs"] - 1
        assert datos["hierbas"]["hn"] == INVENTARIO_INICIAL["hn"] - 1
        assert datos["pildoras"] == {"shield.media": 1}
        assert datos["refinadas"] == 1
        assert datos["fallos"] == 0
        assert datos["vida"] is None  # el éxito no toca la vida

    def test_fallo_dania_y_suma_fallos(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", hierbas={"hv": 3}, vida=10)
        datos = HornoService(store).refinar(
            "h1", ["hv", "hv"], _rngs([0.99, 0.5, 0.0])
        )
        resultado = datos["resultado"]
        assert resultado["exito"] is False
        # 30 × lerp(6,14,0.5)=10% × 1.43 = 4.29 → 4
        assert resultado["danio"] == 4
        assert resultado["danio_real"] == 4
        assert resultado["clave"] == "waste.fallida"
        assert datos["vida"] == 6
        assert datos["fallos"] == 1
        assert datos["pildoras"] == {"waste.fallida": 1}
        # 3 sembradas − 2 consumidas = 1 restante
        assert datos["hierbas"]["hv"] == 1

    def test_fallo_no_mata(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", hierbas={"hv": 2}, vida=1)
        datos = HornoService(store).refinar(
            "h1", ["hv", "hv"], _rngs([0.99, 0.5, 0.0])
        )
        assert datos["vida"] == 1  # suelo 1: PUEDE_MATAR = false
        assert datos["resultado"]["danio_real"] == 0

    def test_fallo_con_vida_none_no_toca(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", hierbas={"hv": 2}, vida=None)
        datos = HornoService(store).refinar(
            "h1", ["hv", "hv"], _rngs([0.99, 0.5, 0.0])
        )
        assert datos["vida"] is None
        assert datos["resultado"]["danio_real"] == 0
        assert datos["fallos"] == 1

    def test_validacion_minimas(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).refinar("h1", ["hs"])
        assert excinfo.value.code == "hierbas_minimas"

    def test_validacion_maximas(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", hierbas={"hv": 4})
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).refinar(
                "h1", ["hs", "hn", "hv", "hv", "hv"]
            )
        assert excinfo.value.code == "hierbas_maximas"

    def test_validacion_hierba_desconocida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).refinar("h1", ["hs", "zzz"])
        assert excinfo.value.code == "hierba_desconocida"

    def test_validacion_material_insuficiente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        # el inventario inicial sólo tiene 1 lu
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).refinar("h1", ["lu", "lu"])
        assert excinfo.value.code == "hierbas_insuficientes"


class TestUsarPildora:
    def test_cura_media(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(
            store, "h1", pildoras={"heal.media": 1}, vida=10
        )
        datos = HornoService(store).usar_pildora("h1", "heal.media")
        assert datos["resultado"] == {
            "clave": "heal.media",
            "cura": 8,  # round(30 × 25%)
            "vida_antes": 10,
            "vida_despues": 18,
            "cura_pct": 25.0,
        }
        assert datos["vida"] == 18
        assert datos["pildoras"] == {}  # gasta la última

    def test_perfecta_no_pasa_de_maximo(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", pildoras={"heal.perfecta": 1}, vida=1)
        datos = HornoService(store).usar_pildora("h1", "heal.perfecta")
        # round(30 × 81.3%) = 24 → 25 < 30, sin tocar el techo
        assert datos["resultado"]["cura"] == 24
        assert datos["vida"] == 25

    def test_vida_completa_no_gasta(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", pildoras={"heal.media": 1}, vida=30)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).usar_pildora("h1", "heal.media")
        assert excinfo.value.code == "vida_completa"
        # no se gastó
        assert store.get_or_create("h1").horno["pildoras"] == {
            "heal.media": 1
        }

    def test_vida_none_tambien_completa(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", pildoras={"heal.media": 1}, vida=None)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).usar_pildora("h1", "heal.media")
        assert excinfo.value.code == "vida_completa"

    def test_sin_stock(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(store, "h1", vida=10)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).usar_pildora("h1", "heal.media")
        assert excinfo.value.code == "pildora_inexistente"

    def test_clave_invalida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _sembrar(
            store, "h1", pildoras={"no.existe": 1}, vida=10
        )
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).usar_pildora("h1", "no.existe")
        assert excinfo.value.code == "clave_invalida"


class TestAgregarHierbas:
    def test_dict_explicito(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        datos = HornoService(store).agregar_hierbas(
            "h1", {"nf": 2, "hs": 1}
        )
        assert datos["anadidas"] == {"nf": 2, "hs": 1}
        assert datos["hierbas"]["nf"] == 2
        assert datos["hierbas"]["hs"] == INVENTARIO_INICIAL["hs"] + 1

    def test_entero_sortea_por_peso(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        datos = HornoService(store).agregar_hierbas(
            "h1", 1, rng=_rngs([0.0])
        )
        assert datos["anadidas"] == {"hs": 1}
        assert datos["hierbas"]["hs"] == INVENTARIO_INICIAL["hs"] + 1

    def test_cantidad_invalida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).agregar_hierbas("h1", 0)
        assert excinfo.value.code == "cantidad_invalida"
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).agregar_hierbas("h1", {"nf": 0})
        assert excinfo.value.code == "cantidad_invalida"

    def test_hierba_desconocida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as excinfo:
            HornoService(store).agregar_hierbas("h1", {"zzz": 1})
        assert excinfo.value.code == "hierba_desconocida"


class TestBotinVictoria:
    def test_dificultad_baja_una_hierba(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        datos = HornoService(store).botin_victoria(
            "h1", 0, rng=_rngs([0.0, 0.0])
        )
        assert datos["hierbas"] == {"hs": 1}
        assert datos["dificultad"] == 0
        assert datos["mensaje"] == "Hierba Espiritual ×1"
        assert (
            store.get_or_create("h1").horno["hierbas"]["hs"]
            == INVENTARIO_INICIAL["hs"] + 1
        )

    def test_jefe_suma_bonus(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        datos = HornoService(store).botin_victoria(
            "h1", 4, rng=_rngs([0.0, 0.0, 0.0])
        )
        assert datos["hierbas"] == {"hs": 2}

    def test_es_jefe_explícito(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        datos = HornoService(store).botin_victoria(
            "h1", 0, es_jefe=True, rng=_rngs([0.0, 0.0, 0.0])
        )
        assert datos["hierbas"] == {"hs": 2}


class TestReiniciar:
    def test_vuelve_al_inventario_inicial(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        servicio = HornoService(store)
        servicio.refinar("h1", ["hs", "hn"], _rngs([0.0, 1.0, 1.0]))
        servicio.agregar_hierbas("h1", {"nf": 3})
        datos = servicio.reiniciar("h1")
        assert datos["hierbas"] == dict(INVENTARIO_INICIAL)
        assert datos["pildoras"] == {}
        assert datos["refinadas"] == 0
        assert datos["fallos"] == 0
