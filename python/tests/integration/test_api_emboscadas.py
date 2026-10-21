"""API de emboscadas — sorteo al reclamar, combate dinámico y huida."""

from __future__ import annotations

from app.engine import combat, emboscadas
from app.engine.emboscadas import NOMBRES_ALQUIMISTA, NOMBRES_BOTICARIO


def _sembrar(cliente, slot, *, vida=None, reino=0, victorias=None):
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        partida.nivel_reino = reino
        if vida is not None:
            partida.vida_hroe = vida
        if victorias is not None:
            partida.victorias = list(victorias)

    store.mutate(slot, mutador)


def _forzar_sorteo(monkeypatch, tipo: str, receta: str):
    """Sustituye el sorteo real por uno fijo (sólo para el test)."""

    def sorteo_fijo(*_args, **_kwargs):
        return emboscadas.Sorteo(tipo=tipo, receta=receta)

    monkeypatch.setattr(emboscadas, "sortear_amboscada", sorteo_fijo)


def _victoria(cliente, slot: str) -> dict:
    """Mata al enemigo activo y devuelve el evento de campaña."""
    servicio = cliente.app.state.combat_service
    estado = servicio._estado(slot)
    estado.E.hp = 0
    combat.comprobar_fin(estado)
    campaña = servicio._consumir_eventos(slot, estado)
    return next(e for e in campaña if e["tipo"] == "victoria")


def _reclamar(cliente, slot: str):
    return cliente.post(
        f"/api/game/{slot}/combate/reclamar", json={"indice": 0}
    )


class TestSorteoAlReclamar:
    def test_sin_emboscada_no_lleva_la_clave(self, cliente, monkeypatch):
        _sembrar(cliente, "a1")
        monkeypatch.setattr(emboscadas, "sortear_amboscada", lambda *a, **k: None)
        cliente.post("/api/game/a1/combate/iniciar", json={"enemigo": 0})
        _victoria(cliente, "a1")
        data = _reclamar(cliente, "a1").json()["data"]
        assert "emboscada" not in data

    def test_emboscada_encadenada_esta_vetada(self, cliente, monkeypatch):
        """La victoria sobre una emboscada no sortea otra (`ch.amb`)."""
        _sembrar(cliente, "a2")
        original = emboscadas.sortear_amboscada
        _forzar_sorteo(monkeypatch, "boticario", "rcB")
        cliente.post("/api/game/a2/combate/iniciar", json={"enemigo": 0})
        _victoria(cliente, "a2")
        data = _reclamar(cliente, "a2").json()["data"]
        assert data["emboscada"] == {"boticario": True}
        cliente.post("/api/game/a2/combate/emboscada/iniciar", json={})
        _victoria(cliente, "a2")
        # Sorteo real otra vez: `es_amboscada` corta antes del RNG.
        monkeypatch.setattr(emboscadas, "sortear_amboscada", original)
        data2 = _reclamar(cliente, "a2").json()["data"]
        assert "emboscada" not in data2


class TestFlujoBoticario:
    def test_combate_botin_y_contadores(self, cliente, monkeypatch):
        _sembrar(cliente, "b1")
        original = emboscadas.sortear_amboscada
        _forzar_sorteo(monkeypatch, "boticario", "rcB")
        cliente.post("/api/game/b1/combate/iniciar", json={"enemigo": 0})
        _victoria(cliente, "b1")

        data = _reclamar(cliente, "b1").json()["data"]
        assert data["emboscada"] == {"boticario": True}

        r2 = cliente.post("/api/game/b1/combate/emboscada/iniciar", json={})
        combate = r2.json()["data"]["combate"]
        assert combate["indice_enemigo"] is None
        assert combate["enemigo"]["nombre"] in NOMBRES_BOTICARIO
        assert combate["fin"] == ""

        victoria = _victoria(cliente, "b1")
        assert victoria["receta"] == "rcB"
        # Receta nueva → sin píldora de regalo (`!found` corta el roll).
        assert victoria["boticario"] == {"pildora": None}
        # Botín del Jardín enganchado a la victoria del boticario.
        botin = victoria["jardin"]
        assert sum(botin["semillas"].values()) >= 1
        assert "formacion" in botin

        snapshot = cliente.app.state.store.snapshot("b1")
        assert snapshot["qs"]["bt"] == 1
        assert snapshot["qs"]["am"] == 1
        assert snapshot["rec"]["rcB"] == 1
        # Sin Talismán de Escape: la emboscada es de d=1.
        assert snapshot["pil"].get("tes", 0) == 0

        # Reclamar la victoria de la emboscada no sortea otra.
        monkeypatch.setattr(emboscadas, "sortear_amboscada", original)
        data2 = _reclamar(cliente, "b1").json()["data"]
        assert "emboscada" not in data2

    def test_iniciar_normal_descarta_la_pendiente(self, cliente, monkeypatch):
        _sembrar(cliente, "b2")
        _forzar_sorteo(monkeypatch, "boticario", "rcA")
        cliente.post("/api/game/b2/combate/iniciar", json={"enemigo": 0})
        _victoria(cliente, "b2")
        _reclamar(cliente, "b2")
        # `begin` hace `amb = null`: otro combate descarta la emboscada.
        cliente.post("/api/game/b2/combate/iniciar", json={"enemigo": 0})
        r = cliente.post("/api/game/b2/combate/emboscada/iniciar", json={})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "sin_emboscada"


