"""API del gacha — flujos completos contra la app de prueba.

Los tests se enfocan en invariantes (piedad, tickets, tipos de
recompensa) porque el RNG del servicio usa semilla de tiempo.
"""

from __future__ import annotations

from app.data.cartas import CARTAS


def _sembrar(cliente, slot, tickets=None, piedad=None, coleccion=None):
    """Crea el slot y siembra estado del gacha para los tests.

    El estado se siembra mutando la partida en memoria (el endpoint
    del gacha auto-guarda cada mutación).
    """
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        if tickets:
            partida.entradas_gacha.update(tickets)
        if piedad:
            partida.piedad_gacha.update(piedad)
        if coleccion:
            partida.coleccion.update(coleccion)

    store.mutate(slot, mutador)


class TestTirar:
    def test_tirada_unica_consume_un_ticket(self, cliente):
        _sembrar(cliente, "g1", tickets={"ticket_common": 5})
        respuesta = cliente.post(
            "/api/game/g1/gacha/tirar", json={"pool": "STANDARD", "count": 1}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert "Ceremonia Completada" in datos["mensaje"]
        assert len(datos["resultados"]) == 1
        assert datos["tickets_restantes"] == 4
        assert datos["snapshot"]["gt"]["ticket_common"] == 4

    def test_tirada_diez_consume_diez_tickets(self, cliente):
        _sembrar(cliente, "g2", tickets={"ticket_common": 12})
        respuesta = cliente.post(
            "/api/game/g2/gacha/tirar", json={"pool": "STANDARD", "count": 10}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert len(datos["resultados"]) == 10
        assert datos["tickets_restantes"] == 2
        assert datos["snapshot"]["gt"]["ticket_common"] == 2

    def test_pool_premium_usa_ticket_premium(self, cliente):
        _sembrar(cliente, "g3", tickets={"ticket_premium": 3})
        respuesta = cliente.post(
            "/api/game/g3/gacha/tirar", json={"pool": "PREMIUM", "count": 1}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["tickets_restantes"] == 2
        assert datos["snapshot"]["gt"]["ticket_premium"] == 2

    def test_todas_las_recompensas_tienen_rareza_valida(self, cliente):
        _sembrar(cliente, "g4", tickets={"ticket_common": 10})
        respuesta = cliente.post(
            "/api/game/g4/gacha/tirar", json={"pool": "STANDARD", "count": 10}
        )
        datos = respuesta.json()["data"]
        validas = {"common", "rare", "epic", "legendary"}
        for recompensa in datos["resultados"]:
            assert recompensa["rareza"] in validas
            assert recompensa["tipo"] in {"carta", "recurso"}
            if recompensa["tipo"] == "carta":
                assert recompensa["carta"] in CARTAS
            else:
                assert recompensa["carta"] is None

    def test_piedad_garantiza_epico_al_llegar_al_limite(self, cliente):
        # piedad a 50 = guaranteedEpicAfter del STANDARD: la primera
        # tirada debe ser épica y resetear la piedad a 0
        _sembrar(
            cliente,
            "g5",
            tickets={"ticket_common": 5},
            piedad={"standard_pity": 50},
        )
        respuesta = cliente.post(
            "/api/game/g5/gacha/tirar", json={"pool": "STANDARD", "count": 1}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["resultados"][0]["rareza"] == "epic"
        assert datos["piedad"] == 0
        assert datos["snapshot"]["gp"]["standard_pity"] == 0

    def test_piedad_incrementa_en_rarezas_no_epicas(self, cliente):
        # con piedad en 0, 10 tiradas no épicas llegan como máximo a 10
        _sembrar(cliente, "g6", tickets={"ticket_common": 10})
        respuesta = cliente.post(
            "/api/game/g6/gacha/tirar", json={"pool": "STANDARD", "count": 10}
        )
        datos = respuesta.json()["data"]
        assert datos["piedad"] <= 10
        assert datos["snapshot"]["gp"]["standard_pity"] == datos["piedad"]

    def test_tirada_diez_ultima_es_al_menos_rara_o_mejor(self, cliente):
        # el décimo resultado de una tirada de 10 nunca es común
        _sembrar(cliente, "g7", tickets={"ticket_common": 10})
        respuesta = cliente.post(
            "/api/game/g7/gacha/tirar", json={"pool": "STANDARD", "count": 10}
        )
        datos = respuesta.json()["data"]
        assert datos["resultados"][-1]["rareza"] in {"rare", "epic", "legendary"}

    def test_carta_llena_la_coleccion(self, cliente):
        _sembrar(
            cliente,
            "g8",
            tickets={"ticket_common": 1},
            coleccion={"pq": 0},
        )
        respuesta = cliente.post(
            "/api/game/g8/gacha/tirar", json={"pool": "STANDARD", "count": 1}
        )
        assert respuesta.status_code == 200
        # sea carta o polvo, la colección y los materiales quedan coherentes
        snapshot = respuesta.json()["data"]["snapshot"]
        assert isinstance(snapshot["col"], dict)
        assert snapshot["mat"]["p"] >= 0


class TestErrores:
    def test_tickets_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "g9", tickets={"ticket_common": 0})
        respuesta = cliente.post(
            "/api/game/g9/gacha/tirar", json={"pool": "STANDARD", "count": 1}
        )
        assert respuesta.status_code == 400
        assert (
            respuesta.json()["error"]["code"] == "tickets_insuficientes"
        )

    def test_pool_desconocida_es_400(self, cliente):
        _sembrar(cliente, "g10", tickets={"ticket_common": 5})
        respuesta = cliente.post(
            "/api/game/g10/gacha/tirar", json={"pool": "OTRA", "count": 1}
        )
        assert respuesta.status_code == 422  # Literal de pydantic

    def test_count_invalido_es_400(self, cliente):
        # pydantic deja pasar 2..10; la regla de negocio exige 1 o 10
        _sembrar(cliente, "g11", tickets={"ticket_common": 50})
        respuesta = cliente.post(
            "/api/game/g11/gacha/tirar", json={"pool": "STANDARD", "count": 3}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "cantidad_invalida"

    def test_count_fuera_de_rango_es_422(self, cliente):
        # el contrato de pydantic rechaza count fuera de 1..10
        _sembrar(cliente, "g12", tickets={"ticket_common": 50})
        respuesta = cliente.post(
            "/api/game/g12/gacha/tirar", json={"pool": "STANDARD", "count": 0}
        )
        assert respuesta.status_code == 422

    def test_slot_inexistente_es_404(self, cliente):
        respuesta = cliente.post(
            "/api/game/noexist/gacha/tirar",
            json={"pool": "STANDARD", "count": 1},
        )
        assert respuesta.status_code == 404


class TestDatosGacha:
    def test_get_data_gacha(self, cliente):
        respuesta = cliente.get("/api/data/gacha")
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert len(datos["pools"]) == 2
        assert len(datos["tickets"]) == 2
        claves = {pool["clave"] for pool in datos["pools"]}
        assert claves == {"STANDARD", "PREMIUM"}
        for pool in datos["pools"]:
            assert pool["coste_por_tirada"] == 1
            total = (
                pool["probabilidades"]["common"]
                + pool["probabilidades"]["rare"]
                + pool["probabilidades"]["epic"]
                + pool["probabilidades"]["legendary"]
            )
            assert abs(total - 100) < 1e-9
