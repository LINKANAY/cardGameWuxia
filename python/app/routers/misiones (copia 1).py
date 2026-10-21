"""Endpoints de misiones: listar, reclamar y seguir (`mis` del JS).

Espejo del tab `mis` del monolito. Cada acción muta la partida del
slot con auto-guardado (`SessionStore.mutate`) y devuelve el snapshot
actualizado dentro del sobre uniforme.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.misiones import ReclamarMisionRequest, SeguirMisionRequest
from app.services.mision_service import MisionService


def _service(request: Request) -> MisionService:
    return MisionService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/misiones", tags=["misiones"])


@router.get("")
def listar(slot: str, request: Request):
    """Misiones del jugador con progreso y estado (`[...GQ, ...missions]`)."""
    misiones = _service(request).listar(slot)
    tracker = _service(request).tracker(slot)
    return exito({"misiones": misiones, "tracker": tracker})


@router.post("/reclamar")
def reclamar(slot: str, body: ReclamarMisionRequest, request: Request):
    """Reclama una misión cumplida (`claimQ` del JS)."""
    resultado = _service(request).reclamar(slot, body.mision)
    return exito({"slot": slot, **resultado})


@router.post("/seguir")
def seguir(slot: str, body: SeguirMisionRequest, request: Request):
    """Activa/desactiva el seguimiento (`missionTrack` del JS)."""
    resultado = _service(request).seguir(slot, body.mision)
    return exito({"slot": slot, **resultado})
