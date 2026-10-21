"""Núcleo puro del Horno de Alquimia — paridad con `js/11-horno.js`.

Puerto de la sección 3 · NÚCLEO (líneas 131–230) y de la sección 5 ·
ESTADO en su parte pura de botín (líneas 283–307). Nada de esto toca
DOM, `Partida` ni almacenamiento: mismas entradas → mismas salidas.

El azar entra siempre como `rng`: un callable sin argumentos que
devuelve float en ``[0, 1)`` (el contrato de `Math.random`), igual que
en `alchemy_service`/`gacha_service` para poder fijarlo en pruebas.

Referencias de línea del monolito citadas en cada función. El redondeo
usa `redondear_js` (equivalente exacto de `Math.round`, mitad hacia
arriba; el `round()` de Python es bancario y no sirve aquí).
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping, Sequence

from app.data.hierbas import CFG, HIERBA, HIERBAS, MENSAJES_FALLO, TIPOS
from app.data.narrativa import redondear_js

#: Callback aleatorio: float en ``[0, 1)`` (`Math.random` del JS).
Rng = Callable[[], float]


def _clamp(valor: float, minimo: float, maximo: float) -> float:
    """`Math.max(a, Math.min(b, v))` (línea 134)."""
    return max(minimo, min(maximo, valor))


def _lerp(a: float, b: float, t: float) -> float:
    """Interpolación lineal (línea 135)."""
    return a + (b - a) * t


def resumen_combinacion(ids: Sequence[str], reino: int | None) -> dict:
    """Analiza una combinación de hierbas (`resumenCombinacion`, 139-173).

    Los ids pueden repetirse y los desconocidos se ignoran
    (`HIERBA[id]).filter(Boolean)`).

    Args:
        ids: ids de hierbas de la combinación.
        reino: índice de reino de cultivo (`realm`); suma
            `EXITO_POR_REINO` % por nivel.

    Returns:
        Dict con `prob` (clamp 5–95), `puntos` (calidad), `tipo` de
        píldora, `armonia`, `discordia` y `desglose` (lista
        ``[concepto, valor]`` para la UI).
    """
    hierbas = [HIERBA[i] for i in ids if i in HIERBA]
    cuenta: dict[str, int] = {}
    voto: dict[str, int] = {}
    orden: list[str] = []
    suma_exito = 0
    puntos = 0

    for hierba in hierbas:
        suma_exito += hierba.exito
        puntos += hierba.calidad
        if hierba.afinidad:
            clave = hierba.afinidad
            cuenta[clave] = cuenta.get(clave, 0) + 1
            # la hierba potente "vota" más
            voto[clave] = voto.get(clave, 0) + hierba.calidad
            if clave not in orden:
                orden.append(clave)

    exito = CFG["EXITO_BASE"] + suma_exito
    desglose: list[list] = [
        ["Base", CFG["EXITO_BASE"]],
        ["Hierbas", suma_exito],
    ]

    armonia = any(n >= 2 for n in cuenta.values())
    discordia = len(orden) >= 3
    if armonia:
        exito += CFG["BONO_ARMONIA"]
        puntos += CFG["BONO_ARMONIA_CALIDAD"]
        desglose.append(["Armonía", CFG["BONO_ARMONIA"]])
    if discordia:
        exito -= CFG["PENA_DISCORDIA"]
        desglose.append(["Discordia", -CFG["PENA_DISCORDIA"]])

    bonus_reino = (reino or 0) * CFG["EXITO_POR_REINO"]
    if bonus_reino:
        exito += bonus_reino
        desglose.append(["Reino", bonus_reino])

    # Tipo de píldora = afinidad con más votos (empate: la primera).
    # Sin votos → restauradora.
    tipo = "heal"
    mejor = -1
    for afinidad in orden:
        if voto[afinidad] > mejor:
            mejor = voto[afinidad]
            tipo = afinidad

    return {
        "prob": int(
            _clamp(
                redondear_js(exito),
                CFG["EXITO_MIN"],
                CFG["EXITO_MAX"],
            )
        ),
        "puntos": puntos,
        "tipo": tipo,
        "armonia": armonia,
        "discordia": discordia,
        "desglose": desglose,
    }


def clasificar(puntos: float) -> str:
    """Puntos de calidad → rango (`clasificar`, línea 176-179)."""
    umbrales = CFG["UMBRALES_CALIDAD"]
    if puntos >= umbrales["suprema"]:
        return "suprema"
    if puntos >= umbrales["alta"]:
        return "alta"
    if puntos >= umbrales["media"]:
        return "media"
    return "baja"


def rango_calidad(puntos: float) -> list[str]:
    """Rango de calidades posibles, para la vista previa (182-184).

    Args:
        puntos: calidad media estimada de la combinación.

    Returns:
        ``[rango_mínimo, rango_máximo]`` aplicando el ruido ±RUIDO y el
        margen PESO_MARGEN de la tirada.
    """
    return [
        clasificar(puntos - CFG["RUIDO_CALIDAD"]),
        clasificar(puntos + CFG["RUIDO_CALIDAD"] + CFG["PESO_MARGEN"]),
    ]


def rango_danio(prob: float, max_hp: float) -> tuple[int, int]:
    """Daño mínimo y máximo si el refinamiento falla (`rangoDanio`, 187-191).

    Args:
        prob: probabilidad de éxito en % (0–100).
        max_hp: vida máxima del héroe.

    Returns:
        Tupla (mínimo, máximos) con suelo 1 (`PUEDE_MATAR = false`).
    """
    mult = 1 + (1 - prob / 100) * CFG["FACTOR_RIESGO"]
    bajo, alto = CFG["DANIO_FALLO_PCT"]
    return (
        max(1, redondear_js(max_hp * bajo / 100 * mult)),
        max(1, redondear_js(max_hp * alto / 100 * mult)),
    )


def cura_pct(pildora: Mapping[str, str]) -> float:
    """% de vida máxima que cura una píldora (`curaPct`, 194-200).

    Args:
        pildora: dict con `tipo` (clave de `TIPOS`) y `calidad`
            (clave de `CALIDADES`).

    Returns:
        Porcentaje con un decimal (la Perfecta cura 65 × 1.25 ≈ 81 %).
        Desecho (`waste`) → `CURA_DESECHO_PCT` (1 %).
    """
    tipo = pildora.get("tipo")
    calidad = pildora.get("calidad")
    if tipo == "waste":
        return CFG["CURA_DESECHO_PCT"]
    perfecta = calidad == "perfecta"
    base = CFG["CURA_POR_CALIDAD"].get(
        "suprema" if perfecta else calidad, 0
    ) or 0
    tipo_dato = TIPOS.get(tipo) or TIPOS["heal"]
    factor = CFG["MULT_PERFECTA"] if perfecta else 1
    return redondear_js(base * factor * tipo_dato.mult * 10) / 10


def refinar(
    ids: Sequence[str],
    rng: Rng | None = None,
    ctx: Mapping | None = None,
) -> dict:
    """★ El refinamiento: una sola tirada decide éxito/fracaso (206-230).

    Args:
        ids: hierbas del horno (se consumen fuera, en el servicio).
        rng: callback float en ``[0, 1)``; por defecto `random.random`
            (equivale a `Math.random` del JS).
        ctx: `{"reino": int, "maxHp": int}` — sin `maxHp` el daño usa
            el 30 del JS (`ctx.maxHp || 30`).

    Returns:
        Éxito: ``{exito, prob, tirada, puntos, pildora:{tipo,calidad}}``.
        Fracaso: ``{exito, prob, tirada, danio, mensaje, pildora:{tipo:
        'waste', calidad: 'fallida'}}``.
    """
    if rng is None:
        rng = random.random
    contexto = ctx or {}
    resumen = resumen_combinacion(ids, contexto.get("reino"))
    tirada = rng() * 100  # 0..100
    exito = tirada < resumen["prob"]

    if not exito:
        # ── FRACASO: daño por inestabilidad + píldora de desecho ──
        bajo, alto = CFG["DANIO_FALLO_PCT"]
        pct = _lerp(bajo, alto, rng())
        mult = 1 + (1 - resumen["prob"] / 100) * CFG["FACTOR_RIESGO"]
        max_hp = contexto.get("maxHp") or 30
        danio = max(1, redondear_js(max_hp * pct / 100 * mult))
        mensaje = MENSAJES_FALLO[math.floor(rng() * len(MENSAJES_FALLO))]
        return {
            "exito": False,
            "prob": resumen["prob"],
            "tirada": tirada,
            "danio": danio,
            "mensaje": mensaje,
            "pildora": {"tipo": "waste", "calidad": "fallida"},
        }

    # ── ÉXITO: materiales + margen de la tirada + suerte ──
    prob = resumen["prob"]
    margen = (prob - tirada) / prob  # 0 (justo) … 1 (tirada perfecta)
    ruido = (rng() + rng() - 1) * CFG["RUIDO_CALIDAD"]  # triangular −R..R
    puntos = resumen["puntos"] + margen * CFG["PESO_MARGEN"] + ruido
    calidad = clasificar(puntos)
    if calidad == "suprema" and rng() < CFG["PROB_PERFECTA"]:
        calidad = "perfecta"
    return {
        "exito": True,
        "prob": prob,
        "tirada": tirada,
        "puntos": puntos,
        "pildora": {"tipo": resumen["tipo"], "calidad": calidad},
    }


# --- Botín (sección 5 · ESTADO, funciones puras de `botin`/`botinCombate`) --


def _peso_botin(hierba, dificultad: int) -> float:
    """Peso ponderado del botín (`w = h.peso * (1 + dif * 0.25 * rareza)`)."""
    return hierba.peso * (
        1
        + (dificultad or 0) * CFG["BOTIN_RAREZA_POR_DIF"] * hierba.rareza
    )


def botin(n: int, rng: Rng, dificultad: int = 0) -> dict[str, int]:
    """Botín aleatorio ponderado por `peso` (`botin(n, rng, dif)`, 290-300).

    Args:
        n: nº de hierbas a sortear (0 → sortea 1, como `n || 1` del JS).
        rng: callback float en ``[0, 1)``.
        dificultad: 0–5; sube el peso de las hierbas raras.

    Returns:
        Dict id → cantidad obtenida (sin tocar inventarios).
    """
    pesos = [_peso_botin(h, dificultad) for h in HIERBAS]
    total = sum(pesos)
    conseguido: dict[str, int] = {}
    for _ in range(n or 1):
        resto = rng() * total
        elegida = HIERBAS[0]
        for hierba, peso in zip(HIERBAS, pesos, strict=True):
            resto -= peso
            if resto <= 0:
                elegida = hierba
                break
        identificador = elegida.identificador
        conseguido[identificador] = conseguido.get(identificador, 0) + 1
    return conseguido


def botin_combate(
    dificultad: int, rng: Rng, es_jefe: bool = False
) -> dict[str, int]:
    """Botín de una victoria (`botinCombate(dif, rng)`, 302-307).

    Args:
        dificultad: dificultad del enemigo vencido (`ch.d`, 0–5).
        rng: callback float en ``[0, 1)``.
        es_jefe: jefe reconocido por el llamador. En el monolito el
            bonus sólo depende de ``dif >= 4`` (4–5 son los jefes);
            aquí se honra también este flag explícito.

    Returns:
        Dict id → cantidad (`{id: n}` del JS).
    """
    bajo, alto = CFG["BOTIN_VICTORIA"]
    bonus = (
        CFG["BOTIN_BONUS_JEFE"]
        if (dificultad >= 4 or es_jefe)
        else 0
    )
    cantidad = bajo + math.floor(rng() * (alto - bajo + 1)) + bonus
    return botin(cantidad, rng, dificultad)
