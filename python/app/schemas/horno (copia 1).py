"""Schemas del Horno de Alquimia (`HornoAlq` de `js/11-horno.js`).

Cada endpoint de `app.routers.horno` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el estado del horno. Las validaciones
de negocio (mínimo 2 hierbas, material insuficiente…) viven en
`HornoService`, no aquí, para poder devolver códigos de error propios.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HierbasRequest(BaseModel):
    """Cuerpo de `POST …/horno/{resumen,refinar}` (`ids` de la UI).

    Atributos:
        ids: ids de hierbas de la combinación; se pueden repetir (el
            orden es el de los slots del modal del monolito).
    """

    ids: list[str]


class UsarPildoraRequest(BaseModel):
    """Cuerpo de `POST …/horno/usar` (`data-pill` del JS).

    Atributos:
        clave: clave de inventario de píldora (`'heal.media'`,
            `'waste.fallida'`…; ver `clave_pildora`).
    """

    clave: str = Field(min_length=1, max_length=64)
