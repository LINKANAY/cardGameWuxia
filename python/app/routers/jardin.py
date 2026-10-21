"""Endpoints del Jardín Medicinal — estado, sembrar, acelerar, cosechar.

Módulo nuevo (no existe en el monolito). Cada acción muta la partida
del slot con auto-guardado (`SessionStore.mutate`) y devuelve el
estado del jardín actualizado dentro del sobre uniforme. El botín de
boticario y el regalo de ascensión **no** tienen endpoint: se enganchan
a la resolución de la victoria (como el envoltorio de `notifyWin` del
JS).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.jardin import (
    AcelerarRequest,
    CasillaRequest,
    FormacionRequest,
    SembrarRequest,
)
from app.services.jardin_service import JardinService


def _service(request: Request) -> JardinService:
    return JardinService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/jardin", tags=["jardin"])


@router.get("/estado")
def estado(slot: str, request: Request):
    """Jardín, semillas, formaciones y mejoras con tiempos calculados."""
    datos = _service(request).estado(slot)
    return exito({"slot": slot, **datos})


@router.post("/sembrar")
def sembrar(slot: str, body: SembrarRequest, request: Request):
    """Siembra una semilla en una casilla vacía (gasta 1 semilla)."""
    datos = _service(request).sembrar(slot, body.indice, body.planta)
    return exito({"slot": slot, **datos})


@router.post("/acelerar")
def acelerar(slot: str, body: AcelerarRequest, request: Request):
    """Gasta piedras espirituales: cada una quita 5 % del resto."""
    datos = _service(request).acelerar(slot, body.indice, body.piedras)
    return exito({"slot": slot, **datos})


@router.post("/cosechar")
def cosechar(slot: str, body: CasillaRequest, request: Request):
    """Cosecha una planta lista: hierbas al Horno y casilla libre."""
    datos = _service(request).cosechar(slot, body.indice)
    return exito({"slot": slot, **datos})


@router.post("/mejorar")
def mejorar(slot: str, request: Request):
    """Amplía la cuadrícula (4 → 6 → 9 → 12) pagando materiales."""
    datos = _service(request).mejorar(slot)
    return exito({"slot": slot, **datos})


@router.post("/formacion")
def formacion(slot: str, body: FormacionRequest, request: Request):
    """Equipa o quita la formación de crecimiento del jardín."""
    datos = _service(request).equipar_formacion(slot, body.identificador)
    return exito({"slot": slot, **datos})
