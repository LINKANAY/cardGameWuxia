"""Endpoints del mercado: comprar/vender cartas, materiales y píldoras.

Espejo del tab `mkt` del monolito (`buy`/`buyM`/`sellM`/`buyC`). Cada
acción muta la partida del slot con auto-guardado (`SessionStore.mutate`)
y devuelve el snapshot actualizado dentro del sobre uniforme.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.market import (
    ComprarCartaRequest,
    ComprarMaterialRequest,
    ComprarPildoraRequest,
    VenderMaterialRequest,
)
from app.services.market_service import MarketService


def _service(request: Request) -> MarketService:
    return MarketService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/mercado", tags=["mercado"])


@router.post("/comprar")
def comprar_carta(slot: str, body: ComprarCartaRequest, request: Request):
    resultado = _service(request).comprar_carta(slot, body.carta)
    return exito({"slot": slot, **resultado})


@router.post("/comprar-material")
def comprar_material(
    slot: str, body: ComprarMaterialRequest, request: Request
):
    resultado = _service(request).comprar_material(
        slot, body.puesto, body.confirmado
    )
    return exito({"slot": slot, **resultado})


@router.post("/vender")
def vender_material(slot: str, body: VenderMaterialRequest, request: Request):
    resultado = _service(request).vender_material(slot, body.material)
    return exito({"slot": slot, **resultado})


@router.post("/comprar-pildora")
def comprar_pildora(
    slot: str, body: ComprarPildoraRequest, request: Request
):
    resultado = _service(request).comprar_pildora(slot, body.pildora)
    return exito({"slot": slot, **resultado})
