from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError


def test_valores_por_defecto():
    assert NotFoundError.code == "not_found" and NotFoundError.status == 404
    assert ValidationError.code == "validation_error" and ValidationError.status == 400
    assert ConflictError.code == "conflict" and ConflictError.status == 409


def test_excepcion_con_codigo_y_estado_propios():
    error = AppError("x", code="custom", status=418)
    assert error.code == "custom" and error.status == 418


def test_mensaje():
    error = NotFoundError("falta")
    assert error.message == "falta"
    assert str(error) == "falta"
