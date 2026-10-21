"""Servicio del Jardín — casos de uso sobre `SessionStore`.

El reloj (`_ahora`) y el azar (`_aleatorio`) se congelan con
`monkeypatch`: los valores esperados están calculados a mano con las
fórmulas de `app.engine.jardin` (ver `test_jardin_nucleo` para la
paridad pura).
"""

from __future__ import annotations

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.data.hierbas import INVENTARIO_INICIAL
from app.services.jardin_service import JardinService
from app.state.session_store import SessionStore

#: epoch ms congelado para todas las operaciones de estos tests.
T0 = 1_760_000_000_000


def _tienda(tmp_path, monkeypatch, slot: str = "j1") -> SessionStore:
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    from app.config import reset_settings

    reset_settings()
    store = SessionStore()
    store.create(slot)
    monkeypatch.setattr(
        JardinService, "_ahora", staticmethod(lambda: T0)
    )
    return store


def _preparar(store: SessionStore, slot: str, **cambios) -> None:
    """Aplica cambios directos a la partida (reino, stn, inventarios…)."""

    def mutador(partida):
        for clave, valor in cambios.items():
            if clave == "reino":
                partida.nivel_reino = valor
            elif clave == "piedras":
                partida.piedras_espirituales = valor
            elif clave == "materiales":
                partida.materiales.update(valor)
            elif clave == "semillas":
                partida.semillas = dict(valor)
            elif clave == "formaciones":
                partida.formaciones_crecimiento = dict(valor)
            elif clave == "nivel":
                partida.jardin["nivel"] = valor
                from app.data.jardin import MEJORAS

                partida.jardin["casillas"] = [None] * MEJORAS[valor].casillas
            elif clave == "hierbas":
                partida.horno["hierbas"].update(valor)

    store.mutate(slot, mutador)


def _rngs(valores):
    it = iter(valores)
    return lambda: next(it)


