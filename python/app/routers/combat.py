"""Endpoints de combate: iniciar y ejecutar un combate activo.

Espejo de `begin`/`play`/`hit`/`act`/`endT` del monolito. El estado
del combate vive en memoria del servicio; la campaña se aplica con
auto-guardado al emitirse eventos (`victoria`/`muerte`/…).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.combat import (
    ActivarRequest,
    AtacarRequest,
    DescartarExcesoRequest,
    ElegirVacioRequest,
    EventoRequest,
    FinTurnoRequest,
    IniciarCombateRequest,
    JugarCartaRequest,
    ReclamarRequest,
    UsarPildoraRequest,
)
from app.schemas.envelope import exito
from app.services.combat_service import CombatService


def _service(request: Request) -> CombatService:
    store = request.app.state.store
    if not hasattr(request.app.state, "combates"):
        request.app.state.combates = {}
    servicio = getattr(request.app.state, "combat_service", None)
    if servicio is None:
        servicio = CombatService(store)
        request.app.state.combat_service = servicio
    return servicio


router = APIRouter(prefix="/api/game/{slot}/combate", tags=["combate"])


@router.get("")
def estado_combate(slot: str, request: Request):
    return exito({"slot": slot, "combate": _service(request).snapshot(slot)})


@router.post("/iniciar")
def iniciar(slot: str, body: IniciarCombateRequest, request: Request):
    resultado = _service(request).iniciar(
        slot, body.enemigo, body.pildoras, body.bolsa
    )
    return exito({"slot": slot, **resultado})


@router.post("/jugar")
def jugar(slot: str, body: JugarCartaRequest, request: Request):
    resultado = _service(request).jugar(
        slot, body.indice, body.objetivo
    )
    return exito({"slot": slot, **resultado})


@router.post("/atacar")
def atacar(slot: str, body: AtacarRequest, request: Request):
    resultado = _service(request).atacar(
        slot, body.atacante, body.objetivo
    )
    return exito({"slot": slot, **resultado})


@router.post("/activar")
def activar(slot: str, body: ActivarRequest, request: Request):
    resultado = _service(request).activar(slot, body.indice)
    return exito({"slot": slot, **resultado})


@router.post("/fin-turno")
def fin_turno(slot: str, body: FinTurnoRequest, request: Request):
    resultado = _service(request).fin_turno(slot, body.forzar)
    return exito({"slot": slot, **resultado})


@router.post("/descartar-exceso")
def descartar_exceso(
    slot: str, body: DescartarExcesoRequest, request: Request
):
    resultado = _service(request).descartar_exceso(slot, body.indice)
    return exito({"slot": slot, **resultado})


@router.post("/descartar-cancelar")
def descartar_cancelar(slot: str, request: Request):
    resultado = _service(request).cancelar_exceso(slot)
    return exito({"slot": slot, **resultado})


@router.post("/elegir-vacio")
def elegir_vacio(slot: str, body: ElegirVacioRequest, request: Request):
    resultado = _service(request).elegir_vacio(slot, body.indice)
    return exito({"slot": slot, **resultado})


@router.post("/cancelar-vacio")
def cancelar_vacio(slot: str, request: Request):
    resultado = _service(request).cancelar_vacio(slot)
    return exito({"slot": slot, **resultado})


@router.post("/evento")
def evento(slot: str, body: EventoRequest, request: Request):
    resultado = _service(request).resolver_evento(slot, body.opcion)
    return exito({"slot": slot, **resultado})


@router.post("/usar-pildora")
def usar_pildora(slot: str, body: UsarPildoraRequest, request: Request):
    resultado = _service(request).usar_pildora(slot, body.pildora)
    return exito({"slot": slot, **resultado})


@router.post("/abandonar")
def abandonar(slot: str, request: Request):
    resultado = _service(request).abandonar(slot)
    return exito({"slot": slot, **resultado})


@router.post("/cerrar")
def cerrar(slot: str, request: Request):
    resultado = _service(request).cerrar(slot)
    return exito({"slot": slot, **resultado})


@router.post("/reclamar")
def reclamar(slot: str, body: ReclamarRequest, request: Request):
    resultado = _service(request).reclamar(slot, body.indice)
    return exito({"slot": slot, **resultado})
