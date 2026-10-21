"""API del Jardín Medicinal — flujos completos contra la app de prueba.

El reloj del servidor se congela con `monkeypatch` sobre
`JardinService._ahora` (mismo truco que `_aleatorio` en el horno):
así los tiempos de crecimiento son exactos y los tests no flaquean.
"""

from __future__ import annotations

import pytest

from app.services.jardin_service import JardinService

#: epoch ms congelado para todas las operaciones de estos tests.
T0 = 1_760_000_000_000


@pytest.fixture(autouse=True)
def _reloj_congelado(monkeypatch):
    monkeypatch.setattr(JardinService, "_ahora", staticmethod(lambda: T0))


def _crear(cliente, slot: str) -> None:
    r = cliente.post("/api/game/new", json={"slot": slot})
    assert r.status_code == 200


def _preparar(cliente, slot: str, **cambios) -> None:
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

    cliente.app.state.store.mutate(slot, mutador)


def _nivel(slot_partida, nivel: int, cliente) -> None:
    """Fija el nivel de la cuadrícula con el tamaño que le corresponde."""

    def mutador(partida):
        from app.data.jardin import MEJORAS

        partida.jardin["nivel"] = nivel
        partida.jardin["casillas"] = [None] * MEJORAS[nivel].casillas

    cliente.app.state.store.mutate(slot_partida, mutador)


def _error(cliente, url: str, cuerpo: dict | None = None) -> str:
    """POST que debe fallar con 400; devuelve el `code` del envelope."""
    r = cliente.post(url, json=cuerpo)
    assert r.status_code == 400, r.text
    return r.json()["error"]["code"]


class TestEstado:
    def test_inicial(self, cliente):
        _crear(cliente, "j1")
        r = cliente.get("/api/game/j1/jardin/estado")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["slot"] == "j1"
        assert data["nivel"] == 0
        assert data["casillas"] == [None] * 4
        assert data["semillas"] == {"hs": 2}
        assert data["formaciones"] == {}
        assert data["piedras"] == 30
        assert data["ahora"] == T0
        assert data["siguiente_mejora"]["casillas"] == 6

    def test_partida_inexistente(self, cliente):
        r = cliente.get("/api/game/nope/jardin/estado")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "not_found"


class TestCatalogo:
    def test_data_jardin(self, cliente):
        r = cliente.get("/api/data/jardin")
        assert r.status_code == 200
        data = r.json()["data"]
        ids = [planta["identificador"] for planta in data["hierbas"]]
        assert ids == [
            "hs", "rj", "hn", "ff", "rd", "ll", "hv", "gm", "lu", "ed", "nf",
        ]
        assert data["hierbas"][0] == {
            "identificador": "hs",
            "nombre": "Hierba Espiritual",
            "glifo": "灵",
            "rareza": 0,
            "duracion_ms": 120_000,
            "rendimiento": 1,
            "reino_min": 0,
        }
        # rareza 4: 45 min, 3 hierbas, reino 7
        assert data["hierbas"][-1]["duracion_ms"] == 2_700_000
        assert data["hierbas"][-1]["rendimiento"] == 3
        assert data["hierbas"][-1]["reino_min"] == 7
        assert len(data["formaciones"]) == 6
        assert data["formaciones"][0]["descuento"] == 0.05
        assert data["formaciones"][-1]["descuento"] == 0.30
        assert data["mejoras"] == [
            {"nivel": 0, "casillas": 4, "coste": {}, "reino_min": 0},
            {
                "nivel": 1, "casillas": 6,
                "coste": {"h": 15, "n": 5, "p": 5}, "reino_min": 2,
            },
            {
                "nivel": 2, "casillas": 9,
                "coste": {"h": 30, "n": 15, "p": 15}, "reino_min": 5,
            },
            {
                "nivel": 3, "casillas": 12,
                "coste": {"h": 60, "n": 30, "p": 30}, "reino_min": 8,
            },
        ]


class TestSembrar:
    def test_flujo(self, cliente):
        _crear(cliente, "j2")
        cuerpo = {"indice": 0, "planta": "hs"}
        r = cliente.post("/api/game/j2/jardin/sembrar", json=cuerpo)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["casillas"][0]["planta"] == "hs"
        assert data["casillas"][0]["listo"] is False
        assert data["semillas"] == {"hs": 1}
        # toda mutación lleva el snapshot xcg3 actualizado
        assert data["snapshot"]["sd"] == {"hs": 1}

    def test_errores(self, cliente):
        _crear(cliente, "j3")
        url = "/api/game/j3/jardin/sembrar"
        codigo = _error(cliente, url, {"indice": 0, "planta": "zz"})
        assert codigo == "planta_desconocida"
        codigo = _error(cliente, url, {"indice": 0, "planta": "ff"})
        assert codigo == "planta_bloqueada"
        codigo = _error(cliente, url, {"indice": 9, "planta": "hs"})
        assert codigo == "casilla_invalida"
        cliente.post(url, json={"indice": 0, "planta": "hs"})
        codigo = _error(cliente, url, {"indice": 0, "planta": "hs"})
        assert codigo == "casilla_ocupada"
        cliente.post(url, json={"indice": 1, "planta": "hs"})
        codigo = _error(cliente, url, {"indice": 2, "planta": "hs"})
        assert codigo == "semillas_insuficientes"


