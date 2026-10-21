"""Schemas del Jardín Medicinal (módulo nuevo, sin monolito).

Cada endpoint de `app.routers.jardin` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el estado del jardín. Las validaciones
de negocio (casilla ocupada, reino insuficiente, piedras de más…)
viven en `JardinService`, no aquí, para devolver códigos de error
propios con estado 400.

`indice` va sin acotar en el schema porque el tamaño de la cuadrícula
depende del nivel (4/6/9/12): el rango real lo valida el servicio
contra `len(casillas)`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CasillaRequest(BaseModel):
    """Cuerpo de `POST …/jardin/{cosechar}`.

    Atributos:
        indice: casilla de la cuadrícula (0 en adelante).
    """

    indice: int


class SembrarRequest(CasillaRequest):
    """Cuerpo de `POST …/jardin/sembrar`.

    Atributos:
        indice: casilla destino (vacía).
        planta: id de la semilla (`'hs'`, `'ff'`…; ver `HIERBA`).
    """

    planta: str = Field(min_length=1, max_length=16)


class AcelerarRequest(CasillaRequest):
    """Cuerpo de `POST …/jardin/acelerar`.

    Atributos:
        indice: casilla sembrada.
        piedras: nº de piedras espirituales a gastar; el rango real
            (≥ 1 y ≤ coste de la casilla) lo valida el servicio y
            devuelve envelope 400, no 422.
    """

    piedras: int


class FormacionRequest(BaseModel):
    """Cuerpo de `POST …/jardin/formacion`.

    Atributos:
        identificador: id `fc*` a equipar; None o cadena vacía →
            quitar la formación equipada.
    """

    identificador: str | None = Field(
        default=None, min_length=0, max_length=16
    )
