"""API de mazos — flujos completos contra la app de prueba."""

from __future__ import annotations

from app.data.sectas import SECTAS

SECTA = "esp"
BASE_ESP = SECTAS[SECTA].cartas_iniciales


def _sembrar(cliente, slot, coleccion=None, secta=None):
    """Crea el slot y siembra colección/secta para los tests."""
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        if coleccion:
            partida.coleccion.update(coleccion)
        if secta:
            partida.secta = secta

    store.mutate(slot, mutador)


class TestCrear:
    def test_crear_vacio(self, cliente):
        _sembrar(cliente, "m1")
        respuesta = cliente.post("/api/game/m1/mazos", json={})
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["dk"] == [{"n": "Mazo 1", "c": {}}]
        assert datos["snapshot"]["ad"] == -1

    def test_crear_desde_automatico_tiene_40(self, cliente):
        _sembrar(cliente, "m2", coleccion={"aa": 2})
        respuesta = cliente.post(
            "/api/game/m2/mazos", json={"desde_automatico": True}
        )
        assert respuesta.status_code == 200
        mazo = respuesta.json()["data"]["snapshot"]["dk"][0]
        assert sum(mazo["c"].values()) == 40
        assert all(mazo["c"].get(carta, 0) == 3 for carta in BASE_ESP)

    def test_slot_inexistente_es_404(self, cliente):
        respuesta = cliente.post("/api/game/nope/mazos", json={})
        assert respuesta.status_code == 404

    def test_maximo_mazos_es_400(self, cliente):
        _sembrar(cliente, "m3")
        for _ in range(8):
            cliente.post("/api/game/m3/mazos", json={})
        respuesta = cliente.post("/api/game/m3/mazos", json={})
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "maximo_mazos"


