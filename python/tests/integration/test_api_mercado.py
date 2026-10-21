"""API del mercado — flujos completos contra la app de prueba."""

from __future__ import annotations


def _sembrar(
    cliente,
    slot,
    piedras=None,
    materiales=None,
    coleccion=None,
    secta=None,
):
    """Crea el slot y siembra estado para los tests.

    El estado se siembra mutando la partida en memoria (el endpoint
    del mercado auto-guarda cada mutación).
    """
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        if piedras is not None:
            partida.piedras_espirituales = piedras
        if materiales:
            partida.materiales.update(materiales)
        if coleccion:
            partida.coleccion.update(coleccion)
        if secta is not None:
            partida.secta_elegida_confirmada = secta

    store.mutate(slot, mutador)


class TestComprarCarta:
    def test_compra_carta_neutral(self, cliente):
        _sembrar(cliente, "m1", piedras=50, secta="esp")
        respuesta = cliente.post(
            "/api/game/m1/mercado/comprar", json={"carta": "pq"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert "Compraste" in datos["mensaje"]
        assert datos["snapshot"]["col"]["pq"] == 1
        # pq es neutral: 6 piedras (rareza 0)
        assert datos["snapshot"]["stn"] == 44
        assert datos["snapshot"]["qs"]["bu"] == 1
        assert datos["snapshot"]["qs"]["ss"] == 6

    def test_compra_carta_de_mi_secta_cuenta_bsc(self, cliente):
        _sembrar(cliente, "m2", piedras=50, secta="esp")
        # 'ex' es de esp y no inicial
        respuesta = cliente.post(
            "/api/game/m2/mercado/comprar", json={"carta": "ex"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["col"]["ex"] == 1
        assert datos["snapshot"]["qs"]["bsc"] == 1

    def test_carta_de_otra_secta_es_400(self, cliente):
        _sembrar(cliente, "m3", piedras=50, secta="esp")
        respuesta = cliente.post(
            "/api/game/m3/mercado/comprar", json={"carta": "bl"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "no_disponible"

    def test_tres_copias_es_400(self, cliente):
        _sembrar(
            cliente, "m4", piedras=50, coleccion={"pq": 3}, secta="esp"
        )
        respuesta = cliente.post(
            "/api/game/m4/mercado/comprar", json={"carta": "pq"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "coleccion_llena"

    def test_piedras_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "m5", piedras=1, secta="esp")
        respuesta = cliente.post(
            "/api/game/m5/mercado/comprar", json={"carta": "pq"}
        )
        assert respuesta.status_code == 400
        assert (
            respuesta.json()["error"]["code"] == "piedras_insuficientes"
        )

    def test_carta_desconocida_es_400(self, cliente):
        _sembrar(cliente, "m6", piedras=50, secta="esp")
        respuesta = cliente.post(
            "/api/game/m6/mercado/comprar", json={"carta": "nope"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "carta_desconocida"

    def test_slot_inexistente_es_404(self, cliente):
        respuesta = cliente.post(
            "/api/game/noexist/mercado/comprar", json={"carta": "pq"}
        )
        assert respuesta.status_code == 404


class TestComprarMaterial:
    def test_confirmacion_previa_devuelve_lote(self, cliente):
        _sembrar(cliente, "m7", piedras=100, secta="esp")
        respuesta = cliente.post(
            "/api/game/m7/mercado/comprar-material",
            json={"puesto": "esp", "confirmado": False},
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["confirmar"] is True
        assert datos["lote"]["cantidad"] == 3
        assert datos["lote"]["costo"] == 14
        # sin confirmar no se muta nada
        assert datos["snapshot"]["stn"] == 100
        assert datos["snapshot"]["mat"]["p"] == 0

    def test_confirmado_compra_lote(self, cliente):
        _sembrar(cliente, "m8", piedras=100, secta="esp")
        respuesta = cliente.post(
            "/api/game/m8/mercado/comprar-material",
            json={"puesto": "esp", "confirmado": True},
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert "Compraste" in datos["mensaje"]
        assert datos["snapshot"]["stn"] == 86
        assert datos["snapshot"]["mat"]["p"] == 3
        assert datos["snapshot"]["qs"]["bm"] == 1
        assert datos["snapshot"]["qs"]["ss"] == 14

    def test_puesto_general_sin_lote_es_400(self, cliente):
        _sembrar(cliente, "m9", piedras=100, secta="esp")
        respuesta = cliente.post(
            "/api/game/m9/mercado/comprar-material",
            json={"puesto": "neu", "confirmado": True},
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "puesto_invalido"

    def test_piedras_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "m10", piedras=1, secta="esp")
        respuesta = cliente.post(
            "/api/game/m10/mercado/comprar-material",
            json={"puesto": "esp", "confirmado": True},
        )
        assert respuesta.status_code == 400
        assert (
            respuesta.json()["error"]["code"] == "piedras_insuficientes"
        )


class TestVenderMaterial:
    def test_vende_unidad(self, cliente):
        _sembrar(
            cliente,
            "m11",
            piedras=0,
            materiales={"h": 2, "n": 0, "p": 0},
        )
        respuesta = cliente.post(
            "/api/game/m11/mercado/vender", json={"material": "h"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["piedras"] == 1  # SELL.h
        assert datos["snapshot"]["mat"]["h"] == 1
        assert datos["snapshot"]["stn"] == 1
        assert datos["snapshot"]["qs"]["sv"] == 1

    def test_sin_material_es_400(self, cliente):
        _sembrar(cliente, "m12", piedras=0)
        respuesta = cliente.post(
            "/api/game/m12/mercado/vender", json={"material": "n"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "material_insuficiente"

    def test_material_desconocido_es_400(self, cliente):
        _sembrar(cliente, "m13", materiales={"h": 5})
        respuesta = cliente.post(
            "/api/game/m13/mercado/vender", json={"material": "x"}
        )
        assert respuesta.status_code == 400
        assert (
            respuesta.json()["error"]["code"] == "material_desconocido"
        )


class TestComprarPildora:
    def test_compra_vit_basica(self, cliente):
        _sembrar(cliente, "m14", piedras=100, secta="esp")
        respuesta = cliente.post(
            "/api/game/m14/mercado/comprar-pildora",
            json={"pildora": "vit"},
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert "Compraste" in datos["mensaje"]
        assert datos["snapshot"]["pil"]["vit"] == 1
        assert datos["snapshot"]["stn"] == 100 - 31  # mkcPrice vit
        assert datos["snapshot"]["qs"]["ss"] == 31

    def test_receta_no_aprendida_no_en_venta(self, cliente):
        _sembrar(cliente, "m15", piedras=500, secta="esp")
        # 'rob' no es básica ni está aprendida
        respuesta = cliente.post(
            "/api/game/m15/mercado/comprar-pildora",
            json={"pildora": "rob"},
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "no_en_venta"

    def test_pildora_desconocida_es_400(self, cliente):
        _sembrar(cliente, "m16", piedras=500)
        respuesta = cliente.post(
            "/api/game/m16/mercado/comprar-pildora",
            json={"pildora": "nope"},
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "pildora_desconocida"

    def test_piedras_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "m17", piedras=1)
        respuesta = cliente.post(
            "/api/game/m17/mercado/comprar-pildora",
            json={"pildora": "vit"},
        )
        assert respuesta.status_code == 400
        assert (
            respuesta.json()["error"]["code"] == "piedras_insuficientes"
        )


class TestDatosMercado:
    def test_get_data_mercado(self, cliente):
        respuesta = cliente.get("/api/data/mercado")
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert len(datos["puestos"]) == 11
        assert datos["precios_venta"] == {"h": 1, "n": 8, "p": 2}
        identificadores = [p["identificador"] for p in datos["puestos"]]
        assert "esp" in identificadores
        assert "neu" in identificadores
        # el General no tiene lote
        general = next(p for p in datos["puestos"] if p["identificador"] == "neu")
        assert general["lote"] is None

    def test_get_detalle_carta(self, cliente):
        respuesta = cliente.get(
            "/api/data/cartas/ex/detalle", params={"secta": "esp"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]["carta"]
        assert datos["identificador"] == "ex"
        assert datos["precio"] == 45  # rareza 3
        assert isinstance(datos["descripcion"], list)
        assert isinstance(datos["obtencion"], list)

    def test_get_detalle_carta_neutral(self, cliente):
        respuesta = cliente.get("/api/data/cartas/pq/detalle")
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]["carta"]
        assert datos["precio"] == 6  # rareza 0
        assert datos["secta_visible"] == "Neutral"
