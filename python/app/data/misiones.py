"""Catálogo de misiones (port de `GQ`, `TH`, `RIV`, `exq`, `missions`).

Fuente: js/06-contenido.js:88-104 (`TH`/`RIV`/`exq`/`missions`) y
js/06-contenido.js:104 (`GQ`). Los contadores de progreso viven en
``Partida.misiones`` (``qs``); las reclamadas en
``Partida.misiones_reclamadas`` (``qd``).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.data.sectas import SECTAS


@dataclass(frozen=True, slots=True)
class MisionData:
    """Una misión del catálogo (entrada de `GQ` o de `missions(k)`).

    Atributos:
        identificador: id estable (`'g1'`, `'esp3'`…).
        nombre: título visible (`n`).
        descripcion: descripción corta (`d`).
        clave: contador de progreso en `qs` (`k`; `'ek.val'` usa
            `qs.ek['val']`).
        meta: valor objetivo (`g`).
        recompensa: objeto `rw` (claves `s`, `h`, `n`, `p`, `tes`,
            `card`, `recipe`, `design`).
    """

    identificador: str
    nombre: str
    descripcion: str
    clave: str
    meta: int
    recompensa: dict


#: `TH` del monolito: clave de secta → (contador, meta, nombre, desc).
_TH: dict[str, tuple[str, int, str, str]] = {
    "esp": ("sp", 20, "Maestro de la Espada", "Juega 20 técnicas de espada"),
    "lot": ("hl", 40, "Mano Sanadora", "Cura 40 de vida con tus cartas"),
    "tal": ("tg", 15, "Sellador de Destinos", "Lanza 15 técnicas con objetivo"),
    "lun": ("eq", 10, "Ladrón de Qi", "Drena el Qi del rival 10 veces"),
    "val": ("sc", 25, "Pacto de Sangre", "Sacrifica 25 de vida"),
    "dra": ("sm", 25, "Domador de Criaturas", "Invoca 25 criaturas"),
    "mon": ("sh", 60, "Muro Inquebrantable", "Gana 60 de escudo con tus cartas"),
    "pil": ("br", 6, "Gran Alquimista", "Elabora 6 píldoras"),
    "tru": ("tt", 15, "Señor de la Tormenta", "Juega 15 técnicas de área"),
    "bam": ("rsm", 12, "Cazador Veloz", "Invoca 12 criaturas con Ímpetu"),
}

#: `RIV` del monolito: secta → secta rival para misiones de eliminación.
_RIV: dict[str, str] = {
    "esp": "val",
    "lot": "val",
    "tal": "esp",
    "lun": "dra",
    "val": "lot",
    "dra": "val",
    "mon": "tru",
    "pil": "val",
    "tru": "mon",
    "bam": "tal",
}

#: `GQ` del monolito (js/06-contenido.js:104), en orden (ojo: el
#: monolito lista g6 antes que g5).
MISIONES_GENERALES: tuple[MisionData, ...] = (
    MisionData(
        "g1", "Primera sangre", "Gana tu primer combate",
        "w", 1, {"h": 2, "p": 2},
    ),
    MisionData(
        "g2", "Veterano", "Gana 15 combates",
        "w", 15, {"p": 10, "n": 3, "card": 3},
    ),
    MisionData(
        "g3", "Cazador de jefes", "Derrota a 3 jefes finales",
        "bs", 3, {"n": 4, "p": 10, "tes": 1},
    ),
    MisionData(
        "g4", "Explorador de mazmorras", "Vence 4 pisos de mazmorra",
        "dg", 4, {"h": 6, "n": 3, "card": 2},
    ),
    MisionData(
        "g6", "Alquimista de batalla",
        "Usa 6 píldoras durante combates",
        "pu", 6, {"n": 3, "p": 6, "card": 2},
    ),
    MisionData(
        "g5", "Emboscador", "Vence a un alquimista errante",
        "am", 1, {"p": 6, "n": 2},
    ),
    MisionData(
        "g7", "Primer trato", "Compra una carta en el mercado",
        "bu", 1, {"s": 12},
    ),
    MisionData(
        "g8", "Cliente fiel", "Compra 5 cartas en el mercado",
        "bu", 5, {"s": 30, "h": 3},
    ),
    MisionData(
        "g9", "Bolsa de piedras",
        "Gana 150 piedras espirituales en combates",
        "ge", 150, {"s": 40, "n": 1},
    ),
    MisionData(
        "g10", "Comerciante",
        "Vende 8 materiales en el puesto General",
        "sv", 8, {"s": 20, "p": 4},
    ),
    MisionData(
        "g11", "Gran inversor",
        "Gasta 300 piedras espirituales en el mercado",
        "ss", 300, {"n": 3, "card": 3},
    ),
    MisionData(
        "g12", "Curtido en batalla", "Gana 30 combates",
        "w", 30, {"n": 4, "p": 12, "card": 3},
    ),
    MisionData(
        "g13", "Leyenda viviente", "Gana 50 combates",
        "w", 50, {"n": 6, "p": 20, "card": 4, "tes": 1},
    ),
    MisionData(
        "g14", "Matajefes", "Derrota a 6 jefes finales",
        "bs", 6, {"n": 6, "p": 15, "tes": 1},
    ),
    MisionData(
        "g15", "Conquistador de mazmorras",
        "Vence 8 pisos de mazmorra",
        "dg", 8, {"h": 8, "n": 4, "card": 3},
    ),
    MisionData(
        "g16", "Cazador de emboscadas",
        "Vence a 3 alquimistas errantes",
        "am", 3, {"p": 12, "n": 3, "card": 2},
    ),
    MisionData(
        "g17", "Alquimista experto", "Elabora 10 píldoras",
        "br", 10, {"n": 3, "p": 8, "card": 2},
    ),
    MisionData(
        "g18", "Botica de campaña",
        "Usa 15 píldoras durante combates",
        "pu", 15, {"n": 4, "p": 10, "card": 3},
    ),
    MisionData(
        "g19", "Ahorro espiritual",
        "Gana 500 piedras espirituales en combates",
        "ge", 500, {"s": 80, "n": 2},
    ),
    MisionData(
        "g20", "Gran mercader",
        "Vende 20 materiales en el puesto General",
        "sv", 20, {"s": 50, "p": 8},
    ),
    MisionData(
        "g21", "Magnate espiritual",
        "Gasta 1000 piedras espirituales en el mercado",
        "ss", 1000, {"n": 5, "card": 4},
    ),
)


def _segundo_rival(clave_secta: str) -> str:
    """`r2` de `exq` (js/06-contenido.js:90): otro rival determinista."""
    otros = [
        x for x in SECTAS if x != clave_secta and x != _RIV[clave_secta]
    ]
    return otros[(ord(clave_secta[0]) + len(clave_secta)) % len(otros)]


def misiones_secta(clave_secta: str) -> tuple[MisionData, ...]:
    """Las 15 misiones de una secta (`missions(k)` del JS).

    Args:
        clave_secta: clave de la secta del jugador (`sect`).

    Returns:
        Tupla con las misiones k+1 … k+15 en orden del monolito.
    """
    contador, meta, nombre, descripcion = _TH[clave_secta]
    rival = _RIV[clave_secta]
    rival2 = _segundo_rival(clave_secta)
    nombre_rival = SECTAS[rival].nombre
    nombre_rival2 = SECTAS[rival2].nombre
    k = clave_secta
    return (
        MisionData(
            f"{k}1", nombre, descripcion,
            contador, meta, {"p": 6, "n": 1},
        ),
        MisionData(
            f"{k}2", "Caza de bestias", "Derrota a 6 enemigos bestia",
            "bk", 6, {"h": 5, "n": 2},
        ),
        MisionData(
            f"{k}3", f"Eliminación: {nombre_rival}",
            f"Derrota a 8 enemigos de la secta {nombre_rival}",
            f"ek.{rival}", 8, {"p": 8, "n": 2, "tes": 1},
        ),
        MisionData(
            f"{k}4", "Armería de la secta",
            "Compra 3 cartas de tu secta en el mercado",
            "bsc", 3, {"s": 25, "card": 2},
        ),
        MisionData(
            f"{k}5", "Ruta de suministros",
            "Compra un material en el puesto de tu secta",
            "bm", 1, {"s": 15, "h": 2},
        ),
        MisionData(
            f"{k}6", f"{nombre} II", f"{descripcion} (x2)",
            contador, meta * 2, {"p": 10, "n": 2, "card": 2},
        ),
        MisionData(
            f"{k}7", f"{nombre} III", f"{descripcion} (x4)",
            contador, meta * 4, {"n": 4, "p": 14, "card": 3},
        ),
        MisionData(
            f"{k}8", "Gran cacería", "Derrota a 15 enemigos bestia",
            "bk", 15, {"h": 8, "n": 3, "card": 2},
        ),
        MisionData(
            f"{k}9", "Señor de las bestias",
            "Derrota a 30 enemigos bestia",
            "bk", 30, {"n": 5, "p": 12, "card": 3},
        ),
        MisionData(
            f"{k}10", f"Eliminación mayor: {nombre_rival}",
            f"Derrota a 16 enemigos de la secta {nombre_rival}",
            f"ek.{rival}", 16, {"p": 12, "n": 3, "tes": 1},
        ),
        MisionData(
            f"{k}11", f"Eliminación: {nombre_rival2}",
            f"Derrota a 8 enemigos de la secta {nombre_rival2}",
            f"ek.{rival2}", 8, {"p": 8, "n": 2, "tes": 1},
        ),
        MisionData(
            f"{k}12", "Gran armería",
            "Compra 8 cartas de tu secta en el mercado",
            "bsc", 8, {"s": 50, "card": 3},
        ),
        MisionData(
            f"{k}13", "Armería legendaria",
            "Compra 15 cartas de tu secta en el mercado",
            "bsc", 15, {"s": 90, "card": 4},
        ),
        MisionData(
            f"{k}14", "Rutas comerciales",
            "Compra 4 materiales en el puesto de tu secta",
            "bm", 4, {"s": 40, "h": 4, "n": 1},
        ),
        MisionData(
            f"{k}15", "Red de suministros",
            "Compra 8 materiales en el puesto de tu secta",
            "bm", 8, {"s": 80, "n": 3},
        ),
    )


def todas_las_misiones(clave_secta: str) -> tuple[MisionData, ...]:
    """Generales + de la secta, en orden (`[...GQ, ...missions(sect)]`)."""
    return MISIONES_GENERALES + misiones_secta(clave_secta)


def buscar_mision(
    clave_secta: str, identificador: str
) -> MisionData | None:
    """Busca una misión por id en el conjunto del jugador o None."""
    for mision in todas_las_misiones(clave_secta):
        if mision.identificador == identificador:
            return mision
    return None


def valor_mision(mision: MisionData, qs: dict) -> int:
    """Progreso actual de una misión (`qv` del JS).

    Args:
        mision: misión a evaluar.
        qs: contadores `Partida.misiones`.

    Returns:
        Valor actual (0 si el contador no existe).
    """
    if "." in mision.clave:
        return int(qs.get("ek", {}).get(mision.clave.split(".", 1)[1], 0))
    return int(qs.get(mision.clave, 0))


def grupo_mision(mision: MisionData) -> str:
    """Grupo de la UI (`missionGroup` del JS).

    Referencia: js/06-contenido.js:118-126. Ojo: en el monolito las
    misiones `'ek.*'` NO entran en el grupo Combate (el `includes`
    compara la clave entera), así que caen en Progreso.
    """
    clave = mision.clave
    if clave == "dg":
        return "Exploración"
    if clave in {"br", "bm"}:
        return "Fabricación"
    if clave in {"w", "bk", "bs", "ek", "pu"}:
        return "Combate"
    return "Progreso"
