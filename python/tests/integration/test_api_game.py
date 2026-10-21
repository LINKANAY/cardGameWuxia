def test_nueva_partida_y_carga(cliente):
    respuesta = cliente.post("/api/game/new", json={"slot": "p1"})
    assert respuesta.status_code == 200
    instantanea = respuesta.json()["data"]["snapshot"]
    # snapshot = dict `data` en formato xcg3 (sin sobre {v,t,data})
    assert instantanea["sect"] == "esp"
    assert instantanea["stn"] == 30
    assert instantanea["wins"] == []
    assert instantanea["mat"] == {"h": 0, "n": 0, "p": 0}
    assert instantanea["rec"] == {"vit": 1, "tes": 1}
    # aún no ha elegido secta (sin victorias/colección)
    assert instantanea["sc"] is None

    respuesta_carga = cliente.get("/api/game/p1")
    assert respuesta_carga.status_code == 200
    assert respuesta_carga.json()["data"]["snapshot"]["sect"] == "esp"


def test_slot_inexistente_es_404_envelope(cliente):
    respuesta = cliente.get("/api/game/nope")
    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"]["code"] == "not_found"


def test_persiste_tras_reinicio(cliente, aplicacion):
    cliente.post("/api/game/new", json={"slot": "p1"})
    # simular restart: store nuevo, saves en disco intactos
    from app.state.session_store import SessionStore

    aplicacion.state.store = SessionStore()
    respuesta = cliente.get("/api/game/p1")
    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["snapshot"]["stn"] == 30


def test_confirmar_secta_fija_secta_y_regala_talisman(cliente):
    cliente.post("/api/game/new", json={"slot": "p1"})
    respuesta = cliente.post("/api/game/p1/secta", json={"secta": "val"})
    assert respuesta.status_code == 200
    instantanea = respuesta.json()["data"]["snapshot"]
    assert instantanea["sect"] == "val"
    assert instantanea["sc"] == "val"
    # regalo de la puerta: un Talismán de Escape (`pil.tes += 1`)
    assert instantanea["pil"]["tes"] == 1

    # persiste al releer desde disco
    carga = cliente.get("/api/game/p1").json()["data"]["snapshot"]
    assert carga["sc"] == "val"


def test_secta_invalida_devuelve_envelope_400(cliente):
    cliente.post("/api/game/new", json={"slot": "p1"})
    respuesta = cliente.post("/api/game/p1/secta", json={"secta": "zzz"})
    assert respuesta.status_code == 400
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"]["code"] == "secta_invalida"


def test_secta_en_slot_inexistente_es_404(cliente):
    respuesta = cliente.post("/api/game/nope/secta", json={"secta": "esp"})
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "not_found"


def test_error_no_manejado_devuelve_envelope(cliente, monkeypatch):
    from fastapi import Request

    @cliente.app.get("/api/_boom")
    def _boom(request: Request):
        raise RuntimeError("boom")

    respuesta = cliente.get("/api/_boom")
    assert respuesta.status_code == 500
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"]["code"] == "internal_error"
