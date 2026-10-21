"""Fixtures compartidas: aplicación de prueba con saves en directorio temporal."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture()
def aplicacion(tmp_path, monkeypatch):
    """App FastAPI con saves_dir apuntando a un tmp y settings frescos."""
    monkeypatch.setenv("SAVES_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    from app.config import reset_settings

    reset_settings()

    from app.main import create_app

    application = create_app()
    # levantar lifespan manualmente (TestClient lo hace, pero así queda explícito)
    return application


@pytest.fixture()
def cliente(aplicacion):
    from fastapi.testclient import TestClient

    # raise_server_exceptions=False: deja que el handler global maneje
    # los errores inesperados y devuelva el envelope 500
    with TestClient(aplicacion, raise_server_exceptions=False) as cliente_prueba:
        yield cliente_prueba
