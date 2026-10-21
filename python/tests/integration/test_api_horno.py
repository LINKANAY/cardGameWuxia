"""API del Horno de Alquimia — flujos completos contra la app de prueba.

El azar se congela con `monkeypatch` sobre `HornoService._aleatorio`
(mismo truco que en los tests de gacha/mercado): el servicio pide un
nuevo callback por operación, que en pruebas devuelve los valores de
una lista fija.
"""

from __future__ import annotations

import pytest

from app.data.hierbas import INVENTARIO_INICIAL
from app.services.horno_service import HornoService


def _crear(cliente, slot: str) -> None:
    r = cliente.post("/api/game/new", json={"slot": slot})
    assert r.status_code == 200


def _rng_fijo(monkeypatch, valores) -> None:
    """Sustituye el RNG del servicio por una lista fija de valores."""

    def falso():
        it = iter(valores)
        return lambda: next(it)

    monkeypatch.setattr(HornoService, "_aleatorio", staticmethod(falso))


def _sembrar(cliente, slot: str, **cambios) -> None:
    store = cliente.app.state.store

    def mutador(partida):
        horno = partida.horno
        for clave, valor in cambios.items():
            if clave == "hierbas":
                horno["hierbas"].update(valor)
            elif clave == "pildoras":
                horno["pildoras"].update(valor)
            elif clave == "vida":
                partida.vida_hroe = valor

    store.mutate(slot, mutador)


def _total_hierbas(cliente, slot: str) -> int:
    r = cliente.get(f"/api/game/{slot}/horno/estado")
    return sum(r.json()["data"]["hierbas"].values())


class TestEstado:
    def test_inventario_inicial(self, cliente):
        _crear(cliente, "h1")
        r = cliente.get("/api/game/h1/horno/estado")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["slot"] == "h1"
        assert data["hierbas"] == dict(INVENTARIO_INICIAL)
        assert data["pildoras"] == {}
        assert data["refinadas"] == 0
        assert data["fallos"] == 0
        assert data["vida"] is None
        assert data["vida_max"] == 30

    def test_partida_inexistente(self, cliente):
        r = cliente.get("/api/game/nope/horno/estado")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "not_found"


class TestResumen:
    def test_armonía_de_dos_heal(self, cliente):
        _crear(cliente, "h2")
        r = cliente.post(
            "/api/game/h2/horno/resumen", json={"ids": ["hs", "hs"]}
        )
        assert r.status_code == 200
        resumen = r.json()["data"]["resumen"]
        assert resumen["prob"] == 47
        assert resumen["tipo"] == "heal"
        assert resumen["armonia"] is True

    def test_discordia_tres_tipos(self, cliente):
        _crear(cliente, "h3")
        r = cliente.post(
            "/api/game/h3/horno/resumen",
            json={"ids": ["hs", "hn", "ll"]},
        )
        resumen = r.json()["data"]["resumen"]
        assert resumen["prob"] == 35
        assert resumen["discordia"] is True
        assert resumen["tipo"] == "gold"


