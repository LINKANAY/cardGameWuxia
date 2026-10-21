"""Endpoints del Horno de Alquimia — inventario, resumen, refinar, usar.

Espejo de la API pública `window.HornoAlq` de `js/11-horno.js`. Cada
acción muta la partida del slot con auto-guardado
(`SessionStore.mutate`) y devuelve el estado del horno actualizado
dentro del sobre uniforme. El botín de victoria no tiene endpoint: se
engancha al resolver la victoria en `CombatService` (como el envoltorio
de `notifyWin` del JS).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.envelope import exito
from app.schemas.horno import HierbasRequest, UsarPildoraRequest
from app.services.horno_service import HornoService


def _service(request: Request) -> HornoService:
    return HornoService(request.app.state.store)


router = APIRouter(prefix="/api/game/{slot}/horno", tags=["horno"])


@router.get("/estado")
def estado(slot: str, request: Request):
    """Inventario de hierbas/píldoras y vida del héroe."""
    datos = _service(request).estado(slot)
    return exito({"slot": slot, **datos})


@router.post("/resumen")
def resumen(slot: str, body: HierbasRequest, request: Request):
    """Probabilidad/desglose de una combinación (sin gastar nada)."""
    datos = _service(request).resumen(slot, body.ids)
    return exito({"slot": slot, "resumen": datos})


@router.post("/refinar")
def refinar(slot: str, body: HierbasRequest, request: Request):
    """Refina la combinación: gasta hierbas y produce una píldora."""
    datos = _service(request).refinar(slot, body.ids)
    return exito({"slot": slot, **datos})


@router.post("/usar")
def usar(slot: str, body: UsarPildoraRequest, request: Request):
    """Consume una píldora del horno (cura fuera de combate)."""
    datos = _service(request).usar_pildora(slot, body.clave)
    return exito({"slot": slot, **datos})


@router.post("/reiniciar")
def reiniciar(slot: str, request: Request):
    """Restaura el inventario inicial del horno."""
    datos = _service(request).reiniciar(slot)
    return exito({"slot": slot, **datos})
