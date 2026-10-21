from app.schemas.envelope import exito, fallo


def test_exito_con_datos():
    respuesta = exito({"x": 1})
    assert respuesta == {"ok": True, "data": {"x": 1}}


def test_exito_sin_datos():
    assert exito() == {"ok": True, "data": None}


def test_fallo_con_error():
    respuesta = fallo("not_found", "No existe")
    assert respuesta == {
        "ok": False,
        "error": {"code": "not_found", "message": "No existe"},
    }
