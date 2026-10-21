"""GET /api/slots — listado de partidas guardadas con su resumen."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.services.game_service import GameService


def _service(request: Request) -> GameService:
    return GameService(request.app.state.store)


router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.get("")
def list_slots(request: Request):
    resumenes = _service(request).list_slots()
    return exito({"slots": [resumen.model_dump() for resumen in resumenes]})
