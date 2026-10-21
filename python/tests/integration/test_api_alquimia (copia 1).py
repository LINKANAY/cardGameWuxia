"""API de alquimia — flujos completos contra la app de prueba."""

from __future__ import annotations

from app.data.cartas import CARTAS, cartas_de_rareza, rareza_de


def _sembrar(cliente, slot, materiales=None, coleccion=None, recetas=None):
    """Crea el slot y siembra materiales/coleccion/recetas para los tests.

    El estado se siembra mutando la partida en memoria (el endpoint de
    alquimia auto-guarda cada mutación).
    """
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        if materiales:
            partida.materiales.update(materiales)
        if coleccion:
            partida.coleccion.update(coleccion)
        if recetas:
            partida.recetas.update(recetas)

    store.mutate(slot, mutador)


class TestElaborar:
    def test_elabora_vit_y_paga_materiales(self, cliente):
        _sembrar(cliente, "a1", materiales={"h": 5})
        respuesta = cliente.post(
            "/api/game/a1/alquimia/elaborar", json={"pildora": "vit"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["mensaje"] == "Elaboraste: Elixir de Vitalidad"
        assert datos["snapshot"]["pil"] == {"vit": 1}
        assert datos["snapshot"]["mat"]["h"] == 2
        # brew incrementa el contador de misiones qs.br
        assert datos["snapshot"]["qs"]["br"] == 1

    def test_receta_no_aprendida_es_400(self, cliente):
        _sembrar(cliente, "a2", materiales={"h": 50})
        respuesta = cliente.post(
            "/api/game/a2/alquimia/elaborar", json={"pildora": "cur"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "receta_no_aprendida"

    def test_materiales_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "a3", materiales={"h": 2})
        respuesta = cliente.post(
            "/api/game/a3/alquimia/elaborar", json={"pildora": "vit"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "materiales_insuficientes"

    def test_pildora_desconocida_es_400(self, cliente):
        _sembrar(cliente, "a4")
        respuesta = cliente.post(
            "/api/game/a4/alquimia/elaborar", json={"pildora": "zzz"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "pildora_desconocida"

    def test_slot_inexistente_es_404(self, cliente):
        respuesta = cliente.post(
            "/api/game/nope/alquimia/elaborar", json={"pildora": "vit"}
        )
        assert respuesta.status_code == 404
        assert respuesta.json()["error"]["code"] == "not_found"


class TestForjar:
    def test_forja_comun(self, cliente):
        _sembrar(cliente, "f1", materiales={"p": 2})
        respuesta = cliente.post(
            "/api/game/f1/alquimia/forjar", json={"rareza": 0}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        carta = datos["carta"]
        assert carta in cartas_de_rareza(0)
        assert rareza_de(CARTAS[carta]) == 0
        assert datos["snapshot"]["mat"]["p"] == 0
        assert datos["snapshot"]["col"][carta] == 1
        assert datos["mensaje"].startswith("Forjaste: ")
        assert "(Común)" in datos["mensaje"]

    def test_materiales_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "f2", materiales={"p": 1})
        respuesta = cliente.post(
            "/api/game/f2/alquimia/forjar", json={"rareza": 0}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "materiales_insuficientes"

    def test_rareza_invalida_es_422(self, cliente):
        _sembrar(cliente, "f3", materiales={"p": 99})
        respuesta = cliente.post(
            "/api/game/f3/alquimia/forjar", json={"rareza": 9}
        )
        assert respuesta.status_code == 422


class TestFusionar:
    def test_fusiona_tres_copias_comunes(self, cliente):
        _sembrar(cliente, "u1", coleccion={"cf": 3})
        respuesta = cliente.post(
            "/api/game/u1/alquimia/fusionar", json={"carta": "cf"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        coleccion = datos["snapshot"]["col"]
        assert coleccion.get("cf", 0) == 0  # 3 copias consumidas
        obtenida = datos["carta"]
        assert rareza_de(CARTAS[obtenida]) == 1
        assert coleccion[obtenida] == 1
        assert "(Poco común)" in datos["mensaje"]

    def test_sin_tres_copias_es_400(self, cliente):
        _sembrar(cliente, "u2", coleccion={"cf": 2})
        respuesta = cliente.post(
            "/api/game/u2/alquimia/fusionar", json={"carta": "cf"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "coleccion_insuficiente"

    def test_carta_desconocida_es_400(self, cliente):
        _sembrar(cliente, "u3")
        respuesta = cliente.post(
            "/api/game/u3/alquimia/fusionar", json={"carta": "zzz"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "carta_desconocida"


class TestDesmantelar:
    def test_desmantela_y_gana_polvo(self, cliente):
        _sembrar(cliente, "d1", coleccion={"cf": 2})
        respuesta = cliente.post(
            "/api/game/d1/alquimia/desmantelar", json={"carta": "cf"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["polvo"] == 1  # cf es Común: 1 + 0
        assert datos["snapshot"]["col"] == {"cf": 1}
        assert datos["snapshot"]["mat"]["p"] == 1
        assert datos["mensaje"] == (
            f"Desmantelaste {CARTAS['cf'].nombre}: +1 polvo de jade"
        )

    def test_sin_copias_es_400(self, cliente):
        _sembrar(cliente, "d2")
        respuesta = cliente.post(
            "/api/game/d2/alquimia/desmantelar", json={"carta": "cf"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "coleccion_insuficiente"

    def test_persiste_tras_recarga(self, cliente):
        _sembrar(cliente, "d3", materiales={"h": 5})
        cliente.post("/api/game/d3/alquimia/elaborar", json={"pildora": "vit"})
        # releer desde disco (simula otro proceso)
        respuesta = cliente.get("/api/game/d3")
        assert respuesta.json()["data"]["snapshot"]["pil"] == {"vit": 1}


class TestDataAlquimia:
    def test_catalogo_completo(self, cliente):
        respuesta = cliente.get("/api/data/alquimia")
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert len(datos["pildoras"]) == 27
        assert len(datos["forja"]) == 6

    def test_pildoras_clave(self, cliente):
        datos = cliente.get("/api/data/alquimia").json()["data"]
        por_id = {p["identificador"]: p for p in datos["pildoras"]}
        # vit: receta inicial, coste 3h, icono heal, no es de combate
        assert por_id["vit"]["coste"] == {"h": 3}
        assert por_id["vit"]["icono"] == "heal"
        assert por_id["vit"]["es_combate"] is False
        # cur: píldora de combate (flag b), icono heal
        assert por_id["cur"]["es_combate"] is True
        # tes: talismán con glifo 符
        assert por_id["tes"]["icono"] == "tal"

    def test_forja_parity_fc(self, cliente):
        datos = cliente.get("/api/data/alquimia").json()["data"]
        # FC del JS: [{p:2},{p:4},{p:7},{p:10,n:2},{p:16,n:4},{p:24,n:8}]
        assert datos["forja"][0]["coste"] == {"p": 2}
        assert datos["forja"][5]["coste"] == {"p": 24, "n": 8}
        assert datos["forja"][0]["nombre"] == "Común"
        assert datos["forja"][5]["nombre"] == "Celestial"
