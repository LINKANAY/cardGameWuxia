"""Endpoints de alquimia: elaborar, forjar, fusionar y desmantelar.

Espejo del tab `alq` del monolito. Cada acción muta la partida del
slot con auto-guardado (`SessionStore.mutate`) y devuelve el snapshot
actualizado dentro del sobre uniforme.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.alchemy import CartaRequest, ElaborarRequest, ForjarRequest
from app.schemas.envelope import exito
from app.services.alchemy_service import AlchemyService


def _service(request: Request) -> AlchemyService:
    return AlchemyService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/alquimia", tags=["alquimia"])


@router.post("/elaborar")
def elaborar(slot: str, body: ElaborarRequest, request: Request):
    resultado = _service(request).elaborar(slot, body.pildora)
    return exito({"slot": slot, **resultado})


@router.post("/forjar")
def forjar(slot: str, body: ForjarRequest, request: Request):
    resultado = _service(request).forjar(slot, body.rareza)
    return exito({"slot": slot, **resultado})


@router.post("/fusionar")
def fusionar(slot: str, body: CartaRequest, request: Request):
    resultado = _service(request).fusionar(slot, body.carta)
    return exito({"slot": slot, **resultado})


@router.post("/desmantelar")
def desmantelar(slot: str, body: CartaRequest, request: Request):
    resultado = _service(request).desmantelar(slot, body.carta)
    return exito({"slot": slot, **resultado})
