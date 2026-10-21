"""Configuración del backend (lee variables de entorno, tiene defaults)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(clave: str, por_defecto: str) -> str:
    """Lee una variable de entorno, o `por_defecto` si no existe."""
    return os.environ.get(clave, por_defecto)


@dataclass(frozen=True)
class Settings:
    host: str = field(default_factory=lambda: _env("HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(_env("PORT", "8765")))
    saves_dir: Path = field(
        default_factory=lambda: Path(
            _env("SAVES_DIR", str(Path(__file__).resolve().parents[2] / "saves"))
        )
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origen.strip()
            for origen in _env(
                "CORS_ORIGINS",
                "http://127.0.0.1:5173,http://localhost:5173",
            ).split(",")
            if origen.strip()
        )
    )
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    version: str = "0.2.0"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Para tests: fuerza la relectura de env en la siguiente llamada."""
    global _settings
    _settings = None
