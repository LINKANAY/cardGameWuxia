"""Endpoints de mazos: crear, editar, activar y desequipar.

Espejo del tab `dk` del monolito. Cada acción muta la partida del
slot con auto-guardado (`SessionStore.mutate`) y devuelve el snapshot
actualizado dentro del sobre uniforme.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.decks import (
    CartaEnMazoRequest,
    CrearMazoRequest,
    IndiceMazoRequest,
    RenombrarMazoRequest,
    UsarMazoRequest,
)
from app.schemas.envelope import exito
from app.services.deck_service import DeckService


def _service(request: Request) -> DeckService:
    return DeckService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/mazos", tags=["mazos"])


@router.post("")
def crear(slot: str, body: CrearMazoRequest, request: Request):
    resultado = _service(request).crear(slot, body.desde_automatico)
    return exito({"slot": slot, **resultado})


@router.post("/usar")
def usar(slot: str, body: UsarMazoRequest, request: Request):
    resultado = _service(request).usar(slot, body.indice)
    return exito({"slot": slot, **resultado})


@router.post("/duplicar")
def duplicar(slot: str, body: IndiceMazoRequest, request: Request):
    resultado = _service(request).duplicar(slot, body.indice)
    return exito({"slot": slot, **resultado})


@router.post("/eliminar")
def eliminar(slot: str, body: IndiceMazoRequest, request: Request):
    resultado = _service(request).eliminar(slot, body.indice)
    return exito({"slot": slot, **resultado})


@router.post("/desequipar")
def desequipar(slot: str, body: CartaEnMazoRequest, request: Request):
    resultado = _service(request).desequipar(slot, body.carta)
    return exito({"slot": slot, **resultado})


@router.post("/{indice}/renombrar")
def renombrar(slot: str, indice: int, body: RenombrarMazoRequest, request: Request):
    resultado = _service(request).renombrar(slot, indice, body.nombre)
    return exito({"slot": slot, **resultado})


@router.post("/{indice}/anadir")
def anadir(slot: str, indice: int, body: CartaEnMazoRequest, request: Request):
    resultado = _service(request).anadir(slot, indice, body.carta)
    return exito({"slot": slot, **resultado})


@router.post("/{indice}/quitar")
def quitar(slot: str, indice: int, body: CartaEnMazoRequest, request: Request):
    resultado = _service(request).quitar(slot, indice, body.carta)
    return exito({"slot": slot, **resultado})


@router.post("/{indice}/vaciar")
def vaciar(slot: str, indice: int, request: Request):
    resultado = _service(request).vaciar(slot, indice)
    return exito({"slot": slot, **resultado})


@router.post("/{indice}/autocompletar")
def autocompletar(slot: str, indice: int, request: Request):
    resultado = _service(request).autocompletar(slot, indice)
    return exito({"slot": slot, **resultado})
