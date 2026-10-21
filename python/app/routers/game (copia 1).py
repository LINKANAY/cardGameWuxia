"""Endpoints de partida: crear, leer snapshot y borrar."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.game import ConfirmarSectaRequest, NewGameRequest
from app.services.game_service import GameService


def _service(request: Request) -> GameService:
    return GameService(request.app.state.store)


router = APIRouter(prefix="/api/game", tags=["game"])


@router.post("/new")
def new_game(body: NewGameRequest, request: Request):
    snapshot = _service(request).new_game(body.slot)
    return exito({"slot": body.slot, "snapshot": snapshot})


@router.post("/{slot}/secta")
def confirmar_secta(slot: str, body: ConfirmarSectaRequest, request: Request):
    """Confirma la secta en la puerta (`confirmS` de js/06-contenido.js:72)."""
    snapshot = _service(request).confirmar_secta(slot, body.secta)
    return exito({"slot": slot, "snapshot": snapshot})


@router.get("/{slot}")
def get_game(slot: str, request: Request):
    snapshot = _service(request).snapshot(slot)
    return exito({"slot": slot, "snapshot": snapshot})


@router.delete("/{slot}")
def delete_game(slot: str, request: Request):
    _service(request).delete_game(slot)
    return exito({"slot": slot})
