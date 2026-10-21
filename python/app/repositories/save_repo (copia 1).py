"""Persistencia de partidas en disco (saves/*.json).

Única capa que toca el sistema de archivos. Escritura atómica + backup.
Nunca lanza por errores de disco en operaciones críticas de guardado.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("save_repo")


def _save_dir() -> Path:
    directorio = get_settings().saves_dir
    directorio.mkdir(parents=True, exist_ok=True)
    return directorio


def _safe_slot(slot: str) -> str:
    inofensivo = "".join(
        caracter
        for caracter in slot
        if caracter.isalnum() or caracter in "-_"
    ) or "default"
    return inofensivo


def save_path(slot: str) -> Path:
    return _save_dir() / f"{_safe_slot(slot)}.json"


def save(slot: str, state: dict[str, Any]) -> bool:
    """Guarda el estado. Rotación: .json → .json.bak, luego escribe el nuevo."""
    path = save_path(slot)
    try:
        payload = {"v": 1, "t": int(time.time() * 1000), "data": state}
        ruta_temporal = path.with_suffix(".json.tmp")
        ruta_temporal.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        if path.exists():
            path.replace(path.with_suffix(".json.bak"))
        ruta_temporal.replace(path)
        return True
    except OSError:
        logger.exception("No se pudo guardar slot=%s", slot)
        return False


def load(slot: str) -> dict[str, Any] | None:
    """Carga el estado. None si no existe o está corrupto (prueba backup)."""
    for path in (save_path(slot), save_path(slot).with_suffix(".json.bak")):
        if not path.exists():
            continue
        try:
            sobre = json.loads(path.read_text(encoding="utf-8"))
            datos = sobre.get("data")
            if isinstance(datos, dict):
                if path.suffixes[-2:] == [".json", ".bak"]:
                    logger.warning("slot=%s cargado desde backup", slot)
                return datos
        except (json.JSONDecodeError, OSError):
            logger.exception("Save corrupto: %s", path)
    return None


def delete(slot: str) -> bool:
    path = save_path(slot)
    ruta_respaldo = path.with_suffix(".json.bak")
    borrado = False
    for ruta in (path, ruta_respaldo):
        try:
            if ruta.exists():
                ruta.unlink()
                borrado = True
        except OSError:
            logger.exception("No se pudo borrar %s", ruta)
    return borrado


def list_slots() -> list[str]:
    try:
        return sorted(ruta.stem for ruta in _save_dir().glob("*.json"))
    except OSError:
        return []
