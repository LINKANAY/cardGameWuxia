"""Envelope uniforme de respuestas API.

Éxito:  {"ok": true,  "data": {...}}
Error:  {"ok": false, "error": {"code": "...", "message": "..."}}

Las claves `ok`/`data`/`error`/`code`/`message` son el **formato de
hilo** acordado con la UI y con las pruebas del monolito: no se traducen.
Los nombres de las funciones y parámetros sí están en español.
"""

from __future__ import annotations

from typing import Any


def exito(datos: Any = None) -> dict:
    """Envelope de éxito: `{"ok": True, "data": datos}`."""
    return {"ok": True, "data": datos}


def fallo(codigo: str, mensaje: str) -> dict:
    """Envelope de error: `{"ok": False, "error": {code, message}}`."""
    return {"ok": False, "error": {"code": codigo, "message": mensaje}}