class TestEditar:
    def test_anadir_y_quitar_roundtrip(self, cliente):
        _sembrar(cliente, "m4")
        cliente.post("/api/game/m4/mazos", json={})
        respuesta = cliente.post(
            "/api/game/m4/mazos/0/anadir", json={"carta": "cf"}
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["data"]["snapshot"]["dk"][0]["c"] == {"cf": 1}
        respuesta = cliente.post(
            "/api/game/m4/mazos/0/quitar", json={"carta": "cf"}
        )
        assert respuesta.json()["data"]["snapshot"]["dk"][0]["c"] == {}

    def test_anadir_carta_desconocida_es_400(self, cliente):
        _sembrar(cliente, "m5")
        cliente.post("/api/game/m5/mazos", json={})
        respuesta = cliente.post(
            "/api/game/m5/mazos/0/anadir", json={"carta": "zzz"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "carta_desconocida"

    def test_anadir_indice_invalido_es_400(self, cliente):
        _sembrar(cliente, "m6")
        respuesta = cliente.post(
            "/api/game/m6/mazos/3/anadir", json={"carta": "cf"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "indice_invalido"

    def test_renombrar_recorta_a_22(self, cliente):
        _sembrar(cliente, "m7")
        cliente.post("/api/game/m7/mazos", json={})
        enviado = "  Mazo de fuego x" * 3
        respuesta = cliente.post(
            "/api/game/m7/mazos/0/renombrar",
            json={"nombre": enviado},
        )
        assert respuesta.status_code == 200
        nombre = respuesta.json()["data"]["snapshot"]["dk"][0]["n"]
        assert nombre == enviado.strip()[:22]

    def test_renombrar_vacio_es_400(self, cliente):
        _sembrar(cliente, "m8")
        cliente.post("/api/game/m8/mazos", json={})
        respuesta = cliente.post(
            "/api/game/m8/mazos/0/renombrar", json={"nombre": "   "}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "nombre_vacio"

    def test_vaciar(self, cliente):
        _sembrar(cliente, "m9")
        cliente.post("/api/game/m9/mazos", json={})
        cliente.post("/api/game/m9/mazos/0/anadir", json={"carta": "cf"})
        respuesta = cliente.post("/api/game/m9/mazos/0/vaciar")
        assert respuesta.status_code == 200
        assert respuesta.json()["data"]["snapshot"]["dk"][0]["c"] == {}

    def test_autocompletar_llena_a_40(self, cliente):
        _sembrar(cliente, "m10")
        cliente.post("/api/game/m10/mazos", json={})
        respuesta = cliente.post("/api/game/m10/mazos/0/autocompletar")
        assert respuesta.status_code == 200
        mazo = respuesta.json()["data"]["snapshot"]["dk"][0]
        assert sum(mazo["c"].values()) == 40


class TestUsar:
    def test_usar_automatico(self, cliente):
        _sembrar(cliente, "m11")
        respuesta = cliente.post(
            "/api/game/m11/mazos/usar", json={"indice": -1}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["ad"] == -1
        assert datos["mensaje"] == "Usarás el mazo automático."

    def test_usar_mazo_valido(self, cliente):
        _sembrar(cliente, "m12")
        cliente.post("/api/game/m12/mazos", json={})
        cliente.post("/api/game/m12/mazos/0/autocompletar")
        respuesta = cliente.post(
            "/api/game/m12/mazos/usar", json={"indice": 0}
        )
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["ad"] == 0
        assert datos["mensaje"] == "Mazo en uso: Mazo 1."

    def test_usar_mazo_incompleto_lo_activa_y_avisa(self, cliente):
        _sembrar(cliente, "m13")
        cliente.post("/api/game/m13/mazos", json={})
        respuesta = cliente.post(
            "/api/game/m13/mazos/usar", json={"indice": 0}
        )
        datos = respuesta.json()["data"]
        # paridad con dUse: el mazo se activa aunque aún no sea válido
        assert datos["snapshot"]["ad"] == 0
        assert "aún no tiene 40 cartas" in datos["mensaje"]

    def test_usar_indice_invalido_es_400(self, cliente):
        _sembrar(cliente, "m14")
        respuesta = cliente.post(
            "/api/game/m14/mazos/usar", json={"indice": 5}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "indice_invalido"


class TestDuplicarYEliminar:
    def test_duplicar(self, cliente):
        _sembrar(cliente, "m15")
        cliente.post("/api/game/m15/mazos", json={})
        cliente.post("/api/game/m15/mazos/0/anadir", json={"carta": "cf"})
        respuesta = cliente.post(
            "/api/game/m15/mazos/duplicar", json={"indice": 0}
        )
        assert respuesta.status_code == 200
        dk = respuesta.json()["data"]["snapshot"]["dk"]
        assert len(dk) == 2
        assert dk[1]["n"] == "Mazo 1 (copia)"
        assert dk[1]["c"] == {"cf": 1}

    def test_eliminar_ajusta_el_activo(self, cliente):
        _sembrar(cliente, "m16")
        cliente.post("/api/game/m16/mazos", json={})
        cliente.post("/api/game/m16/mazos", json={})
        cliente.post("/api/game/m16/mazos/usar", json={"indice": 1})
        respuesta = cliente.post(
            "/api/game/m16/mazos/eliminar", json={"indice": 0}
        )
        datos = respuesta.json()["data"]
        assert len(datos["snapshot"]["dk"]) == 1
        assert datos["snapshot"]["ad"] == 0  # 1 → 0 tras borrar el 0

    def test_eliminar_el_activo_pasa_a_automatico(self, cliente):
        _sembrar(cliente, "m17")
        cliente.post("/api/game/m17/mazos", json={})
        cliente.post("/api/game/m17/mazos/usar", json={"indice": 0})
        respuesta = cliente.post(
            "/api/game/m17/mazos/eliminar", json={"indice": 0}
        )
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["dk"] == []
        assert datos["snapshot"]["ad"] == -1


class TestDesequipar:
    def test_desequpa_del_activo(self, cliente):
        _sembrar(cliente, "m18")
        cliente.post("/api/game/m18/mazos", json={})
        cliente.post("/api/game/m18/mazos/0/anadir", json={"carta": "cf"})
        cliente.post("/api/game/m18/mazos/0/anadir", json={"carta": "cf"})
        cliente.post("/api/game/m18/mazos/usar", json={"indice": 0})
        respuesta = cliente.post(
            "/api/game/m18/mazos/desequipar", json={"carta": "cf"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["dk"][0]["c"] == {"cf": 1}
        assert "incompleto" in datos["mensaje"]

    def test_sin_mazo_activo_es_400(self, cliente):
        _sembrar(cliente, "m19")
        respuesta = cliente.post(
            "/api/game/m19/mazos/desequipar", json={"carta": "cf"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "carta_no_en_mazo"
