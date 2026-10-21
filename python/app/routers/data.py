"""Endpoints de solo lectura del catálogo estático para la UI.

Todas las respuestas salen del `DataService` (dataclasses → resúmenes
pydantic) envueltas en el envelope uniforme. No hay estado que mutar.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.envelope import exito
from app.services.data_service import DataService

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/sectas")
def sectas():
    datos = DataService().sectas()
    return exito({"sectas": [dato.model_dump() for dato in datos]})


@router.get("/cartas")
def cartas():
    datos = DataService().cartas()
    return exito({"cartas": [dato.model_dump() for dato in datos]})


@router.get("/enemigos")
def enemigos():
    datos = DataService().enemigos()
    return exito({"enemigos": [dato.model_dump() for dato in datos]})


@router.get("/mazmorras")
def mazmorras():
    """Catálogo de mazmorras de recetas (`DG` del JS) para el tab `dgn`."""
    datos = DataService().mazmorras()
    return exito({"mazmorras": [dato.model_dump() for dato in datos]})


@router.get("/bestias")
def bestias():
    """Bestias domables por jefe de nivel (`BEAST` del JS)."""
    datos = DataService().bestias()
    return exito({"bestias": [dato.model_dump() for dato in datos]})


@router.get("/equipo")
def equipo():
    """Huecos y piezas de la Herrería (`GEAR`/`SLOTS` para `eqp`)."""
    datos = DataService().equipo()
    return exito({"equipo": datos.model_dump()})


@router.get("/trajes")
def trajes():
    """Armario completo de trajes (`OF`/`OAT` de las 10 sectas)."""
    datos = DataService().trajes()
    return exito({"trajes": [dato.model_dump() for dato in datos]})


@router.get("/misiones")
def misiones(secta: str):
    """Misiones generales + de la secta (`GQ` + `missions`) para `mis`.

    Args:
        secta: clave de la secta del jugador (`sect`).
    """
    datos = DataService().misiones(secta)
    return exito({"misiones": [dato.model_dump() for dato in datos]})


@router.get("/narrativa")
def narrativa():
    return exito({"narrativa": DataService().narrativa().model_dump()})


@router.get("/alquimia")
def alquimia():
    datos = DataService().alquimia()
    return exito(
        {
            "pildoras": [dato.model_dump() for dato in datos.pildoras],
            "forja": [dato.model_dump() for dato in datos.forja],
        }
    )


@router.get("/mercado")
def mercado():
    datos = DataService().mercado()
    return exito(
        {
            "puestos": [dato.model_dump() for dato in datos.puestos],
            "precios_venta": datos.precios_venta,
            "pildoras_en_venta": [
                dato.model_dump() for dato in datos.pildoras_en_venta
            ],
        }
    )


@router.get("/cartas/{identificador}/detalle")
def detalle_carta(identificador: str, secta: str | None = None):
    """Detalle de carta para el modal del mercado (`mkDet` del JS).

    Args:
        identificador: id de la carta en el catálogo `C`.
        secta: secta del jugador (`schosen`); afecta a la línea de
            bloqueo de «Obtención».
    """
    datos = DataService().detalle_carta(identificador, secta)
    return exito({"carta": datos.model_dump()})


@router.get("/gacha")
def gacha():
    """Catálogo estático del gacha para el modal de invocación."""
    datos = DataService().gacha()
    return exito(
        {
            "tickets": [dato.model_dump() for dato in datos.tickets],
            "pools": [dato.model_dump() for dato in datos.pools],
            "rarezas": [dato.model_dump() for dato in datos.rarezas],
        }
    )
