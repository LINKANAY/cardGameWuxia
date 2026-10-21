"""Schemas de las acciones de equipo y trajes (tabs `eqp`/`trj`).

Cada endpoint de `app.routers.equipo` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el snapshot actualizado. Los ids
(`'G1'`, `'BS1'`, `'esp'`…) se conservan literales, como en todo el
proyecto.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PiezaRequest(BaseModel):
    """Cuerpo de `POST …/equipo/{forjar,equipar}` (`forgeG`/`wearG`).

    Atributos:
        pieza: id de la pieza del catálogo (`G1`…`G17`).
    """

    pieza: str = Field(min_length=1, max_length=8)


class BestiaRequest(BaseModel):
    """Cuerpo de `POST …/equipo/bestia` (`eqB(id)` del JS).

    Atributos:
        bestia: id de la bestia domable (`BS1`…`BS8`); `None`
            retira la bestia equipada.
    """

    bestia: str | None = Field(default=None, min_length=1, max_length=8)


class TrajeRequest(BaseModel):
    """Cuerpo de `POST …/traje/vestir` (`wear(k, i)` del JS).

    Atributos:
        secta: secta del traje; debe ser la del jugador.
        indice: índice del traje en su armario (0–5).
    """

    secta: str = Field(min_length=1, max_length=8)
    indice: int = Field(ge=0)