class TestRefinar:
    def test_exito_persiste_en_snapshot(self, cliente, monkeypatch):
        _crear(cliente, "h4")
        _rng_fijo(monkeypatch, [0.0, 1.0, 1.0])
        r = cliente.post(
            "/api/game/h4/horno/refinar", json={"ids": ["hs", "hn"]}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["resultado"]["exito"] is True
        assert data["resultado"]["clave"] == "shield.media"
        assert data["refinadas"] == 1
        # la partida persistida (xcg3) lleva la píldora y el inventario
        snap = cliente.app.state.store.snapshot("h4")
        assert snap["xn"]["pildoras"] == {"shield.media": 1}
        assert snap["xn"]["hierbas"]["hs"] == INVENTARIO_INICIAL["hs"] - 1

    def test_fallo_dania_vida(self, cliente, monkeypatch):
        _crear(cliente, "h5")
        _sembrar(cliente, "h5", hierbas={"hv": 2}, vida=10)
        _rng_fijo(monkeypatch, [0.99, 0.5, 0.0])
        r = cliente.post(
            "/api/game/h5/horno/refinar", json={"ids": ["hv", "hv"]}
        )
        data = r.json()["data"]
        assert data["resultado"]["exito"] is False
        assert data["resultado"]["danio"] == 4
        assert data["vida"] == 6
        assert data["pildoras"] == {"waste.fallida": 1}

    def test_menos_de_dos_rechazado(self, cliente):
        _crear(cliente, "h6")
        r = cliente.post(
            "/api/game/h6/horno/refinar", json={"ids": ["hs"]}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "hierbas_minimas"

    def test_material_insuficiente_rechazado(self, cliente):
        _crear(cliente, "h7")
        r = cliente.post(
            "/api/game/h7/horno/refinar", json={"ids": ["lu", "lu"]}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "hierbas_insuficientes"

    def test_hierba_desconocida_rechazada(self, cliente):
        _crear(cliente, "h8")
        r = cliente.post(
            "/api/game/h8/horno/refinar", json={"ids": ["hs", "zzz"]}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "hierba_desconocida"


class TestUsar:
    def test_cura_fuera_de_combate(self, cliente):
        _crear(cliente, "u1")
        _sembrar(cliente, "u1", pildoras={"heal.media": 1}, vida=10)
        r = cliente.post(
            "/api/game/u1/horno/usar", json={"clave": "heal.media"}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["resultado"]["cura"] == 8
        assert data["vida"] == 18
        assert data["pildoras"] == {}
        snap = cliente.app.state.store.snapshot("u1")
        assert snap["hp"] == 18

    def test_vida_completa_rechazada_sin_gastar(self, cliente):
        _crear(cliente, "u2")
        _sembrar(cliente, "u2", pildoras={"heal.media": 1}, vida=30)
        r = cliente.post(
            "/api/game/u2/horno/usar", json={"clave": "heal.media"}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "vida_completa"
        snap = cliente.app.state.store.snapshot("u2")
        assert snap["xn"]["pildoras"] == {"heal.media": 1}

    def test_sin_stock_rechazado(self, cliente):
        _crear(cliente, "u3")
        _sembrar(cliente, "u3", vida=10)
        r = cliente.post(
            "/api/game/u3/horno/usar", json={"clave": "heal.media"}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "pildora_inexistente"

    def test_clave_invalida_rechazada(self, cliente):
        _crear(cliente, "u4")
        _sembrar(cliente, "u4", pildoras={"no.existe": 1}, vida=10)
        r = cliente.post(
            "/api/game/u4/horno/usar", json={"clave": "no.existe"}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "clave_invalida"


class TestReiniciar:
    def test_vuelve_al_inventario_inicial(self, cliente, monkeypatch):
        _crear(cliente, "r1")
        _rng_fijo(monkeypatch, [0.0, 1.0, 1.0])
        cliente.post(
            "/api/game/r1/horno/refinar", json={"ids": ["hs", "hn"]}
        )
        r = cliente.post("/api/game/r1/horno/reiniciar")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["hierbas"] == dict(INVENTARIO_INICIAL)
        assert data["pildoras"] == {}


class TestBotinEnVictoria:
    def test_ganar_combate_suelta_hierbas(
        self, cliente, monkeypatch
    ):
        """El hook de victoria añade botín al evento y al inventario."""
        from app.engine.combat import comprobar_fin

        _crear(cliente, "b1")
        _rng_fijo(monkeypatch, [0.0, 0.0])
        cliente.post("/api/game/b1/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("b1")
        estado.E.hp = 0
        comprobar_fin(estado)
        campaña = servicio._consumir_eventos("b1", estado)
        victoria = next(e for e in campaña if e["tipo"] == "victoria")
        assert victoria["botin"]["hierbas"] == {"hs": 1}
        assert victoria["botin"]["dificultad"] == 0
        assert victoria["botin"]["mensaje"] == "Hierba Espiritual ×1"
        assert (
            cliente.app.state.store.snapshot("b1")["xn"]["hierbas"]["hs"]
            == INVENTARIO_INICIAL["hs"] + 1
        )

    def test_muerte_no_suelta_botin(self, cliente, monkeypatch):
        """La rama de muerte del evento no toca el horno."""
        _crear(cliente, "b2")
        antes = _total_hierbas(cliente, "b2")
        cliente.post("/api/game/b2/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("b2")
        estado.P.hp = 0
        from app.engine.combat import comprobar_fin

        comprobar_fin(estado)
        campaña = servicio._consumir_eventos("b2", estado)
        assert any(e["tipo"] == "muerte" for e in campaña)
        assert _total_hierbas(cliente, "b2") == antes
