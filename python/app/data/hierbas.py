"""Horno de Alquimia — datos y estado por defecto (`HornoAlq` del JS).

Fuente de verdad: `js/11-horno.js` (módulo IIFE completo, 594 líneas).
Este módulo sólo contiene constantes y constructores de estado; toda la
matemática vive en `app.engine.horno`.

Secciones del original:

- `CFG` (líneas 29–66): números de balance (éxito, calidad, curación,
  fallo, botín) con las mismas claves que el JS para poder citarlas.
- `HIERBAS` (81–93): 11 hierbas con éxito/calidad/afinidad/peso.
- `CALIDADES` (99–107), `TIPOS` (113–121), `MENSAJES_FALLO` (123–129).
- `clave_pildora` (278): la clave de inventario de píldoras es
  ``tipo + '.' + calidad`` y para desecho siempre `'waste.fallida'`.

El estado del horno en el monolito vive en `localStorage` con la clave
aparte `xcg_horno`; aquí se serializa dentro de la partida bajo la clave
`xn` (ver `Partida.a_dict` en `app.engine.state`).

Notas de paridad:

- El JS define `TIPOS[*].alUsar` (callback opcional al consumir); hoy
  ninguna píldora lo usa, así que el campo no se portó.
- `INVENTARIO_INICIAL` vive dentro de `CFG` como en el JS; el alias de
  módulo es sólo lectura (copia con `dict(...)` antes de mutar).
"""

from __future__ import annotations

from dataclasses import dataclass

#: Clave de `localStorage` del monolito (`xcg_horno`); aquí es sólo
#: documentación — el backend guarda bajo `xn` dentro de `xcg3`.
CLAVE_LEGADO: str = "xcg_horno"

#: Rareza de la hierba 0..4 (`RAREZA_NOMBRE`/`RAREZA_COLOR` del JS:73-74).
RAREZA_NOMBRE: tuple[str, ...] = (
    "Común",
    "Poco común",
    "Rara",
    "Épica",
    "Legendaria",
)
RAREZA_COLOR: tuple[str, ...] = (
    "#aab8b2",
    "#6cc4a1",
    "#5aa0e8",
    "#b070e0",
    "#e8a23a",
)

#: Números de balance (`CFG` de js/11-horno.js:29-66, literales).
CFG: dict = {
    # --- Probabilidad de éxito (en %) (31-38) ---
    "EXITO_BASE": 30,
    "EXITO_MIN": 5,
    "EXITO_MAX": 95,
    "EXITO_POR_REINO": 1,
    "BONO_ARMONIA": 5,
    "PENA_DISCORDIA": 6,
    "MIN_HIERBAS": 2,
    "MAX_HIERBAS": 4,
    # --- Calidad (41-45) ---
    "UMBRALES_CALIDAD": {"media": 7, "alta": 13, "suprema": 20},
    "BONO_ARMONIA_CALIDAD": 2,
    "PESO_MARGEN": 3,
    "RUIDO_CALIDAD": 4,
    "PROB_PERFECTA": 0.08,
    # --- Curación al consumir una píldora (48-50) ---
    "CURA_POR_CALIDAD": {
        "baja": 12,
        "media": 25,
        "alta": 40,
        "suprema": 65,
    },
    "MULT_PERFECTA": 1.25,
    "CURA_DESECHO_PCT": 1,
    # --- Fallo: reacción del Qi (53-55) ---
    "DANIO_FALLO_PCT": (6, 14),
    "FACTOR_RIESGO": 0.5,
    "PUEDE_MATAR": False,
    # --- Botín de victoria (58-61) ---
    "BOTIN_ACTIVO": True,
    "BOTIN_VICTORIA": (1, 2),
    "BOTIN_BONUS_JEFE": 1,
    "BOTIN_RAREZA_POR_DIF": 0.25,
    # --- Ritmo y arranque (64-65) ---
    "DURACION_MS": 900,
    "INVENTARIO_INICIAL": {
        "hs": 6,
        "rj": 4,
        "hn": 3,
        "ff": 2,
        "ll": 2,
        "rd": 2,
        "gm": 1,
        "lu": 1,
        "hv": 1,
    },
}

