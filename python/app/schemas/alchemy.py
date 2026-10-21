"""Schemas de las acciones de alquimia (tab `alq` del monolito).

Cada endpoint de `app.routers.alchemy` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el snapshot actualizado. Los ids
(`'vit'`, `'cf'`…) se conservan literales, como en todo el proyecto.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ElaborarRequest(BaseModel):
    """Cuerpo de `POST …/alquimia/elaborar` (`brew(k)` del JS).

    Atributos:
        pildora: id de la píldora en `PILDORAS` (debe tener receta
            aprendida en la partida).
    """

    pildora: str = Field(min_length=1, max_length=16)


class ForjarRequest(BaseModel):
    """Cuerpo de `POST …/alquimia/forjar` (`forge(r)` del JS).

    Atributos:
        rareza: índice 0–5 de la rareza deseada (`RN[r]`).
    """

    rareza: int = Field(ge=0, le=5)


class CartaRequest(BaseModel):
    """Cuerpo de `POST …/alquimia/{fusionar,desmantelar}`.

    Atributos:
        carta: id de carta de la colección (`fuse(id)` / `dis(id)`).
    """

    carta: str = Field(min_length=1, max_length=16)
