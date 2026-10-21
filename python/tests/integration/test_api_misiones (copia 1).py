"""API de misiones — listar, reclamar y seguir (`mis` del JS)."""

from __future__ import annotations


def _sembrar(cliente, slot, **contadores):
    """Crea el slot y siembra contadores de misión (`qs`)."""
    cliente.post("/api/game/new", json={"slot": slot})
    store = cliente.app.state.store

    def mutador(partida):
        partida.misiones.update(contadores)

    store.mutate(slot, mutador)


def test_listar_misiones(cliente):
    _sembrar(cliente, "mi1", w=1)
    respuesta = cliente.get("/api/game/mi1/misiones")
    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    misiones = datos["misiones"]
    assert len(misiones) == 21 + 15  # GQ + missions(esp)
    por_id = {m["identificador"]: m for m in misiones}
    g1 = por_id["g1"]
    assert g1["progreso"] == 1 and g1["lista"] is True
    assert g1["grupo"] == "Combate" and g1["es_general"] is True
    g2 = por_id["g2"]
    assert g2["progreso"] == 1 and g2["lista"] is False
    # la UI agrupa por `grupo` (`missionGroup`): debe venir siempre
    assert all(m["grupo"] for m in misiones)
    assert por_id["esp3"]["grupo"] == "Progreso"
    assert por_id["esp3"]["es_general"] is False
    assert datos["tracker"] is None


def test_seguir_toggle(cliente):
    _sembrar(cliente, "mi2")
    r1 = cliente.post(
        "/api/game/mi2/misiones/seguir", json={"mision": "g1"}
    ).json()
    assert r1["data"]["track"] == "g1"
    assert r1["data"]["snapshot"]["qs"]["track"] == "g1"
    r2 = cliente.post(
        "/api/game/mi2/misiones/seguir", json={"mision": "g1"}
    ).json()
    assert r2["data"]["track"] == ""
    tracker = cliente.get("/api/game/mi2/misiones").json()["data"]
    assert tracker["tracker"] is None


def test_reclamar_rechaza_incompleta_y_duplicada(cliente):
    _sembrar(cliente, "mi3")
    r1 = cliente.post(
        "/api/game/mi3/misiones/reclamar", json={"mision": "g1"}
    ).json()
    assert r1["ok"] is False
    assert r1["error"]["code"] == "mision_incompleta"

    _sembrar(cliente, "mi4", w=1)
    ok = cliente.post(
        "/api/game/mi4/misiones/reclamar", json={"mision": "g1"}
    ).json()
    assert ok["ok"] is True
    assert "Misión cumplida: Primera sangre" in ok["data"]["mensaje"]
    assert ok["data"]["snapshot"]["mat"]["h"] == 2
    assert ok["data"]["snapshot"]["mat"]["p"] == 2
    assert ok["data"]["snapshot"]["qd"]["g1"] == 1

    duplicada = cliente.post(
        "/api/game/mi4/misiones/reclamar", json={"mision": "g1"}
    ).json()
    assert duplicada["ok"] is False
    assert duplicada["error"]["code"] == "mision_reclamada"


def test_reclamar_carta_rareza(cliente):
    _sembrar(cliente, "mi5", w=15)
    r = cliente.post(
        "/api/game/mi5/misiones/reclamar", json={"mision": "g2"}
    ).json()
    assert r["ok"] is True
    # g2: p10 n3 card3 → la carta (rareza 3) entra a la colección
    assert r["data"]["carta"] is not None
    col = r["data"]["snapshot"]["col"]
    assert any(v >= 1 for v in col.values())
    assert r["data"]["snapshot"]["qd"]["g2"] == 1


def test_reclamar_talismán(cliente):
    _sembrar(cliente, "mi6", bs=3)
    r = cliente.post(
        "/api/game/mi6/misiones/reclamar", json={"mision": "g3"}
    ).json()
    assert r["ok"] is True
    assert r["data"]["tes"] is True
    assert r["data"]["snapshot"]["pil"]["tes"] == 1


def test_tracker_muestra_progreso(cliente):
    _sembrar(cliente, "mi7", w=10)
    cliente.post("/api/game/mi7/misiones/seguir", json={"mision": "g2"})
    datos = cliente.get("/api/game/mi7/misiones").json()["data"]
    tracker = datos["tracker"]
    assert tracker["identificador"] == "g2"
    assert tracker["meta"] == 15 and tracker["progreso"] == 10
