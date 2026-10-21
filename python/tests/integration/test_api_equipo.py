"""API de equipo y trajes — flujos completos contra la app de prueba."""

from __future__ import annotations


def _sembrar(cliente, slot, materiales=None, victorias=None):
    """Crea el slot y siembra materiales/victorias para los tests.

    El estado se siembra mutando la partida en memoria (el endpoint de
    equipo auto-guarda cada mutación).
    """
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        if materiales:
            partida.materiales.update(materiales)
        if victorias is not None:
            partida.victorias.extend(victorias)

    store.mutate(slot, mutador)


class TestCatalogos:
    def test_catalogo_de_equipo(self, cliente):
        respuesta = cliente.get("/api/data/equipo")
        assert respuesta.status_code == 200
        equipo = respuesta.json()["data"]["equipo"]
        assert len(equipo["piezas"]) == 17
        assert [hueco["clave"] for hueco in equipo["huecos"]] == [
            "cabeza",
            "cuerpo",
            "guantes",
            "botas",
            "reliquia",
            "artefacto",
        ]
        g1 = next(
            p for p in equipo["piezas"] if p["identificador"] == "G1"
        )
        assert g1["nombre"] == "Diadema de Jade"
        assert g1["coste"] == {"p": 3, "h": 2}
        assert g1["desbloqueo"] is None

    def test_catalogo_de_trajes(self, cliente):
        respuesta = cliente.get("/api/data/trajes")
        assert respuesta.status_code == 200
        trajes = respuesta.json()["data"]["trajes"]
        assert len(trajes) == 10 * 6
        esp = [t for t in trajes if t["secta"] == "esp"]
        assert esp[0]["umbral"] == 0 and esp[1]["umbral"] == 3
        assert esp[0]["nombre"] == "Túnica del Discípulo"
        assert esp[0]["descripcion"] == "+2 vida máxima"