class TestAcelerarCosechar:
    def test_ciclo_completo(self, cliente):
        _crear(cliente, "j4")
        _preparar(cliente, "j4", piedras=1_000)
        url_s = "/api/game/j4/jardin/sembrar"
        cliente.post(url_s, json={"indice": 0, "planta": "hs"})
        # 94 piedras dejan la hs lista (coste exacto a los 2 min)
        r = cliente.post(
            "/api/game/j4/jardin/acelerar",
            json={"indice": 0, "piedras": 94},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["casillas"][0]["restante_ms"] == 0
        assert data["casillas"][0]["listo"] is True
        assert data["piedras"] == 906
        assert data["snapshot"]["stn"] == 906

        r = cliente.post("/api/game/j4/jardin/cosechar", json={"indice": 0})
        assert r.status_code == 200
        resultado = r.json()["data"]["resultado"]
        assert resultado == {"indice": 0, "planta": "hs", "hierbas": 1}
        assert r.json()["data"]["casillas"][0] is None

        # y el Horno recibió la hierba
        r = cliente.get("/api/game/j4/horno/estado")
        assert r.json()["data"]["hierbas"]["hs"] >= 1

    def test_errores(self, cliente):
        _crear(cliente, "j5")
        url_a = "/api/game/j5/jardin/acelerar"
        url_c = "/api/game/j5/jardin/cosechar"
        assert _error(cliente, url_a, {"indice": 0, "piedras": 1}) == (
            "casilla_vacia"
        )
        assert _error(cliente, url_c, {"indice": 0}) == "casilla_vacia"
        cliente.post(
            "/api/game/j5/jardin/sembrar",
            json={"indice": 0, "planta": "hs"},
        )
        assert _error(cliente, url_c, {"indice": 0}) == "planta_pendiente"
        codigo = _error(cliente, url_a, {"indice": 0, "piedras": 95})
        assert codigo == "piedras_invalidas"
        codigo = _error(cliente, url_a, {"indice": 0, "piedras": 94})
        assert codigo == "piedras_insuficientes"
        _preparar(cliente, "j5", piedras=1_000)
        # piedras = 0 lo rechaza el servicio con envelope (no el schema)
        assert _error(cliente, url_a, {"indice": 0, "piedras": 0}) == (
            "piedras_invalidas"
        )
        cliente.post(url_a, json={"indice": 0, "piedras": 94})
        codigo = _error(cliente, url_a, {"indice": 0, "piedras": 1})
        assert codigo == "planta_lista"


class TestMejorar:
    def test_flujo(self, cliente):
        _crear(cliente, "j6")
        url = "/api/game/j6/jardin/mejorar"
        assert _error(cliente, url) == "reino_insuficiente"
        _preparar(
            cliente, "j6", reino=2, materiales={"h": 15, "n": 5, "p": 5}
        )
        r = cliente.post(url)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["nivel"] == 1
        assert len(data["casillas"]) == 6
        assert data["materiales"] == {"h": 0, "n": 0, "p": 0}
        assert data["siguiente_mejora"]["reino_min"] == 5
        # sin reino 5 no avanza la siguiente mejora
        assert _error(cliente, url) == "reino_insuficiente"

    def test_materiales_insuficientes(self, cliente):
        _crear(cliente, "j7")
        _preparar(cliente, "j7", reino=2)
        codigo = _error(cliente, "/api/game/j7/jardin/mejorar")
        assert codigo == "materiales_insuficientes"

    def test_al_tope(self, cliente):
        _crear(cliente, "j8")
        _preparar(cliente, "j8", reino=14)
        _nivel("j8", 3, cliente)
        codigo = _error(cliente, "/api/game/j8/jardin/mejorar")
        assert codigo == "mejora_no_disponible"


class TestFormacion:
    def test_flujo(self, cliente):
        _crear(cliente, "j9")
        url = "/api/game/j9/jardin/formacion"
        codigo = _error(cliente, url, {"identificador": "fc1"})
        assert codigo == "formacion_insuficiente"
        _preparar(cliente, "j9", formaciones={"fc1": 1})
        r = cliente.post(url, json={"identificador": "fc1"})
        assert r.status_code == 200
        assert r.json()["data"]["formacion"] == "fc1"
        r = cliente.post(url, json={"identificador": None})
        assert r.status_code == 200
        assert r.json()["data"]["formacion"] is None
        codigo = _error(cliente, url, {"identificador": "zz"})
        assert codigo == "formacion_desconocida"


class TestPersistencia:
    def test_save_lleva_las_claves_nuevas(self, cliente):
        _crear(cliente, "j10")
        cliente.post(
            "/api/game/j10/jardin/sembrar",
            json={"indice": 0, "planta": "hs"},
        )
        snapshot = cliente.app.state.store.snapshot("j10")
        assert snapshot["jdn"]["casillas"][0]["planta"] == "hs"
        assert snapshot["sd"] == {"hs": 1}
        assert snapshot["fg"] == {}
        # el estado vuelve a leerse de esa partida tras «recargar»
        r = cliente.get("/api/game/j10/jardin/estado")
        assert r.json()["data"]["casillas"][0]["planta"] == "hs"