class TestFlujoAlquimista:
    def test_d5_sin_tes_sin_reliquia_sin_ascenso(self, cliente, monkeypatch):
        _sembrar(cliente, "q1", victorias=[])
        _forzar_sorteo(monkeypatch, "alquimista", "qi2")
        # ENEMIGOS[4] = nivel 0, dificultad 4 → la emboscada sube a d=5.
        cliente.post("/api/game/q1/combate/iniciar", json={"enemigo": 4})
        victoria_normal = _victoria(cliente, "q1")
        assert victoria_normal["materiales"].get("tes") == 1
        _reclamar(cliente, "q1")

        r2 = cliente.post("/api/game/q1/combate/emboscada/iniciar", json={})
        combate = r2.json()["data"]["combate"]
        assert combate["enemigo"]["nombre"] in NOMBRES_ALQUIMISTA
        assert combate["indice_enemigo"] is None

        tes_antes = cliente.app.state.store.snapshot("q1")["pil"].get(
            "tes", 0
        )
        victoria = _victoria(cliente, "q1")
        assert victoria["receta"] == "qi2"
        assert "boticario" not in victoria  # es alquimista, no boticario
        assert "jardin" not in victoria
        assert victoria["materiales"].get("tes") is None  # `!ch.amb`
        assert victoria["reliquia"] is None  # `!ch.amb`
        assert victoria["vida_max_reseteada"] is False  # d=5 con `ch.amb`
        assert victoria["ascenso"] is False  # no hay `first` (indice None)

        snapshot = cliente.app.state.store.snapshot("q1")
        assert snapshot["pil"].get("tes", 0) == tes_antes
        assert snapshot["qs"]["am"] == 1
        assert snapshot["qs"].get("bs", 0) == 0
        assert snapshot["rec"]["qi2"] == 1
        # Sólo cuenta la victoria normal (indice 4); la emboscada no.
        assert snapshot["wins"] == [4]


class TestAscensoDelReino:
    def test_jefe_de_nivel_entrega_el_regalo(self, cliente, monkeypatch):
        _sembrar(cliente, "s1", reino=0)
        monkeypatch.setattr(
            emboscadas, "sortear_amboscada", lambda *a, **k: None
        )
        # ENEMIGOS[5] = jefe de nivel 0 (d=5): primera victoria asciende.
        cliente.post("/api/game/s1/combate/iniciar", json={"enemigo": 5})
        victoria = _victoria(cliente, "s1")
        assert victoria["ascenso"] is True
        regalo = victoria["jardin"]
        assert regalo["semilla"] is not None
        assert regalo["formacion"] is not None

        snapshot = cliente.app.state.store.snapshot("s1")
        assert snapshot["realm"] == 1
        assert snapshot["sd"].get(regalo["semilla"], 0) >= 1
        assert snapshot["fg"].get(regalo["formacion"], 0) >= 1


class TestHuir:
    def test_huir_descarta_y_no_se_puede_repetir(self, cliente, monkeypatch):
        _sembrar(cliente, "h1")
        _forzar_sorteo(monkeypatch, "alquimista", "qi2")
        cliente.post("/api/game/h1/combate/iniciar", json={"enemigo": 0})
        _victoria(cliente, "h1")
        _reclamar(cliente, "h1")

        r = cliente.post("/api/game/h1/combate/emboscada/huir")
        assert r.status_code == 200
        assert r.json()["data"]["emboscada"] is None
        r2 = cliente.post("/api/game/h1/combate/emboscada/huir")
        assert r2.status_code == 400
        assert r2.json()["error"]["code"] == "sin_emboscada"
        r3 = cliente.post("/api/game/h1/combate/emboscada/iniciar", json={})
        assert r3.status_code == 400

    def test_iniciar_sin_pendiente_rechazado(self, cliente):
        _sembrar(cliente, "h2")
        r = cliente.post("/api/game/h2/combate/emboscada/iniciar", json={})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "sin_emboscada"