class TestForjar:
    def test_forjar_g1_paga_y_auto_equipa(self, cliente):
        _sembrar(cliente, "eq1", materiales={"p": 3, "h": 2})
        respuesta = cliente.post(
            "/api/game/eq1/equipo/forjar", json={"pieza": "G1"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["mensaje"] == "Forjaste: Diadema de Jade"
        assert datos["snapshot"]["gr"] == {"G1": 1}
        assert datos["snapshot"]["eq"]["cabeza"] == "G1"
        assert datos["snapshot"]["mat"] == {"h": 0, "n": 0, "p": 0}

    def test_artefacto_inicia_usos(self, cliente):
        _sembrar(cliente, "eq2", materiales={"p": 14, "n": 6},
                 victorias=[23])
        respuesta = cliente.post(
            "/api/game/eq2/equipo/forjar", json={"pieza": "G10"}
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["data"]["snapshot"]["du"] == {"G10": 3}

    def test_ya_poseida_es_400(self, cliente):
        _sembrar(cliente, "eq3", materiales={"p": 6, "h": 4})
        cliente.post("/api/game/eq3/equipo/forjar", json={"pieza": "G1"})
        respuesta = cliente.post(
            "/api/game/eq3/equipo/forjar", json={"pieza": "G1"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "pieza_ya_poseida"

    def test_plano_bloqueado_es_400_y_se_abre_con_la_victoria(
        self, cliente
    ):
        _sembrar(cliente, "eq4", materiales={"p": 6, "n": 2})
        respuesta = cliente.post(
            "/api/game/eq4/equipo/forjar", json={"pieza": "G2"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "pieza_bloqueada"
        assert "Nivel 3" in respuesta.json()["error"]["message"]

        store = cliente.app.state.store
        store.mutate("eq4", lambda partida: partida.victorias.append(17))
        respuesta = cliente.post(
            "/api/game/eq4/equipo/forjar", json={"pieza": "G2"}
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["data"]["snapshot"]["gr"] == {"G2": 1}

    def test_materiales_insuficientes_es_400(self, cliente):
        _sembrar(cliente, "eq5", materiales={"p": 1})
        respuesta = cliente.post(
            "/api/game/eq5/equipo/forjar", json={"pieza": "G1"}
        )
        assert respuesta.status_code == 400
        assert (
            respuesta.json()["error"]["code"] == "materiales_insuficientes"
        )

    def test_pieza_desconocida_es_400(self, cliente):
        _sembrar(cliente, "eq6")
        respuesta = cliente.post(
            "/api/game/eq6/equipo/forjar", json={"pieza": "G99"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "pieza_desconocida"

    def test_slot_inexistente_es_404(self, cliente):
        respuesta = cliente.post(
            "/api/game/nope/equipo/forjar", json={"pieza": "G1"}
        )
        assert respuesta.status_code == 404


class TestEquipar:
    def test_alterna_equipar_y_retirar(self, cliente):
        _sembrar(cliente, "eq7", materiales={"p": 3, "h": 2})
        cliente.post("/api/game/eq7/equipo/forjar", json={"pieza": "G1"})

        respuesta = cliente.post(
            "/api/game/eq7/equipo/equipar", json={"pieza": "G1"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["mensaje"] == "Retiraste: Diadema de Jade"
        assert datos["snapshot"]["eq"]["cabeza"] is None

        respuesta = cliente.post(
            "/api/game/eq7/equipo/equipar", json={"pieza": "G1"}
        )
        assert respuesta.json()["data"]["snapshot"]["eq"]["cabeza"] == "G1"

    def test_pieza_no_poseida_es_400(self, cliente):
        _sembrar(cliente, "eq8")
        respuesta = cliente.post(
            "/api/game/eq8/equipo/equipar", json={"pieza": "G1"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "pieza_no_poseida"


class TestBestia:
    def test_bloqueada_hasta_vencer_al_jefe(self, cliente):
        _sembrar(cliente, "eq9")
        respuesta = cliente.post(
            "/api/game/eq9/equipo/bestia", json={"bestia": "BS1"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "bestia_bloqueada"

        store = cliente.app.state.store
        store.mutate("eq9", lambda partida: partida.victorias.append(5))
        respuesta = cliente.post(
            "/api/game/eq9/equipo/bestia", json={"bestia": "BS1"}
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["snapshot"]["be"] == "BS1"

        # segunda pulsación: se retira (toggle)
        respuesta = cliente.post(
            "/api/game/eq9/equipo/bestia", json={"bestia": "BS1"}
        )
        assert respuesta.json()["data"]["snapshot"]["be"] is None

    def test_bestia_desconocida_es_400(self, cliente):
        _sembrar(cliente, "eq10", victorias=[5])
        respuesta = cliente.post(
            "/api/game/eq10/equipo/bestia", json={"bestia": "BS9"}
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "bestia_desconocida"


class TestTrajes:
    def test_vestir_traje_de_la_secta(self, cliente):
        _sembrar(cliente, "eq11", victorias=[0, 1, 2])
        respuesta = cliente.post(
            "/api/game/eq11/traje/vestir",
            json={"secta": "esp", "indice": 1},
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()["data"]
        assert datos["mensaje"] == "Vestiste: Armadura de Plata"
        assert datos["snapshot"]["of"] == {"esp": 1}

    def test_traje_bloqueado_es_400(self, cliente):
        _sembrar(cliente, "eq12")
        respuesta = cliente.post(
            "/api/game/eq12/traje/vestir",
            json={"secta": "esp", "indice": 1},
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "traje_bloqueado"

    def test_secta_distinta_es_400(self, cliente):
        _sembrar(cliente, "eq13", victorias=list(range(60)))
        respuesta = cliente.post(
            "/api/game/eq13/traje/vestir",
            json={"secta": "lot", "indice": 0},
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "secta_invalida"

    def test_traje_desconocido_es_400(self, cliente):
        _sembrar(cliente, "eq14", victorias=list(range(60)))
        respuesta = cliente.post(
            "/api/game/eq14/traje/vestir",
            json={"secta": "esp", "indice": 9},
        )
        assert respuesta.status_code == 400
        assert respuesta.json()["error"]["code"] == "traje_desconocido"

    def test_el_estado_conserva_las_claves_del_guardado(self, cliente):
        _sembrar(cliente, "eq15", materiales={"p": 3, "h": 2},
                 victorias=[0, 1, 2])
        cliente.post("/api/game/eq15/equipo/forjar", json={"pieza": "G1"})
        cliente.post(
            "/api/game/eq15/traje/vestir",
            json={"secta": "esp", "indice": 1},
        )
        datos = cliente.get("/api/game/eq15").json()["data"]
        snapshot = datos["snapshot"]
        for clave in ("gr", "eq", "du", "of", "be", "mat", "wins"):
            assert clave in snapshot
        assert snapshot["gr"] == {"G1": 1}
        assert snapshot["eq"] == {"cabeza": "G1"}
        assert snapshot["of"] == {"esp": 1}
