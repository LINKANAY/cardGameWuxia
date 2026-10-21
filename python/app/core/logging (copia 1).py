"""Logging con contexto. Nivel desde settings."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # ya configurado (tests)
    handler = logging.StreamHandler(sys.stdout)
    formato = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(formato, "%H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"sendero.{name}")