#: Inventario con el que arranca el horno (`CFG.INVENTARIO_INICIAL`).
#: Alias del dict de `CFG`: cópialo antes de mutar.
INVENTARIO_INICIAL: dict[str, int] = CFG["INVENTARIO_INICIAL"]


@dataclass(frozen=True, slots=True)
class HierbaData:
    """Hierba del horno (objeto literal de `HIERBAS`, js/11-horno.js:81-93).

    Atributos:
        identificador: id corto de inventario (`id`).
        nombre: nombre visible.
        glifo: carácter chino del icono (`glifo`).
        rareza: índice 0–4 (`rareza`).
        exito: puntos de % que suma al éxito (negativo = más peligrosa).
        calidad: puntos de calidad que aporta.
        afinidad: define el tipo/color de píldora (None = neutra).
        peso: probabilidad relativa de caer como botín (`peso`).
    """

    identificador: str
    nombre: str
    glifo: str
    rareza: int
    exito: int
    calidad: int
    afinidad: str | None
    peso: int


#: Catálogo de hierbas (`HIERBAS` del JS, orden literal).
HIERBAS: tuple[HierbaData, ...] = (
    HierbaData("hs", "Hierba Espiritual", "灵", 0, 6, 1, "heal", 40),
    HierbaData("rj", "Raíz de Jade Verde", "玉", 0, 4, 2, "heal", 30),
    HierbaData("hn", "Hongo de Niebla", "雾", 0, 3, 2, "shield", 24),
    HierbaData("ff", "Fruto de Escarcha", "霜", 1, 5, 3, "ice", 14),
    HierbaData("rd", "Rocío del Amanecer", "露", 1, 4, 3, "draw", 14),
    HierbaData("ll", "Loto Carmesí", "莲", 1, 2, 4, "gold", 12),
    HierbaData("hv", "Hongo Sombrío (veneno)", "毒", 1, -8, 7, None, 10),
    HierbaData("gm", "Ginseng de Mil Años", "参", 2, 10, 4, "heal", 6),
    HierbaData("lu", "Esencia de Luz Lunar", "月", 2, 4, 6, "qi", 6),
    HierbaData("ed", "Escama de Dragón Molida", "龙", 3, 8, 7, "gold", 3),
    HierbaData("nf", "Núcleo de Fénix", "凤", 4, 15, 9, "gold", 1),
)

#: Índice por id (`HIERBA` del JS:94).
HIERBA: dict[str, HierbaData] = {
    hierba.identificador: hierba for hierba in HIERBAS
}


@dataclass(frozen=True, slots=True)
class CalidadData:
    """Calidad de píldora (`CALIDADES[k]`, js/11-horno.js:99-106).

    Atributos:
        nombre: nombre visible.
        clase: clase CSS de rareza (vacío = desecho sin brillo).
    """

    nombre: str
    clase: str


CALIDADES: dict[str, CalidadData] = {
    "fallida": CalidadData("Desecho", ""),
    "baja": CalidadData("Baja", "r1"),
    "media": CalidadData("Media", "r2"),
    "alta": CalidadData("Alta", "r3"),
    "suprema": CalidadData("Suprema", "r4"),
    "perfecta": CalidadData("Suprema ✦ Perfecta", "r5"),
}

#: Orden de calidad para el pintado (`ORDEN_CALIDAD`, línea 107).
ORDEN_CALIDAD: tuple[str, ...] = (
    "perfecta",
    "suprema",
    "alta",
    "media",
    "baja",
    "fallida",
)


@dataclass(frozen=True, slots=True)
class TipoPildora:
    """Tipo de píldora (`TIPOS[k]`, js/11-horno.js:113-121).

    Atributos:
        clase: variante de la clase CSS `.pill` (`clase`).
        nombre: nombre visible ("Restauradora", "Dorada"…).
        mult: multiplica la curación de la calidad (0 = no cura).
    """

    clase: str
    nombre: str
    mult: float


