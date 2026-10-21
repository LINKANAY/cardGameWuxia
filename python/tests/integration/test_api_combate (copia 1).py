"""API del combate — flujos completos contra la app de prueba."""

from __future__ import annotations

from app.engine.state import crear_carta_juego


def _sembrar(cliente, slot, *, vida=None, reino=0, victorias=None, pildoras=None):
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        partida.nivel_reino = reino
        if vida is not None:
            partida.vida_hroe = vida
        if victorias is not None:
            partida.victorias = list(victorias)
        if pildoras is not None:
            partida.pildoras = dict(pildoras)

    store.mutate(slot, mutador)


class TestIniciarCombate:
    def test_inicia_combate_contra_enemigo_0(self, cliente):
        _sembrar(cliente, "c1")
        r = cliente.post(
            "/api/game/c1/combate/iniciar", json={"enemigo": 0}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        combate = data["combate"]
        assert combate["activo"] is True
        assert combate["fin"] == ""
        assert combate["enemigo"]["hp"] > 0
        assert len(combate["jugador"]["mano"]) >= 1

    def test_enemigo_invalido_devuelve_400(self, cliente):
        _sembrar(cliente, "c2")
        r = cliente.post(
            "/api/game/c2/combate/iniciar", json={"enemigo": 9999}
        )
        assert r.status_code == 400
        body = r.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "enemigo_invalido"

    def test_sin_partida_devuelve_404(self, cliente):
        r = cliente.post(
            "/api/game/nope/combate/iniciar", json={"enemigo": 0}
        )
        assert r.status_code == 404

    def test_pildora_desconocida_rechazada(self, cliente):
        _sembrar(cliente, "c3")
        r = cliente.post(
            "/api/game/c3/combate/iniciar",
            json={"enemigo": 0, "pildoras": ["xyz"]},
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "pildora_desconocida"


class TestFlujoCombate:
    def test_estado_sin_combate(self, cliente):
        _sembrar(cliente, "c10")
        r = cliente.get("/api/game/c10/combate")
        assert r.status_code == 200
        assert r.json()["data"]["combate"]["activo"] is False

    def test_fin_turno_sin_combate_rechazado(self, cliente):
        _sembrar(cliente, "c11")
        r = cliente.post(
            "/api/game/c11/combate/fin-turno", json={}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "sin_combate"

    def test_abandonar_libera_combate(self, cliente):
        _sembrar(cliente, "c12")
        cliente.post("/api/game/c12/combate/iniciar", json={"enemigo": 0})
        r = cliente.post("/api/game/c12/combate/abandonar")
        assert r.status_code == 200
        assert r.json()["data"]["fin"] == "f"
        r2 = cliente.get("/api/game/c12/combate")
        assert r2.json()["data"]["combate"]["activo"] is False

    def test_jugar_carta_invalida_rechazada(self, cliente):
        _sembrar(cliente, "c13")
        cliente.post("/api/game/c13/combate/iniciar", json={"enemigo": 0})
        r = cliente.post(
            "/api/game/c13/combate/jugar", json={"indice": 99}
        )
        assert r.status_code == 400


class TestVictoriaCampaña:
    def test_victoria_aplica_recompensas(self, cliente):
        _sembrar(cliente, "c20")
        store = cliente.app.state.store
        cliente.post("/api/game/c20/combate/iniciar", json={"enemigo": 0})
        # Matar al enemigo directamente en el estado en memoria
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c20")
        estado.E.hp = 0
        from app.engine.combat import comprobar_fin

        comprobar_fin(estado)
        campaña = servicio._consumir_eventos("c20", estado)
        assert any(e["tipo"] == "victoria" for e in campaña)
        snap = store.snapshot("c20")
        assert 0 in snap["wins"]
        assert snap["stn"] > 30
        assert snap["qs"]["w"] == 1

    def test_muerte_resetea_partida(self, cliente):
        _sembrar(cliente, "c21", reino=2, victorias=[0, 1])
        store = cliente.app.state.store
        cliente.post("/api/game/c21/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c21")
        estado.P.hp = 0
        from app.engine.combat import comprobar_fin

        comprobar_fin(estado)
        campaña = servicio._consumir_eventos("c21", estado)
        assert any(e["tipo"] == "muerte" for e in campaña)
        snap = store.snapshot("c21")
        assert snap["realm"] == 0
        assert snap["wins"] == []
        assert snap["dt"] == 1


class TestBolsaYPildoras:
    def test_iniciar_con_bolsa_no_consume_inventario(self, cliente):
        _sembrar(cliente, "c30", pildoras={"cur": 2, "fue": 1})
        r = cliente.post(
            "/api/game/c30/combate/iniciar",
            json={"enemigo": 0, "bolsa": ["cur", "fue"]},
        )
        assert r.status_code == 200
        combate = r.json()["data"]["combate"]
        assert combate["jugador"]["pouch"] == ["cur", "fue"]
        assert combate["jugador"]["usos"] == 0
        assert combate["pildoras_stock"] == {"cur": 2, "fue": 1}
        snap = cliente.app.state.store.snapshot("c30")
        assert snap["pil"] == {"cur": 2, "fue": 1}

    def test_iniciar_con_bolsa_pildora_desconocida(self, cliente):
        _sembrar(cliente, "c31")
        r = cliente.post(
            "/api/game/c31/combate/iniciar",
            json={"enemigo": 0, "bolsa": ["xyz"]},
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "pildora_desconocida"

    def test_usar_pildora_de_bolsa(self, cliente):
        _sembrar(cliente, "c32", vida=10, pildoras={"cur": 2})
        cliente.post(
            "/api/game/c32/combate/iniciar",
            json={"enemigo": 0, "bolsa": ["cur"]},
        )
        r = cliente.post(
            "/api/game/c32/combate/usar-pildora",
            json={"pildora": "cur"},
        )
        assert r.status_code == 200
        combate = r.json()["data"]["combate"]
        assert combate["jugador"]["usos"] == 1
        # 10 de vida + 10 de la píldora + 2 del traje base (applyOutfit)
        assert combate["jugador"]["hp"] == 22
        assert combate["pildoras_stock"] == {"cur": 1}
        assert any("Usas" in linea for linea in combate["logs"])

    def test_usar_pildora_sin_stock_rechazada(self, cliente):
        _sembrar(cliente, "c33", pildoras={"cur": 1})
        cliente.post(
            "/api/game/c33/combate/iniciar",
            json={"enemigo": 0, "bolsa": ["cur"]},
        )
        store = cliente.app.state.store
        store.mutate("c33", lambda p: p.pildoras.pop("cur", None))
        r = cliente.post(
            "/api/game/c33/combate/usar-pildora",
            json={"pildora": "cur"},
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "pildoras_insuficientes"

    def test_usar_pildora_fuera_de_bolsa_rechazada(self, cliente):
        _sembrar(cliente, "c34", pildoras={"cur": 1})
        cliente.post(
            "/api/game/c34/combate/iniciar",
            json={"enemigo": 0},
        )
        r = cliente.post(
            "/api/game/c34/combate/usar-pildora",
            json={"pildora": "cur"},
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "pildora_invalida"

    def test_tope_de_dos_usos_por_combate(self, cliente):
        _sembrar(cliente, "c35", pildoras={"cur": 5})
        cliente.post(
            "/api/game/c35/combate/iniciar",
            json={"enemigo": 0, "bolsa": ["cur"]},
        )
        for _ in range(2):
            r = cliente.post(
                "/api/game/c35/combate/usar-pildora",
                json={"pildora": "cur"},
            )
            assert r.status_code == 200
        r = cliente.post(
            "/api/game/c35/combate/usar-pildora",
            json={"pildora": "cur"},
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "pildora_invalida"


class TestEventoMapa:
    def test_resolver_evento_desbloquea(self, cliente):
        _sembrar(cliente, "c40")
        cliente.post("/api/game/c40/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c40")
        from app.engine.combat import EVENTOS_MAPA

        estado.ev = EVENTOS_MAPA[0]
        estado.lock = True
        r = cliente.post(
            "/api/game/c40/combate/evento", json={"opcion": 1}
        )
        assert r.status_code == 200
        combate = r.json()["data"]["combate"]
        assert combate["ev"] is None
        assert combate["lock"] is False

    def test_resolver_evento_inexistente_rechazado(self, cliente):
        _sembrar(cliente, "c41")
        cliente.post("/api/game/c41/combate/iniciar", json={"enemigo": 0})
        r = cliente.post("/api/game/c41/combate/evento", json={"opcion": 0})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "evento_invalido"

    def test_acciones_bloqueadas_mientras_hay_evento(self, cliente):
        _sembrar(cliente, "c42")
        cliente.post("/api/game/c42/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c42")
        from app.engine.combat import EVENTOS_MAPA

        estado.ev = EVENTOS_MAPA[0]
        estado.lock = True
        r = cliente.post(
            "/api/game/c42/combate/jugar", json={"indice": 0}
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "combate_bloqueado"
        r2 = cliente.post("/api/game/c42/combate/fin-turno", json={})
        assert r2.status_code == 400

    def test_snapshot_expone_evento_activo(self, cliente):
        _sembrar(cliente, "c43")
        cliente.post("/api/game/c43/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c43")
        from app.engine.combat import EVENTOS_MAPA

        estado.ev = EVENTOS_MAPA[3]
        estado.lock = True
        r = cliente.get("/api/game/c43/combate")
        ev = r.json()["data"]["combate"]["ev"]
        assert ev["nombre"] == "Tesoro abandonado"
        assert ev["texto"]
        assert len(ev["opciones"]) == 2


class TestExcesoDeMana:
    def test_ultimo_descarte_continua_el_turno(self, cliente):
        """`edisc` con ED→0 ejecuta la IA enemiga (js/07-campamento.js:84)."""
        _sembrar(cliente, "c50")
        cliente.post("/api/game/c50/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c50")
        estado.ed = 2
        r1 = cliente.post(
            "/api/game/c50/combate/descartar-exceso", json={"indice": 0}
        )
        assert r1.status_code == 200
        assert r1.json()["data"]["combate"]["ed"] == 1
        r2 = cliente.post(
            "/api/game/c50/combate/descartar-exceso", json={"indice": 0}
        )
        assert r2.status_code == 200
        combate = r2.json()["data"]["combate"]
        assert combate["ed"] == 0
        # el turno del jugador ya avanzó (turno 2 tras la IA)
        assert combate["jugador"]["turnos"] == 2

    def test_cancelar_exceso_deja_seguir_jugando(self, cliente):
        _sembrar(cliente, "c51")
        cliente.post("/api/game/c51/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("c51")
        estado.ed = 1
        r = cliente.post("/api/game/c51/combate/descartar-cancelar")
        assert r.status_code == 200
        assert r.json()["data"]["combate"]["ed"] == 0
        r2 = cliente.post(
            "/api/game/c51/combate/fin-turno", json={"forzar": True}
        )
        assert r2.status_code == 200

    def test_cancelar_sin_exceso_rechazado(self, cliente):
        _sembrar(cliente, "c52")
        cliente.post("/api/game/c52/combate/iniciar", json={"enemigo": 0})
        r = cliente.post("/api/game/c52/combate/descartar-cancelar")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "exceso_inexistente"


class TestVictoriaInmediataYReclamar:
    def test_atacar_matar_cierra_sin_fin_turno(self, cliente):
        _sembrar(cliente, "v1")
        cliente.post("/api/game/v1/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("v1")
        estado.E.hp = 1
        criatura = crear_carta_juego("ma")  # Maestro: ataque 4
        criatura.lista_para_atacar = True
        estado.P.bd = [criatura]
        r = cliente.post(
            "/api/game/v1/combate/atacar",
            json={"atacante": 0, "objetivo": -1},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["combate"]["fin"] == "w"
        victorias = [
            ev for ev in data["campaña"] if ev["tipo"] == "victoria"
        ]
        assert victorias
        assert len(victorias[0]["recompensas"]) == 3

    def test_jugar_carta_matar_cierra_sin_fin_turno(self, cliente):
        _sembrar(cliente, "v2")
        cliente.post("/api/game/v2/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("v2")
        estado.E.hp = 2
        estado.P.hand = [crear_carta_juego("cf")]  # 3 de daño
        estado.P.qi = 5
        r = cliente.post(
            "/api/game/v2/combate/jugar", json={"indice": 0}
        )
        assert r.status_code == 200
        assert r.json()["data"]["combate"]["fin"] == "w"

    def test_reclamar_anade_una_copia(self, cliente):
        _sembrar(cliente, "v3")
        store = cliente.app.state.store
        cliente.post("/api/game/v3/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("v3")
        estado.E.hp = 0
        from app.engine.combat import comprobar_fin

        comprobar_fin(estado)
        campaña = servicio._consumir_eventos("v3", estado)
        victoria = next(e for e in campaña if e["tipo"] == "victoria")
        carta = victoria["recompensas"][0]
        r = cliente.post(
            "/api/game/v3/combate/reclamar", json={"indice": 0}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["carta"] == carta
        assert data["copias"] == 1
        assert store.snapshot("v3")["col"][carta] == 1
        # Reclamar dos veces la misma carta acumula hasta 3 copias.
        servicio._rw_pendiente["v3"] = [carta]
        cliente.post("/api/game/v3/combate/reclamar", json={"indice": 0})
        servicio._rw_pendiente["v3"] = [carta]
        cliente.post("/api/game/v3/combate/reclamar", json={"indice": 0})
        assert store.snapshot("v3")["col"][carta] == 3
        servicio._rw_pendiente["v3"] = [carta]
        cliente.post("/api/game/v3/combate/reclamar", json={"indice": 0})
        assert store.snapshot("v3")["col"][carta] == 3

    def test_reclamar_sin_pendiente_rechazado(self, cliente):
        _sembrar(cliente, "v4")
        r = cliente.post("/api/game/v4/combate/reclamar", json={"indice": 0})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "recompensa_inexistente"

    def test_reclamar_indice_fuera_de_rango(self, cliente):
        _sembrar(cliente, "v5")
        cliente.post("/api/game/v5/combate/iniciar", json={"enemigo": 0})
        servicio = cliente.app.state.combat_service
        estado = servicio._estado("v5")
        estado.E.hp = 0
        from app.engine.combat import comprobar_fin

        comprobar_fin(estado)
        servicio._consumir_eventos("v5", estado)
        r = cliente.post("/api/game/v5/combate/reclamar", json={"indice": 9})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "recompensa_inexistente"
