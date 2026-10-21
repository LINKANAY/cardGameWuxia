from app.state.session_store import SessionStore


def _reset_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    from app.config import reset_settings

    reset_settings()


def test_get_or_create_new(tmp_path, monkeypatch):
    _reset_settings(tmp_path, monkeypatch)
    tienda = SessionStore()
    partida = tienda.get_or_create("p1")
    assert partida.secta == "esp"
    assert partida.piedras_espirituales == 30
    assert partida.recetas == {"vit": 1, "tes": 1}


def test_mutate_autosaves(tmp_path, monkeypatch):
    _reset_settings(tmp_path, monkeypatch)
    tienda = SessionStore()
    tienda.create("p1")
    tienda.mutate("p1", lambda partida: setattr(partida, "secta", "mon"))
    # otra instancia (simula restart) ve el cambio sin cargar explícitamente
    segunda_tienda = SessionStore()
    assert segunda_tienda.get_or_create("p1").secta == "mon"


def test_create_resets(tmp_path, monkeypatch):
    _reset_settings(tmp_path, monkeypatch)
    tienda = SessionStore()
    tienda.mutate(
        "p1",
        lambda partida: setattr(partida, "piedras_espirituales", 999),
    )
    partida_nueva = tienda.create("p1")
    assert partida_nueva.piedras_espirituales == 30


def test_save_all(tmp_path, monkeypatch):
    _reset_settings(tmp_path, monkeypatch)
    tienda = SessionStore()
    tienda.create("a")
    tienda.create("b")
    assert tienda.save_all() == 2


def test_snapshot_is_xcg3_data_dict(tmp_path, monkeypatch):
    _reset_settings(tmp_path, monkeypatch)
    tienda = SessionStore()
    instantanea = tienda.snapshot("p1")
    assert set(instantanea) == {
        "realm", "hp", "wins", "col", "sect", "mat", "stn", "dk", "ad",
        "pil", "of", "rec", "be", "gr", "eq", "sc", "du", "dt", "bt",
        "qs", "qd", "gt", "gp",
        # clave backend del xcg_horno del monolito (horno de alquimia)
        "xn",
        # jardín medicinal (módulo nuevo del backend)
        "jdn", "sd", "fg",
    }
