"""Endpoints de slots: listado con resumen y borrado de partidas."""

from __future__ import annotations

from app.repositories import save_repo


def test_list_slots_vacio_al_iniciar(cliente):
    respuesta = cliente.get("/api/slots")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    assert cuerpo["data"]["slots"] == []


def test_list_slots_refleja_las_creadas(cliente):
    cliente.post("/api/game/new", json={"slot": "alpha"})
    cliente.post("/api/game/new", json={"slot": "beta"})

    respuesta = cliente.get("/api/slots")
    assert respuesta.status_code == 200
    resumenes = respuesta.json()["data"]["slots"]
    por_nombre = {resumen["slot"]: resumen for resumen in resumenes}
    assert set(por_nombre) == {"alpha", "beta"}
    for nombre in ("alpha", "beta"):
        assert por_nombre[nombre]["nivel_reino"] == 0
        assert por_nombre[nombre]["secta"] == "esp"
        assert por_nombre[nombre]["victorias"] == 0


def test_delete_slot_borra_archivo_y_desaparece(cliente):
    cliente.post("/api/game/new", json={"slot": "borrable"})
    assert save_repo.load("borrable") is not None

    respuesta = cliente.delete("/api/game/borrable")
    assert respuesta.status_code == 200
    assert respuesta.json()["ok"] is True

    # sin archivo en disco y fuera del listado
    assert save_repo.load("borrable") is None
    nombres = [
        resumen["slot"]
        for resumen in cliente.get("/api/slots").json()["data"]["slots"]
    ]
    assert "borrable" not in nombres
    # y el GET correspondiente pasa a 404
    assert cliente.get("/api/game/borrable").status_code == 404


def test_delete_slot_inexistente_es_404_envelope(cliente):
    respuesta = cliente.delete("/api/game/fantasma")
    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False
    assert cuerpo["error"]["code"] == "not_found"
