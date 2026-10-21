"""Schemas de las acciones del gacha (Ceremonia de Adivinación).

Cada endpoint de `app.routers.gacha` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el snapshot actualizado.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TirarRequest(BaseModel):
    """Cuerpo de `POST …/gacha/tirar` (`GachaSystem.draw` del JS).

    Atributos:
        pool: clave del pool (`'STANDARD'` o `'PREMIUM'`).
        count: nº de invocaciones (1 o 10; `costPerDraw * count`
            tickets).
    """

    pool: Literal["STANDARD", "PREMIUM"]
    count: int = Field(default=1, ge=1, le=10)
