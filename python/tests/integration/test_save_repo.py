import json

from app.config import get_settings
from app.repositories import save_repo


def _datos(persistidos=1):
    return {"version": 1, "n": persistidos, "sect": "esp"}


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    from app.config import reset_settings

    reset_settings()
    assert save_repo.save("p1", _datos(7))
    cargado = save_repo.load("p1")
    assert cargado == _datos(7)


def test_rotacion_de_respaldo(tmp_path, monkeypatch):
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    from app.config import reset_settings

    reset_settings()
    save_repo.save("p1", _datos(1))
    save_repo.save("p1", _datos(2))
    respaldo = save_repo.save_path("p1").with_suffix(".json.bak")
    assert respaldo.exists()
    assert json.loads(respaldo.read_text())["data"] == _datos(1)
    assert save_repo.load("p1") == _datos(2)


def test_corrupto_vuelve_al_respaldo(tmp_path, monkeypatch):
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    from app.config import reset_settings

    reset_settings()
    save_repo.save("p1", _datos(1))
    save_repo.save("p1", _datos(2))  # respaldo tiene _datos(1)
    save_repo.save_path("p1").write_text("{corrupto", encoding="utf-8")
    assert save_repo.load("p1") == _datos(1)


def test_cargar_inexistente_devuelve_none(tmp_path, monkeypatch):
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    from app.config import reset_settings

    reset_settings()
    assert save_repo.load("nope") is None


def test_listar_y_borrar(tmp_path, monkeypatch):
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    from app.config import reset_settings

    reset_settings()
    save_repo.save("a", _datos())
    save_repo.save("b", _datos())
    assert set(save_repo.list_slots()) >= {"a", "b"}
    assert save_repo.delete("a")
    assert "a" not in save_repo.list_slots()
