"""Schemas de las acciones de mazos (tab `dk` del monolito).

Cada endpoint de `app.routers.decks` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el snapshot actualizado. Los índices de
mazo (`mza`/`mzs[i]`) son enteros; `-1` significa «mazo automático».
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CrearMazoRequest(BaseModel):
    """Cuerpo de `POST …/mazos` (`dNew(a)` del JS).

    Atributos:
        desde_automatico: si es True, el mazo nuevo empieza con las
            cuentas del mazo automático (`deck(sect, true)`); si no,
            vacío.
    """

    desde_automatico: bool = False


class IndiceMazoRequest(BaseModel):
    """Cuerpo de `POST …/mazos/{usar,duplicar,eliminar}`.

    Atributos:
        indice: posición en `mazos` (`mzs[i]`).
    """

    indice: int = Field(ge=0)


class UsarMazoRequest(BaseModel):
    """Cuerpo de `POST …/mazos/usar` (`dUse(i)` del JS).

    Atributos:
        indice: posición en `mazos`, o -1 para el mazo automático.
    """

    indice: int = Field(ge=-1)


class RenombrarMazoRequest(BaseModel):
    """Cuerpo de `POST …/mazos/{indice}/renombrar` (`dRen(v)`).

    Atributos:
        nombre: nombre nuevo (se recorta a 22 caracteres).
    """

    nombre: str = Field(min_length=1, max_length=64)


class CartaEnMazoRequest(BaseModel):
    """Cuerpo de `POST …/mazos/{indice}/{anadir,quitar}` y desequipar.

    Atributos:
        carta: id de carta del catálogo (`dAdd(id)`/`dRm(id)`/`dUneq`).
    """

    carta: str = Field(min_length=1, max_length=16)