class TestEstado:
    def test_inicial(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        estado = JardinService(store).estado("j1")
        assert estado["nivel"] == 0
        assert estado["casillas"] == [None] * 4
        assert estado["formacion"] is None
        assert estado["semillas"] == {"hs": 2}
        assert estado["formaciones"] == {}
        assert estado["reino"] == 0
        assert estado["materiales"] == {"h": 0, "n": 0, "p": 0}
        assert estado["piedras"] == 30
        assert estado["siguiente_mejora"] == {
            "nivel": 1,
            "casillas": 6,
            "coste": {"h": 15, "n": 5, "p": 5},
            "reino_min": 2,
        }
        assert estado["ahora"] == T0

    def test_partida_inexistente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(NotFoundError):
            JardinService(store).estado("nope")


class TestSembrar:
    def test_consume_semillas(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        servicio = JardinService(store)
        estado = servicio.sembrar("j1", 0, "hs")
        assert estado["casillas"][0] == {
            "planta": "hs",
            "siembra": T0,
            "reducido": 0,
            "duracion_ms": 120_000,
            "restante_ms": 120_000,
            "progreso": 0.0,
            "listo": False,
            "coste_piedras": 94,
        }
        assert estado["semillas"] == {"hs": 1}
        servicio.sembrar("j1", 1, "hs")
        assert servicio.estado("j1")["semillas"] == {}

    def test_sin_semillas(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        servicio.sembrar("j1", 1, "hs")
        with pytest.raises(ValidationError) as error:
            servicio.sembrar("j1", 2, "hs")
        assert error.value.code == "semillas_insuficientes"

    def test_casilla_ocupada(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        with pytest.raises(ValidationError) as error:
            servicio.sembrar("j1", 0, "hs")
        assert error.value.code == "casilla_ocupada"

    @pytest.mark.parametrize("indice", [-1, 4, 99])
    def test_casilla_fuera_de_rango(self, tmp_path, monkeypatch, indice):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).sembrar("j1", indice, "hs")
        assert error.value.code == "casilla_invalida"

    def test_planta_desconocida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).sembrar("j1", 0, "zz")
        assert error.value.code == "planta_desconocida"

    def test_planta_bloqueada_por_reino(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", semillas={"ff": 1})
        servicio = JardinService(store)
        with pytest.raises(ValidationError) as error:
            servicio.sembrar("j1", 0, "ff")  # rareza 1, reino 0
        assert error.value.code == "planta_bloqueada"
        _preparar(store, "j1", reino=1)
        assert servicio.sembrar("j1", 0, "ff")["casillas"][0]["planta"] == "ff"

    def test_partida_inexistente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(NotFoundError):
            JardinService(store).sembrar("nope", 0, "hs")


class TestCosechar:
    def test_cosecha_lista(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        estado = servicio.cosechar("j1", 0, ahora=T0 + 120_000)
        assert estado["resultado"] == {
            "indice": 0,
            "planta": "hs",
            "hierbas": 1,
        }
        assert estado["casillas"][0] is None
        esperado = dict(INVENTARIO_INICIAL)
        esperado["hs"] = esperado.get("hs", 0) + 1
        # el estado no expone el Horno; mirar la partida guardada
        partida = store.get_or_create("j1")
        assert partida.horno["hierbas"] == esperado
        assert partida.semillas == {"hs": 1}  # la 2ª sigue en stock

    def test_rendimiento_por_rareza(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", reino=3, semillas={"gm": 1})
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "gm")
        estado = servicio.cosechar("j1", 0, ahora=T0 + 720_000)
        assert estado["resultado"]["hierbas"] == 2

    def test_pendiente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        with pytest.raises(ValidationError) as error:
            servicio.cosechar("j1", 0, ahora=T0 + 118_999)
        assert error.value.code == "planta_pendiente"

    def test_casilla_vacia(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).cosechar("j1", 0)
        assert error.value.code == "casilla_vacia"


class TestAcelerar:
    def _preparado(self, tmp_path, monkeypatch) -> JardinService:
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", piedras=100_000)
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        return servicio

    def test_una_piedra_quita_5_por_ciento(self, tmp_path, monkeypatch):
        servicio = self._preparado(tmp_path, monkeypatch)
        estado = servicio.acelerar("j1", 0, 1)
        assert estado["resultado"] == {
            "indice": 0,
            "reducido": 6_000,
            "restante_ms": 114_000,
            "gastadas": 1,
        }
        assert estado["casillas"][0]["reducido"] == 6_000
        assert estado["piedras"] == 99_999

    def test_golpe_total_deja_lista(self, tmp_path, monkeypatch):
        servicio = self._preparado(tmp_path, monkeypatch)
        estado = servicio.acelerar("j1", 0, 94)
        assert estado["casillas"][0]["restante_ms"] == 0
        assert estado["casillas"][0]["listo"] is True
        assert estado["piedras"] == 100_000 - 94

    def test_mas_del_coste(self, tmp_path, monkeypatch):
        servicio = self._preparado(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            servicio.acelerar("j1", 0, 95)
        assert error.value.code == "piedras_invalidas"

    def test_cero_piedras(self, tmp_path, monkeypatch):
        servicio = self._preparado(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            servicio.acelerar("j1", 0, 0)
        assert error.value.code == "piedras_invalidas"

    def test_stn_insuficientes(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)  # stn = 30
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        with pytest.raises(ValidationError) as error:
            servicio.acelerar("j1", 0, 94)
        assert error.value.code == "piedras_insuficientes"

    def test_casilla_vacia(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).acelerar("j1", 0, 1)
        assert error.value.code == "casilla_vacia"

    def test_ya_lista(self, tmp_path, monkeypatch):
        servicio = self._preparado(tmp_path, monkeypatch)
        servicio.acelerar("j1", 0, 94)
        with pytest.raises(ValidationError) as error:
            servicio.acelerar("j1", 0, 1)
        assert error.value.code == "planta_lista"

    def test_acumulable(self, tmp_path, monkeypatch):
        servicio = self._preparado(tmp_path, monkeypatch)
        servicio.acelerar("j1", 0, 1)
        estado = servicio.acelerar("j1", 0, 1)
        assert estado["casillas"][0]["reducido"] == 11_700
        assert estado["casillas"][0]["restante_ms"] == 108_300


class TestMejorar:
    def test_reino_insuficiente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).mejorar("j1")
        assert error.value.code == "reino_insuficiente"

    def test_materiales_insuficientes(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", reino=2)
        with pytest.raises(ValidationError) as error:
            JardinService(store).mejorar("j1")
        assert error.value.code == "materiales_insuficientes"

    def test_mejora_de_pagina(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(
            store,
            "j1",
            reino=2,
            materiales={"h": 15, "n": 5, "p": 5},
        )
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        estado = servicio.mejorar("j1")
        assert estado["resultado"] == {
            "nivel": 1,
            "casillas": 6,
            "coste": {"h": 15, "n": 5, "p": 5},
        }
        assert estado["nivel"] == 1
        assert len(estado["casillas"]) == 6
        # la planta sembrada sobrevive a la ampliación
        assert estado["casillas"][0]["planta"] == "hs"
        assert estado["materiales"] == {"h": 0, "n": 0, "p": 0}
        # y el tope de materiales quedó cubierto (nivel 2 = reino 5)
        with pytest.raises(ValidationError) as error:
            servicio.mejorar("j1")
        assert error.value.code == "reino_insuficiente"

    def test_al_tope(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(
            store, "j1", reino=14, nivel=3, materiales={"h": 999}
        )
        with pytest.raises(ValidationError) as error:
            JardinService(store).mejorar("j1")
        assert error.value.code == "mejora_no_disponible"


class TestFormacion:
    def test_sin_copias(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).equipar_formacion("j1", "fc1")
        assert error.value.code == "formacion_insuficiente"

    def test_desconocida(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(ValidationError) as error:
            JardinService(store).equipar_formacion("j1", "zz")
        assert error.value.code == "formacion_desconocida"

    def test_equipar_y_quitar(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", formaciones={"fc1": 1})
        servicio = JardinService(store)
        servicio.sembrar("j1", 0, "hs")
        estado = servicio.equipar_formacion("j1", "fc1")
        assert estado["formacion"] == "fc1"
        # la formación acelera al instante lo que ya estaba sembrado
        assert estado["casillas"][0]["duracion_ms"] == 114_000
        assert estado["casillas"][0]["restante_ms"] == 114_000
        # el inventario no se gasta
        assert estado["formaciones"] == {"fc1": 1}
        quitada = servicio.equipar_formacion("j1", None)
        assert quitada["formacion"] is None
        assert quitada["casillas"][0]["restante_ms"] == 120_000


class TestEntregas:
    def test_botin_boticario(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        estado = JardinService(store).botin_boticario(
            "j1", 0, rng=_rngs([0.0, 0.0, 0.0, 0.0, 0.0])
        )
        assert estado["resultado"] == {
            "semillas": {"hs": 2},
            "formacion": "fc1",
            "materiales": {"h": 2, "p": 1, "n": 0},
        }
        assert estado["semillas"] == {"hs": 4}  # 2 iniciales + 2
        assert estado["formaciones"] == {"fc1": 1}
        assert estado["materiales"] == {"h": 2, "n": 0, "p": 1}

    def test_botin_partida_inexistente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(NotFoundError):
            JardinService(store).botin_boticario("nope", 0)

    def test_regalo_ascenso(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", reino=1)
        estado = JardinService(store).regalo_ascenso(
            "j1", rng=_rngs([0.0, 0.0])
        )
        # rareza 1 → primera especie (ff); formación de rareza 0 → fc1
        assert estado["resultado"] == {"semilla": "ff", "formacion": "fc1"}
        assert estado["semillas"] == {"hs": 2, "ff": 1}
        assert estado["formaciones"] == {"fc1": 1}

    def test_regalo_sin_especie_nueva(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        _preparar(store, "j1", reino=2)
        estado = JardinService(store).regalo_ascenso(
            "j1", rng=_rngs([0.0])
        )
        assert estado["resultado"]["semilla"] is None
        assert estado["resultado"]["formacion"] == "fc1"

    def test_regalo_partida_inexistente(self, tmp_path, monkeypatch):
        store = _tienda(tmp_path, monkeypatch)
        with pytest.raises(NotFoundError):
            JardinService(store).regalo_ascenso("nope")
