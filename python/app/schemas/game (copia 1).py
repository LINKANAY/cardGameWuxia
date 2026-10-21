"""Schemas de partida (Fase 0: mínimos; crecen en Fase 1)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NewGameRequest(BaseModel):
    slot: str = Field(default="default", min_length=1, max_length=64)


class ConfirmarSectaRequest(BaseModel):
    """Elección de secta en la puerta (`confirmS` del JS).

    Atributos:
        secta: clave de la secta (`'esp'`, `'lot'`…), la del catálogo.
    """

    secta: str = Field(min_length=1, max_length=16)


class SlotResumen(BaseModel):
    """Resumen de un slot guardado para la puerta de selección.

    Los campos describen el snapshot `xcg3` sin exponer sus claves
    crudas: se leen con `datos.get("realm")` etc. en `GameService`.

    Atributos:
        slot: nombre del slot (clave del archivo de guardado).
        nivel_reino: índice en REINOS (`realm`).
        secta: secta de la partida (`sect`).
        victorias: nº de victorias acumuladas (`len(wins)`).
    """

    slot: str
    nivel_reino: int
    secta: str
    victorias: int
