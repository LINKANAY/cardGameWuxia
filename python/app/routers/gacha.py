"""Endpoints del gacha: invocar en la Ceremonia de Adivinación.

Espejo del modal `.gachab` del monolito (`GachaSystem.draw`). Cada
tirada muta la partida del slot con auto-guardado (`SessionStore.mutate`)
y devuelve el snapshot actualizado dentro del sobre uniforme.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.gacha import TirarRequest
from app.services.gacha_service import GachaService


def _service(request: Request) -> GachaService:
    return GachaService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/gacha", tags=["gacha"])


@router.post("/tirar")
def tirar(slot: str, body: TirarRequest, request: Request):
    resultado = _service(request).tirar(slot, body.pool, body.count)
    return exito({"slot": slot, **resultado})
