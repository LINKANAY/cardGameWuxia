"""Emboscadas tras reclamar la recompensa (`ambRoll` de la v47).

Port puro y testeable de:
- `BOT`/`ambRoll` (js/12-v47-init.js:83-92): sorteo del tipo de
  emboscada al reclamar la carta de una victoria.
- `mkAmb`/`mkBot` (js/06-contenido.js:207 y js/12-v47-init.js:84):
  ficha dinámica del enemigo, construida a partir del recién vencido
  (`ch`) con +1 de dificultad.
- `notifyWin` boticario (js/12-v47-init.js:122-125): contador `qs.bt`
  y píldora de regalo si la receta ya se conocía.

Paridad de orden de los `Math.random()`: cada roll se consume en el
mismo orden que el monolito (puerta → cuota → pozo → índice →
habilidades → nombre → secta → nombre de boticario), de modo que un
RNG con la misma semilla reproduce la misma emboscada.

Reglas de campaña que la emboscada arrastra (ver `campaign.py`):
sin índice en `CH` no hay `first` (no sube reino ni cuenta como jefe),
`!ch.amb` bloquea Talismán de Escape, reliquia y `qs.bs`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace

from app.data.narrativa import (
    MULT_DIFICULTAD,
    VIDA_BASE_NIVEL,
    redondear_js,
)
from app.data.niveles import TEXTO_HABILIDAD_ENEMIGO
from app.data.pildoras import PILDORAS
from app.data.sectas import SECTAS
from app.data.tipos import EnemigoCatalogo
from app.engine.state import Partida

#: Callback aleatorio inyectable (contrato de `Math.random`).
Rng = Callable[[], float]

# --- Ajustes (`BOT` de js/12-v47-init.js:83) --------------------------------

#: Probabilidad base de emboscada tras reclamar (`BOT.chance`).
PROBABILIDAD_BASE = 0.22
#: Bonus de probabilidad por punto de dificultad (`BOT.perDiff`).
PROBABILIDAD_POR_DIFICULTAD = 0.05
#: Cuota de boticario frente a alquimista errante (`BOT.share`).
CUOTA_BOTICARIO = 0.5
#: Probabilidad de píldora de regalo si la receta ya se conocía
#: (`BOT.dropPct`).
PROBABILIDAD_PILDORA = 0.35
#: Si quedan recetas de recuperación sin aprender, probabilidad de que
#: el boticario enseñe una de ellas en vez de una cualquiera (`.8`
#: inline de `ambRoll`, js/12-v47-init.js:89).
PROBABILIDAD_PILDORA_RECUPERACION = 0.8

#: Nombres del alquimista errante (`nm` de `mkAmb`).
NOMBRES_ALQUIMISTA = (
    "Alquimista Errante",
    "Boticario Sombrío",
    "Herborista Enloquecido",
    "Anciano del Caldero",
    "Maestra de Venenos",
)
#: Nombres del boticario (`BOT.names`).
NOMBRES_BOTICARIO = (
    "Boticario Errante",
    "Boticario Sombrío",
    "Herborista Ambulante",
    "Anciano del Caldero",
    "Maestra de Ungüentos",
)

#: Recetas de recuperación de la Cueva de Reclusión (`RCV` de
#: js/12-v47-init.js:59; el flag `o` del JS es `es_recuperacion`).
RECETAS_RECUPERACION: tuple[str, ...] = tuple(
    ident for ident, pildora in PILDORAS.items() if pildora.es_recuperacion
)

_TITULO_ALQUIMISTA = "Emboscada de un alquimista"
_TITULO_BOTICARIO = "Encuentro con un boticario"
_FRASES: dict[str, tuple[str, str, str]] = {
    # (frase_inicio, frase_derrota, nombre_nivel)
    "alquimista": (
        "¿Buscas secretos? Tendrás que quitármelos.",
        "Toma mi receta y úsala con juicio.",
        _TITULO_ALQUIMISTA,
    ),
    "boticario": (
        "Hierbas, humo y un precio. ¿Qué ofreces?",
        "Buen combate. Toma lo que prometí.",
        _TITULO_BOTICARIO,
    ),
}


@dataclass(frozen=True, slots=True)
class Sorteo:
    """Emboscada sorteada (`amb = { bot, o }` del JS).

    Atributos:
        tipo: `'boticario'` o `'alquimista'`.
        receta: id de la píldora que puede enseñar (`rcp`).
    """

    tipo: str
    receta: str

    @property
    def boticario(self) -> bool:
        """True si es un boticario (`amb.bot`)."""
        return self.tipo == "boticario"


def sortear_amboscada(
    aleatorio: Rng,
    *,
    recetas: Mapping[str, int],
    dificultad: int,
    es_mazmorra: bool,
    es_amboscada: bool,
    es_tribulacion: bool = False,
) -> Sorteo | None:
    """Sortea la emboscada al reclamar (`ambRoll`).

    Puerta: no hay emboscada en mazmorra, tras otra emboscada ni en
    tribulación, y la tirada debe caer por debajo de
    ``0.22 + dificultad * 0.05``.

    Args:
        aleatorio: callback float en ``[0, 1)``.
        recetas: recetas aprendidas (`rec`).
        dificultad: 0–5 del enemigo vencido (`ch.d`).
        es_mazmorra: el vencido era de mazmorra (`ch.dg`).
        es_amboscada: el vencido ya era una emboscada (`ch.amb`); no
            se encadenan.
        es_tribulacion: el vencido era una tribulación (`ch.trib`; el
            backend aún no porta ese sistema, queda a False).

    Returns:
        El ``Sorteo`` o None si no hay emboscada.
    """
    if es_mazmorra or es_amboscada or es_tribulacion:
        return None
    umbral = PROBABILIDAD_BASE + dificultad * PROBABILIDAD_POR_DIFICULTAD
    if aleatorio() >= umbral:
        return None
    # `legacy`: recetas sin aprender que no son de recuperación.
    legacy = [
        ident
        for ident, pildora in PILDORAS.items()
        if ident not in recetas and not pildora.es_recuperacion
    ]
    sin_recuperacion = tuple(
        ident for ident in RECETAS_RECUPERACION if ident not in recetas
    )
    if not legacy or aleatorio() < CUOTA_BOTICARIO:
        # Pozo del boticario: recuperaciones sin aprender si quedan
        # (y la tirada cabe), o las tres de siempre.
        if sin_recuperacion and (
            aleatorio() < PROBABILIDAD_PILDORA_RECUPERACION
        ):
            pozo = sin_recuperacion
        else:
            pozo = RECETAS_RECUPERACION
        receta = pozo[int(aleatorio() * len(pozo))]
        return Sorteo(tipo="boticario", receta=receta)
    receta = legacy[int(aleatorio() * len(legacy))]
    return Sorteo(tipo="alquimista", receta=receta)


def construir_enemigo(
    previo: EnemigoCatalogo,
    *,
    receta: str,
    boticario: bool,
    aleatorio: Rng,
) -> EnemigoCatalogo:
    """Ficha dinámica de la emboscada (`mkAmb`/`mkBot`).

    El rival sale de la ficha del recién vencido (`ch`): misma secta
    de nivel (``li``), ``d = min(5, ch.d + 1)``, vida ``B[li] * MU[d]
    * 1.05``, ``cap = min(10, 5 + d)`` y recompensa ``min(5, ch.rw +
    1)``. Sin índice en `CH` (`indice_mazmorra`/`indice_mision` = None),
    lo que desactiva `first`, misiones secundarias y jefatura.

    Args:
        previo: ficha del enemigo vencido (`ch`).
        receta: píldora que puede enseñar (`rcp`).
        boticario: True para `mkBot` (nombre, título y frases propios).
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Ficha nueva con ``es_emboscada`` (y ``es_boticario``) marcados.
    """
    claves_secta = list(SECTAS)
    claves_habilidad = list(TEXTO_HABILIDAD_ENEMIGO)
    dificultad = min(5, previo.dificultad + 1)
    # Orden de los rolls de `mkAmb`: habilidades, nombre, secta y —
    # sólo si es boticario — el nombre de `BOT.names` al final.
    habilidades = [
        claves_habilidad[int(aleatorio() * len(claves_habilidad))]
    ]
    if dificultad >= 3:
        habilidades.append(
            claves_habilidad[int(aleatorio() * len(claves_habilidad))]
        )
    unicas = tuple(dict.fromkeys(habilidades))
    nombre = NOMBRES_ALQUIMISTA[int(aleatorio() * len(NOMBRES_ALQUIMISTA))]
    secta = claves_secta[int(aleatorio() * len(claves_secta))]
    if boticario:
        nombre = NOMBRES_BOTICARIO[int(aleatorio() * len(NOMBRES_BOTICARIO))]
    frase_inicio, frase_derrota, titulo = _FRASES[
        "boticario" if boticario else "alquimista"
    ]
    indice_nivel = previo.indice_nivel
    return replace(
        previo,
        nombre_enemigo=nombre,
        secta=secta,
        habilidades=unicas,
        frase_inicio=frase_inicio,
        frase_derrota=frase_derrota,
        receta=receta,
        nombre_nivel=titulo,
        historia=None,
        indice_nivel=indice_nivel,
        dificultad=dificultad,
        indice_mazmorra=None,
        indice_mision=None,
        fase_mision=None,
        vida=redondear_js(
            VIDA_BASE_NIVEL[indice_nivel]
            * MULT_DIFICULTAD[dificultad]
            * 1.05
        ),
        capacidad=min(10, 5 + dificultad),
        rareza_recompensa=min(5, previo.rareza_recompensa + 1),
        texto_habilidades=". ".join(
            TEXTO_HABILIDAD_ENEMIGO[clave] for clave in unicas
        )
        + ".",
        es_emboscada=True,
        es_boticario=boticario,
    )


def aplicar_boticario(
    partida: Partida,
    enemigo: EnemigoCatalogo,
    *,
    receta_aprendida: str | None,
    aleatorio: Rng,
) -> dict | None:
    """Efectos de vencer a un boticario (`notifyWin`, v47).

    Args:
        partida: partida a mutar (`qs` y `pil`).
        enemigo: ficha vencida (con ``es_boticario``).
        receta_aprendida: receta recién descubierta en este combate
            (``found`` del JS); si la receta es nueva no hay píldora.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        ``{"pildora": id | None}`` si era boticario, o None si no.
    """
    if not enemigo.es_boticario:
        return None
    qs = partida.misiones
    qs["bt"] = qs.get("bt", 0) + 1
    pildora = None
    if (
        not receta_aprendida
        and enemigo.receta
        and aleatorio() < PROBABILIDAD_PILDORA
    ):
        ident = enemigo.receta
        partida.pildoras[ident] = partida.pildoras.get(ident, 0) + 1
        pildora = ident
    return {"pildora": pildora}
