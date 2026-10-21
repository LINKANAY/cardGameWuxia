"""Endpoints de equipo: Herrería, huecos, bestia de ayuda y trajes.

Espejo de las pestañas `eqp`/`trj` del monolito. Cada acción muta la
partida del slot con auto-guardado (`SessionStore.mutate`) y devuelve
el snapshot actualizado dentro del sobre uniforme.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.equipo import BestiaRequest, PiezaRequest, TrajeRequest
from app.services.equipment_service import EquipmentService


def _service(request: Request) -> EquipmentService:
    return EquipmentService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}", tags=["equipo"])


@router.post("/equipo/forjar")
def forjar(slot: str, body: PiezaRequest, request: Request):
    """Forja una pieza de la Herrería (`forgeG(id)` del JS)."""
    resultado = _service(request).forjar(slot, body.pieza)
    return exito({"slot": slot, **resultado})


@router.post("/equipo/equipar")
def equipar(slot: str, body: PiezaRequest, request: Request):
    """Equipa o retira una pieza poseída (`wearG(id)` del JS)."""
    resultado = _service(request).equipar(slot, body.pieza)
    return exito({"slot": slot, **resultado})


@router.post("/equipo/bestia")
def equipar_bestia(slot: str, body: BestiaRequest, request: Request):
    """Equipa o retira la bestia de ayuda (`eqB(id)` del JS)."""
    resultado = _service(request).equipar_bestia(slot, body.bestia)
    return exito({"slot": slot, **resultado})


@router.post("/traje/vestir")
def vestir(slot: str, body: TrajeRequest, request: Request):
    """Viste un traje del armario (`wear(k, i)` del JS)."""
    resultado = _service(request).vestir(slot, body.secta, body.indice)
    return exito({"slot": slot, **resultado})
