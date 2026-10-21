"""Datos del gacha — paridad con `TICKET_TYPES`/`GACHA_POOLS`/`RARITY_INFO`.

Fuente: `js/14-gacha.js:6-47`. El sistema es determinista salvo el
azar inyectado (el backend usa `GeneradorAleatorio` con semilla de
tiempo); no hay rotación de banners ni multiplicadores ocultos.

Los pools usan tickets distintos (común/premium); la piedad se guarda
por pool en `gp` (`standard_pity`/`premium_pity`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TipoTicket:
    """Reliquia resonante que se consume al invocar (`TICKET_TYPES`).

    Atributos:
        identificador: clave de inventario (`ticket_common`/
            `ticket_premium`; la usa `gt`).
        nombre: nombre visible.
        descripcion: lore de la reliquia.
        icono: emoji del monolito.
    """

    identificador: str
    nombre: str
    descripcion: str
    icono: str


@dataclass(frozen=True, slots=True)
class Probabilidades:
    """Distribución de rarezas de un pool (suma 100).

    Atributos:
        common: % de Común.
        rare: % de Raro.
        epic: % de Épico.
        legendary: % de Legendario.
    """

    common: float
    rare: float
    epic: float
    legendary: float


@dataclass(frozen=True, slots=True)
class SistemaPiedad:
    """Garantías de un pool (`pitySystem` del JS).

    Atributos:
        garantizado_raro_tras: declarado en el JS pero no usado por
            `draw` (sólo se usa el épic). Se conserva por paridad.
        garantizado_epico_tras: tiradas sin épico/legendario tras las
            que el siguiente resultado es Épico garantizado.
        clave: clave del contador en `gp` (`standard_pity`/
            `premium_pity`).
    """

    garantizado_raro_tras: int
    garantizado_epico_tras: int
    clave: str


@dataclass(frozen=True, slots=True)
class PoolGacha:
    """Pool de invocación (`GACHA_POOLS[poolKey]`).

    Atributos:
        clave: clave del pool en la API (`'STANDARD'`/`'PREMIUM'`).
        identificador: id largo (`pool_standard`/`pool_premium`).
        nombre: nombre visible del pool.
        descripcion: lore del pool.
        tipo_ticket: id del ticket que consume (`ticketType`).
        coste_por_tirada: tickets por invocación (`costPerDraw`; 1).
        probabilidades: distribución por rareza.
        piedad: garantías del pool.
    """

    clave: str
    identificador: str
    nombre: str
    descripcion: str
    tipo_ticket: str
    coste_por_tirada: int
    probabilidades: Probabilidades
    piedad: SistemaPiedad


@dataclass(frozen=True, slots=True)
class InfoRareza:
    """Metadatos visuales de una rareza de gacha (`RARITY_INFO`).

    Atributos:
        clave: `'common'`/`'rare'`/`'epic'`/`'legendary'`.
        nombre: nombre visible.
        color: color hex del monolito.
        rareza_rn: rareza del catálogo de cartas equivalente (`rn`).
    """

    clave: str
    nombre: str
    color: str
    rareza_rn: int


#: Tickets de invocación (`TICKET_TYPES` de `js/14-gacha.js:6-19`).
TICKETS: dict[str, TipoTicket] = {
    "ticket_common": TipoTicket(
        "ticket_common",
        "Fragmento de Alma Antigua",
        "Un residual de intención cultivado pacientemente. Al "
        "concentrarse en él, permite escuchar los susurros más "
        "débiles del Sendero.",
        "🧿",
    ),
    "ticket_premium": TipoTicket(
        "ticket_premium",
        "Lágrima de Dragón Ancestral",
        "Una reliquia de poder concentrado, formada donde la "
        "voluntad de un ser legendario trascendió. Sintoniza con "
        "Frecuencias del Sendero más profundas.",
        "💎",
    ),
}

#: Distribución y piedad de cada pool (`GACHA_POOLS` de
#: `js/14-gacha.js:21-40`).
POOLS: dict[str, PoolGacha] = {
    "STANDARD": PoolGacha(
        "STANDARD",
        "pool_standard",
        "Ecos Ancestrales",
        "Invocación general a los recuerdos dispersos en el Sendero. "
        "Aquí yacen conocimientos básicos, esencias menores y "
        "fragmentos de memorias comunes.",
        "ticket_common",
        1,
        Probabilidades(
            common=70, rare=25, epic=4.5, legendary=0.5
        ),
        SistemaPiedad(
            garantizado_raro_tras=10,
            garantizado_epico_tras=50,
            clave="standard_pity",
        ),
    ),
    "PREMIUM": PoolGacha(
        "PREMIUM",
        "pool_premium",
        "Velo del Destino",
        "Sintoniza con una frecuencia específica del Sendero. Las "
        "probabilidades de encontrar Ecos raros o legendarios son "
        "mayores.",
        "ticket_premium",
        1,
        Probabilidades(
            common=50, rare=35, epic=12, legendary=3
        ),
        SistemaPiedad(
            garantizado_raro_tras=5,
            garantizado_epico_tras=30,
            clave="premium_pity",
        ),
    ),
}

#: Rarezas del gacha (`RARITY_INFO` de `js/14-gacha.js:42-47`).
RAREZAS_GACHA: dict[str, InfoRareza] = {
    "common": InfoRareza("common", "Común", "#6B7280", 0),
    "rare": InfoRareza("rare", "Raro", "#3B82F6", 1),
    "epic": InfoRareza("epic", "Épico", "#8B5CF6", 2),
    "legendary": InfoRareza("legendary", "Legendario", "#F59E0B", 3),
}

#: Mapa rareza de gacha → rareza mínima del catálogo que se sortea
#: (`rnMap` de `generateReward`, `js/14-gacha.js:135`).
RAREZA_OBJETIVO: dict[str, int] = {
    "common": 0,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

#: Polvo de jade/esencia otorgado cuando no sale carta (`generateReward`,
#: `js/14-gacha.js:152`).
CANTIDAD_POLVO: dict[str, int] = {
    "legendary": 50,
    "epic": 20,
}

#: Probabilidad de que la tirada suelta carta en vez de polvo
#: (`Math.random() < 0.7` de `js/14-gacha.js:141`).
PROBABILIDAD_CARTA = 0.7
