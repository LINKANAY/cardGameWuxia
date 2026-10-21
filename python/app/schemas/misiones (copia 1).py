"""Schemas de las acciones de misiones (tab `mis` del monolito).

Cada endpoint de `app.routers.misiones` recibe uno de estos cuerpos.
Los ids (`'g1'`, `'esp3'`…) se conservan literales, como en todo el
proyecto.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReclamarMisionRequest(BaseModel):
    """Cuerpo de `POST …/misiones/reclamar` (`claimQ(id)` del JS).

    Atributos:
        mision: id de la misión (`'g1'`, `'esp3'`…).
    """

    mision: str = Field(min_length=1, max_length=16)


class SeguirMisionRequest(BaseModel):
    """Cuerpo de `POST …/misiones/seguir` (`missionTrack(id)` del JS).

    Atributos:
        mision: id de la misión a seguir; cadena vacía para dejar de
            seguir (`''`).
    """

    mision: str = Field(max_length=16, default="")
