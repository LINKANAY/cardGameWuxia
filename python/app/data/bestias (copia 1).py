"""Bestias espirituales enemigas (`EBEAST` en `js/07-campamento.js:94`).

El monolito añade estas criaturas al catálogo `C` con
``{...f, c: 0, t: 'C', lk: 1}`` (reliquia, coste 0). El motor de
combate las instancia con `crear_carta_juego(id)` al montar un
enemigo (`enemyBeast`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BestiaData:
    """Entrada de `EBEAST`.

    Atributos:
        nivel_min: nivel mínimo del enemigo para portarla (`lv`).
        identificador: clave corta en el catálogo (`id`; `'EB1'`…).
        nombre: nombre visible (`n`).
        ataque: ataque base (`A`).
        vida: vida base (`H`).
        impetu: entra lista para atacar (`rs`).
        crece_bonus: +N de ataque al atacar (`gr`).
        provocar: provocar (`tk`).
        ultimo_aliento: (`ul`; ver `UltimoAliento`-like `(tipo, valor)`).
        habilidad_activa: (`ab`; `(coste_qi, tipo, valor, texto)`).
        robar_vida: (`vm`).
        rareza: rareza usada por el catálogo (`r`; no afecta al combate).
        icono: tema de arte (`m`; no afecta al motor).
    """

    nivel_min: int
    identificador: str
    nombre: str
    ataque: int
    vida: int
    impetu: bool = False
    crece_bonus: int | None = None
    provocar: bool = False
    robar_vida: bool = False
    ultimo_aliento: tuple[str, int] | None = None
    habilidad_activa: tuple[int, str, int, str] | None = None
    rareza: int = 1
    icono: str = "fox"


#: `EBEAST` del monolito (orden por nivel_min).
BESTIAS_ESPIRITUALES: tuple[BestiaData, ...] = (
    BestiaData(1, "EB1", "Lobo de Viento", 2, 3, impetu=True),
    BestiaData(3, "EB2", "Garza de Niebla", 3, 4, impetu=True, ultimo_aliento=("d", 2)),
    BestiaData(5, "EB3", "Tigre de Llamas", 4, 5, impetu=True, crece_bonus=1),
    BestiaData(
        7,
        "EB4",
        "Tortuga de Jade",
        3,
        9,
        provocar=True,
        habilidad_activa=(1, "s", 3, "Caparazón 3"),
    ),
    BestiaData(
        8,
        "EB5",
        "Qilin del Trueno",
        5,
        7,
        crece_bonus=1,
        habilidad_activa=(2, "d", 3, "Rayo 3"),
    ),
    BestiaData(
        10,
        "EB6",
        "Dragón de Inundación",
        6,
        11,
        robar_vida=True,
        habilidad_activa=(2, "d", 4, "Marea 4"),
    ),
)

#: Índice rápido id → BestiaData.
BESTIAS_POR_ID: dict[str, BestiaData] = {
    b.identificador: b for b in BESTIAS_ESPIRITUALES
}


@dataclass(frozen=True, slots=True)
class BestiaDomable:
    """Bestia de ayuda domable por nivel (entrada de `BEAST`).

    Una por nivel; se gana al vencer al jefe del nivel (`wins`
    incluye ``i*6+5``). Referencia: js/06-contenido.js:31.

    Atributos:
        identificador: clave corta (`'BS1'`…`'BS8'`).
        nombre: nombre visible (`n`).
        ataque: ataque base (`A`).
        vida: vida base (`H`).
        indice_nivel: índice de nivel cuyo jefe la doma (0–7).
    """

    identificador: str
    nombre: str
    ataque: int
    vida: int
    indice_nivel: int


#: `BEAST` del monolito (js/06-contenido.js:31), en orden.
BESTIAS_DOMADAS: tuple[BestiaDomable, ...] = (
    BestiaDomable("BS1", "Lobo de la Aldea", 2, 3, 0),
    BestiaDomable("BS2", "Grulla Sanadora", 1, 4, 1),
    BestiaDomable("BS3", "Cuervo Demoníaco", 3, 2, 2),
    BestiaDomable("BS4", "Zorro de Cola Plateada", 2, 3, 3),
    BestiaDomable("BS5", "Dragoncito del Rayo", 3, 3, 4),
    BestiaDomable("BS6", "Garza Celestial", 2, 5, 5),
    BestiaDomable("BS7", "Gato de Mil Filos", 4, 3, 6),
    BestiaDomable("BS8", "Fénix Primordial", 5, 5, 7),
)


def bestia_para_enemigo(
    nivel_piso: int,
    dificultad: int,
) -> tuple[BestiaData, int]:
    """Elige la bestia de un enemigo (`beastFor` del JS).

    Referencia: `js/07-campamento.js:102`. El «score» es
    ``li * 6 + d``; el nivel de la bestia se limita a ``[1, 10]`` y se
    toma la última cuya ``lv <= nivel``.

    Args:
        nivel_piso: índice de nivel del enemigo (`li`).
        dificultad: índice de dificultad (`d`).

    Returns:
        Tupla (bestia, nivel efectivo de la bestia).
    """
    score = (nivel_piso or 0) * 6 + (dificultad or 0)
    nivel = max(1, min(10, 1 + score // 5))
    elegida = BESTIAS_ESPIRITUALES[0]
    for bestia in BESTIAS_ESPIRITUALES:
        if bestia.nivel_min <= nivel:
            elegida = bestia
    return elegida, nivel
