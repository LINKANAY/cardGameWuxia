"""Núcleo puro del Jardín Medicinal — tiempos, piedras y botines.

Toda la matemática del jardín vive aquí: nada toca `Partida`, relojes
de sistema ni almacenamiento — el «ahora» siempre entra como
`ahora_ms` (epoch ms) y el azar como `rng` (el contrato de
`Math.random`, igual que en `engine.horno`).

Modelo de una casilla sembrada::

    {"planta": "hs", "siembra": <epoch ms>, "reducido": <ms ya descontados>}

y el tiempo que queda es::

    restante = duración_efectiva(planta, formación) - transcurrido - reducido

La formación equipada descuenta su % **en cada lectura** (al equipar
una mejor, las plantas en curso aceleran al instante); las piedras
espirituales suman ms absolutos en `reducido`, así que sirven con
cualquier formación puesta o quitada.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence

from app.data.hierbas import HIERBAS
from app.data.jardin import (
    CFG,
    FORMACIONES,
    MEJORAS,
    descuento_formacion,
    duracion_base,
    rendimiento_base,
)

#: Callback aleatorio: float en ``[0, 1)`` (`Math.random` del JS).
Rng = Callable[[], float]


def duracion_efectiva(planta: str, formacion: str | None) -> int:
    """Duración total (ms) de una planta con la formación puesta.

    Args:
        planta: id de hierba sembrada.
        formacion: id de `FORMACION` equipada, o None.

    Returns:
        ``ceil(base × (1 − descuento))``; nunca menos de 1 ms.
    """
    base = duracion_base(planta)
    descuento = descuento_formacion(formacion)
    if descuento <= 0:
        return base
    return max(1, math.ceil(base * (1 - descuento)))


def transcurrido_ms(casilla: Mapping, ahora_ms: int) -> int:
    """Ms transcurridos desde la siembra (nunca negativos)."""
    return max(0, int(ahora_ms) - int(casilla.get("siembra", 0)))


def restante_ms(
    casilla: Mapping | None, ahora_ms: int, formacion: str | None
) -> int:
    """Ms que quedan de crecimiento (0 = ya cumplió su tiempo).

    Args:
        casilla: dict de casilla o None (vacía → 0).
        ahora_ms: reloj actual en epoch ms.
        formacion: formación equipada (afecta a las plantas en curso).

    Returns:
        Milisegundos restantes sin bajar de 0.
    """
    if not casilla:
        return 0
    efectiva = duracion_efectiva(casilla["planta"], formacion)
    usado = transcurrido_ms(casilla, ahora_ms)
    reducido = int(casilla.get("reducido", 0))
    return max(0, efectiva - usado - reducido)


def esta_listo(
    casilla: Mapping | None, ahora_ms: int, formacion: str | None
) -> bool:
    """¿La planta puede cosecharse? (resto ≤ umbral de 1 s)."""
    if not casilla:
        return False
    return restante_ms(casilla, ahora_ms, formacion) <= CFG["UMBRAL_LISTO_MS"]


def progreso(
    casilla: Mapping | None, ahora_ms: int, formacion: str | None
) -> float:
    """Fración 0–1 de crecimiento (1 = listo para cosechar)."""
    if not casilla:
        return 0.0
    efectiva = duracion_efectiva(casilla["planta"], formacion)
    if efectiva <= 0:
        return 1.0
    restante = restante_ms(casilla, ahora_ms, formacion)
    return max(0.0, min(1.0, 1 - restante / efectiva))


def coste_max_piedras(
    casilla: Mapping | None, ahora_ms: int, formacion: str | None
) -> int:
    """Piedras necesarias para dejar la planta lista de golpe.

    Cada piedra quita `REDUCCION_PIEDRA` (5 %) del resto, así que el
    coste es ``ceil(log(umbral / restante) / log(0.95))``.

    Args:
        casilla: dict de casilla o None.
        ahora_ms: reloj actual en epoch ms.
        formacion: formación equipada.

    Returns:
        Nº de piedras (0 si ya está lista o no hay casilla).
    """
    if not casilla:
        return 0
    restante = restante_ms(casilla, ahora_ms, formacion)
    umbral = CFG["UMBRAL_LISTO_MS"]
    if restante <= umbral:
        return 0
    factor = 1 - CFG["REDUCCION_PIEDRA"]
    return max(1, math.ceil(math.log(umbral / restante) / math.log(factor)))


def aplicar_piedras(
    casilla: Mapping,
    piedras: int,
    ahora_ms: int,
    formacion: str | None,
) -> dict:
    """Descuenta el tiempo de una planta con piedras espirituales.

    Cada piedra quita 5 % del resto que quede en el momento de usarla
    (acumulable); si el resultado baja del umbral de 1 s, la planta
    queda lista (resto exactamente 0).

    Args:
        casilla: dict de casilla sembrada (no se muta).
        piedras: nº de piedras a gastar (≥ 1).
        ahora_ms: reloj actual en epoch ms.
        formacion: formación equipada al aplicar.

    Returns:
        ``{"reducido": ms acumulados, "restante_ms": resto tras el
        gasto, "gastadas": piedras realmente consumidas}``.

    Raises:
        ValueError: `piedras < 1`.
    """
    if piedras < 1:
        raise ValueError("hay que gastar al menos 1 piedra")
    efectiva = duracion_efectiva(casilla["planta"], formacion)
    usado = transcurrido_ms(casilla, ahora_ms)
    reducido = int(casilla.get("reducido", 0))
    restante = max(0, efectiva - usado - reducido)
    if restante <= 0:
        return {"reducido": reducido, "restante_ms": 0, "gastadas": 0}

    factor = (1 - CFG["REDUCCION_PIEDRA"]) ** piedras
    # Techo para que el ruido de coma flotante no regale (ni robe) ms.
    objetivo = math.ceil(restante * factor)
    if objetivo <= CFG["UMBRAL_LISTO_MS"]:
        # Cumplió (o casi): lo dejamos en 0 para que no haya que
        # regar ni un milisegundo más.
        nuevo_reducido = efectiva - usado
    else:
        nuevo_reducido = reducido + (restante - objetivo)
    nuevo_reducido = max(reducido, min(nuevo_reducido, efectiva - usado))
    restante_nuevo = max(0, efectiva - usado - nuevo_reducido)
    return {
        "reducido": int(nuevo_reducido),
        "restante_ms": int(restante_nuevo),
        "gastadas": piedras,
    }


def rendimiento(planta: str) -> int:
    """Hierbas del Horno que rinde cosechar esa planta.

    Args:
        planta: id de hierba sembrada.

    Returns:
        Nº de hierbas (1–3 según rareza).
    """
    return rendimiento_base(planta)


def desbloqueada(rareza: int, reino: int) -> bool:
    """¿Se puede sembrar esa rareza en el reino actual?

    Args:
        rareza: rareza de la hierba (0–4).
        reino: nivel de reino de cultivo del jugador.

    Returns:
        True si el reino alcanza `REINO_POR_RAREZA[rareza]`.
    """
    return (reino or 0) >= CFG["REINO_POR_RAREZA"].get(rareza, 99)


def siguiente_mejora(nivel: int) -> dict | None:
    """Mejora de cuadrícula que viene después del nivel dado.

    Args:
        nivel: nivel actual del jardín (0–3).

    Returns:
        ``{"nivel", "casillas", "coste", "reino_min"}`` de la siguiente
        mejora, o None si la cuadrícula ya está al máximo (12 casillas).
    """
    indice_nivel = max(0, int(nivel))
    indice = min(indice_nivel + 1, len(MEJORAS) - 1)
    if indice <= indice_nivel:
        return None
    mejora = MEJORAS[indice]
    return {
        "nivel": mejora.nivel,
        "casillas": mejora.casillas,
        "coste": dict(mejora.coste),
        "reino_min": mejora.reino_min,
    }


# --- Botines (semillas y formaciones: boticarios y ascensos) ---------------


def _sortear(pesos: Sequence[float], rng: Rng) -> int:
    """Índice ponderado por `pesos` (mismo estilo que `botin` del horno)."""
    total = sum(pesos)
    resto = rng() * total
    elegido = len(pesos) - 1
    for indice, peso in enumerate(pesos):
        resto -= peso
        if resto <= 0:
            elegido = indice
            break
    return elegido


def botin_boticario(dificultad: int, rng: Rng) -> dict:
    """Semillas, formación y materiales al vencer a un boticario.

    Args:
        dificultad: 0–5 del boticario vencido (`ch.d`).
        rng: callback float en ``[0, 1)``.

    Returns:
        ``{"semillas": {id: n}, "formacion": id|None,
        "materiales": {"h","n","p"}}`` — sin tocar inventarios.
    """
    d = int(dificultad or 0)
    prob = CFG["BOTIN_PROB_SEGUNDA"] + CFG["BOTIN_INCREM_POR_DIF"] * d
    extra = 1 if rng() < prob else 0
    cantidad = CFG["BOTIN_SEMILLAS_MIN"] + min(
        extra, CFG["BOTIN_SEMILLAS_MAX"] - CFG["BOTIN_SEMILLAS_MIN"]
    )

    pesos = [
        hierba.peso
        * (1 + d * CFG["PESO_RAREZA_POR_DIF"] * hierba.rareza)
        for hierba in HIERBAS
    ]
    semillas: dict[str, int] = {}
    for _ in range(cantidad):
        hierba = HIERBAS[_sortear(pesos, rng)]
        semillas[hierba.identificador] = (
            semillas.get(hierba.identificador, 0) + 1
        )

    formacion = None
    if rng() < CFG["BOTIN_PROB_FORMACION"]:
        pesos_formacion = [
            CFG["FORMACIONES_PESO"][formacion.rareza]
            * (1 + d * CFG["PESO_RAREZA_POR_DIF"] * formacion.rareza)
            for formacion in FORMACIONES
        ]
        formacion = FORMACIONES[
            _sortear(pesos_formacion, rng)
        ].identificador

    materiales = {
        "h": CFG["BOTIN_MAT_H_BASE"] + d * CFG["BOTIN_MAT_H_DIF"],
        "p": CFG["BOTIN_MAT_P_BASE"] + (d >> 1),
        "n": 1 if d >= CFG["BOTIN_MAT_N_DIF"] else 0,
    }
    return {
        "semillas": semillas,
        "formacion": formacion,
        "materiales": materiales,
    }


def regalo_ascenso(reino: int, rng: Rng) -> dict:
    """Regalo al subir de reino: semilla recién desbloqueada y formación.

    Args:
        reino: nivel de reino recién alcanzado (ya ascendido).
        rng: callback float en ``[0, 1)``.

    Returns:
        ``{"semilla": id|None, "formacion": id}``. La semilla es None
        si ese reino no desbloquea ninguna rareza nueva; la formación
        es de rareza ``min(4, reino // 3)`` (las hay de todas).
    """
    semilla = None
    raras = [
        rareza
        for rareza, minimo in CFG["REINO_POR_RAREZA"].items()
        if minimo == reino
    ]
    if raras:
        candidatas = [
            hierba.identificador
            for hierba in HIERBAS
            if hierba.rareza in raras
        ]
        if candidatas:
            semilla = candidatas[_sortear([1.0] * len(candidatas), rng)]

    rareza_formacion = min(
        max(CFG["DESCUENTO_POR_RAREZA"]),
        int(reino) // CFG["REGALO_FORMACION_DIVISOR"],
    )
    candidatas_f = [
        formacion.identificador
        for formacion in FORMACIONES
        if formacion.rareza == rareza_formacion
    ]
    formacion = candidatas_f[
        _sortear([1.0] * len(candidatas_f), rng)
    ]
    return {"semilla": semilla, "formacion": formacion}