TIPOS: dict[str, TipoPildora] = {
    "heal": TipoPildora("heal", "Restauradora", 1.00),
    "gold": TipoPildora("gold", "Dorada", 0.90),
    "qi": TipoPildora("qi", "de Qi", 0.75),
    "draw": TipoPildora("draw", "de Claridad", 0.75),
    "shield": TipoPildora("shield", "de Coraza", 0.75),
    "ice": TipoPildora("ice", "de Escarcha", 0.75),
    "waste": TipoPildora("waste", "de Desecho", 0),
}

#: Frases de fallo (`MENSAJES_FALLO`, líneas 123-129, orden literal).
MENSAJES_FALLO: tuple[str, ...] = (
    "El Qi del horno se desborda y te golpea el pecho.",
    "Las hierbas se repelen: una onda de energía te desgarra los meridianos.",
    "El caldero ruge, el humo se vuelve negro y la reacción te quema las manos.",
    "La llama se vuelve contra ti: el fuego te muerde el dantian.",
    "Una grieta recorre el horno y el Qi inestable te lanza hacia atrás.",
)


def clave_pildora(tipo: str, calidad: str) -> str:
    """Clave de inventario de una píldora (`claveP` del JS:278).

    Args:
        tipo: clave de `TIPOS` (`'waste'` para desecho).
        calidad: clave de `CALIDADES`.

    Returns:
        ``tipo + '.' + calidad``; para desecho siempre `'waste.fallida'`.
    """
    if tipo == "waste":
        return "waste.fallida"
    return f"{tipo}.{calidad}"


def parsear_pildora(clave: str) -> tuple[str, str] | None:
    """Divide una clave de píldora en (tipo, calidad) (`parseP`, línea 279).

    Args:
        clave: clave tipo `'heal.media'`.

    Returns:
        Tupla (tipo, calidad) o None si la clave no tiene dos partes.
    """
    partes = clave.split(".")
    if len(partes) < 2:
        return None
    return partes[0], partes[1]


def _entero_js(valor) -> int:
    """Trunca hacia cero como el operador `| 0` del JS.

    `None`/no numérico → 0 (el JS produce `NaN | 0 === 0`).
    """
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def nuevo_horno() -> dict:
    """Estado nuevo del horno (`estadoNuevo()` del JS:262-264).

    Returns:
        Dict con `hierbas` (inventario inicial), `pildoras`,
        `refinadas` y `fallos`. Cada llamada devuelve dicts nuevos.
    """
    return {
        "hierbas": dict(CFG["INVENTARIO_INICIAL"]),
        "pildoras": {},
        "refinadas": 0,
        "fallos": 0,
    }


def desde_horno(guardado) -> dict:
    """Reconstruye el estado del horno guardado (`cargar()` del JS:265-275).

    Tolera ausencia, claves desconocidas y tipos raros:

    - Sin `hierbas` utilizables → estado nuevo con el inventario
      inicial (el JS hace `if (d && d.hierbas)` y si no, `estadoNuevo()`).
    - De `hierbas` sólo se conservan ids de `HIERBA` con cantidad > 0
      (mismo filtrado que el JS: `HIERBA[id] && d.hierbas[id] > 0`).
    - `pildoras` se copia tal cual si es dict (el JS no filtra).
    - `refinadas`/`fallos` se truncan con `| 0`.

    Args:
        guardado: valor leído de la clave `xn` (o del `localStorage`).

    Returns:
        Estado normalizado listo para `Partida.horno`.
    """
    if not isinstance(guardado, dict) or not isinstance(
        guardado.get("hierbas"), dict
    ):
        return nuevo_horno()
    hierbas: dict[str, int] = {}
    for identificador, cantidad in guardado["hierbas"].items():
        numero = _entero_js(cantidad)
        if identificador in HIERBA and numero > 0:
            hierbas[identificador] = numero
    pildoras = guardado.get("pildoras")
    return {
        "hierbas": hierbas,
        "pildoras": dict(pildoras) if isinstance(pildoras, dict) else {},
        "refinadas": _entero_js(guardado.get("refinadas")),
        "fallos": _entero_js(guardado.get("fallos")),
    }
