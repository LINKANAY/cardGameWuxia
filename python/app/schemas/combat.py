"""Schemas de las acciones de combate (motor + campaña).

Cada endpoint de `app.routers.combat` recibe uno de estos cuerpos y
devuelve el sobre uniforme con el estado de combate serializado y, si
el combate terminó, el resumen de campaña aplicado.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IniciarCombateRequest(BaseModel):
    """Cuerpo de `POST …/combate/iniciar` (`begin(k)` del JS).

    Atributos:
        enemigo: índice en el catálogo `ENEMIGOS` (`CH`).
        pildoras: ids de píldoras de inicio ya equipadas (`eqp`).
        bolsa: ids de píldoras de combate de la bolsa (`eqpB`).
    """

    enemigo: int = Field(ge=0)
    pildoras: list[str] = Field(default_factory=list)
    bolsa: list[str] = Field(default_factory=list)


class UsarPildoraRequest(BaseModel):
    """Cuerpo de `POST …/combate/usar-pildora` (`usePill`).

    Atributos:
        pildora: id de la píldora de bolsa a usar.
    """

    pildora: str


class EventoRequest(BaseModel):
    """Cuerpo de `POST …/combate/evento` (`evPick`).

    Atributos:
        opcion: índice de la opción del evento de mapa activo.
    """

    opcion: int = Field(ge=0)


class JugarCartaRequest(BaseModel):
    """Cuerpo de `POST …/combate/jugar` (`play`).

    Atributos:
        indice: índice en la mano del jugador.
        objetivo: índice en el tablero rival (None = héroe).
    """

    indice: int = Field(ge=0)
    objetivo: int | None = Field(default=None, ge=0)


class AtacarRequest(BaseModel):
    """Cuerpo de `POST …/combate/atacar` (`hit`).

    Atributos:
        atacante: índice en el tablero del jugador.
        objetivo: índice en el tablero rival, o -1 para el héroe.
    """

    atacante: int = Field(ge=0)
    objetivo: int = -1


class ActivarRequest(BaseModel):
    """Cuerpo de `POST …/combate/activar` (`act`).

    Atributos:
        indice: índice de la criatura en el tablero del jugador.
    """

    indice: int = Field(ge=0)


class FinTurnoRequest(BaseModel):
    """Cuerpo de `POST …/combate/fin-turno` (`endT`).

    Atributos:
        forzar: ignora la confirmación de acciones pendientes.
    """

    forzar: bool = False


class DescartarExcesoRequest(BaseModel):
    """Cuerpo de `POST …/combate/descartar-exceso` (`ED`).

    Atributos:
        indice: índice en la mano a descartar.
    """

    indice: int = Field(ge=0)


class ElegirVacioRequest(BaseModel):
    """Cuerpo de `POST …/combate/elegir-vacio` (`vpick`).

    Atributos:
        indice: índice en el Agujero Negro a recuperar.
    """

    indice: int = Field(ge=0)


class ReclamarRequest(BaseModel):
    """Cuerpo de `POST …/combate/reclamar` (`claim` de js/06-contenido.js:206).

    Atributos:
        indice: índice de la recompensa elegida (0–2).
    """

    indice: int = Field(ge=0)
