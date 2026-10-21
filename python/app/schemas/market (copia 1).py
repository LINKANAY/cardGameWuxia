"""Schemas de las acciones del mercado (tab `mkt` del monolito).

Cada endpoint de `app.routers.market` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el snapshot actualizado. Los ids
(`'esp'`, `'vit'`…) se conservan literales, como en todo el proyecto.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComprarCartaRequest(BaseModel):
    """Cuerpo de `POST …/mercado/comprar` (`buy(id)` del JS).

    Atributos:
        carta: id de la carta del catálogo (`C`).
    """

    carta: str = Field(min_length=1, max_length=16)


class ComprarMaterialRequest(BaseModel):
    """Cuerpo de `POST …/mercado/comprar-material` (`buyM(k)`).

    Atributos:
        puesto: clave del puesto de mercado (`MK[k]`; la clave `'neu'`
            no tiene lote de materiales).
        confirmado: False pide confirmación (como el `cfOpen` del
            monolito) y devuelve el lote; True ejecuta la compra.
    """

    puesto: str = Field(min_length=2, max_length=8)
    confirmado: bool = False


class VenderMaterialRequest(BaseModel):
    """Cuerpo de `POST …/mercado/vender` (`sellM(m)` del JS).

    Atributos:
        material: `'h'`, `'p'` o `'n'` (clave corta de `mat`).
    """

    material: str = Field(min_length=1, max_length=1)


class ComprarPildoraRequest(BaseModel):
    """Cuerpo de `POST …/mercado/comprar-pildora` (`buyC(k)` del v47).

    Atributos:
        pildora: id en `PILDORAS` que esté en la vitrina
            (`pildoras_en_venta`).
    """

    pildora: str = Field(min_length=1, max_length=16)
