"""Trajes del armario (`OF`/`TU`/`OAT`/`OA` de js/05-arte.js:154-173).

Cada secta tiene 6 trajes (4 base + 2 premium de `OX`); se desbloquean
por victorias totales (`TU`) y cada uno aplica un efecto de combate al
empezar (`applyOutfit`). El nombre y el efecto se calculan igual que
`OA(k, i)` del monolito; el arte (colores de tela/sombrero) está en
`web/src/arte/figura.ts`, que ya porta `OF`/`OX`.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

#: Victoria mínima para vestir cada traje (`TU` del JS).
UMBRAL_VICTORIAS: tuple[int, ...] = (0, 3, 12, 30, 45, 60)

#: Sufijo de secta para el nombre del efecto (`OAS`).
_SUFIXO_SECTA: dict[str, str] = {
    "esp": "de la Espada",
    "lot": "del Loto",
    "tal": "del Sello",
    "lun": "de la Luna",
    "val": "del Abismo",
    "dra": "del Dragón",
    "mon": "de la Montaña",
    "pil": "del Horno",
    "tru": "del Trueno",
    "bam": "del Bosque",
}

#: Nombre base del tipo de efecto (`OAN`).
_NOMBRE_TIPO: dict[str, str] = {
    "hp": "Cuerpo",
    "sh": "Velo",
    "q": "Despertar",
    "rg": "Savia",
    "at": "Filo",
    "pa": "Furia",
    "ph": "Coraza",
    "fd": "Primer golpe",
}

_TRAJES_BASE: dict[str, tuple[str, ...]] = {
    "esp": ("Túnica del Discípulo", "Armadura de Plata",
            "Vestido del Filo Carmesí", "Manto del Soberano"),
    "lot": ("Túnica de Loto", "Seda de Jade", "Manto Blanco",
            "Atuendo de la Diosa"),
    "tal": ("Túnica de Escriba", "Capa de Sellos", "Hábito Escarlata",
            "Manto del Sello Eterno"),
    "lun": ("Túnica Lunar", "Velo de Plata", "Vestido Nocturno",
            "Manto del Eclipse"),
    "val": ("Hábito Demoníaco", "Armadura de Sangre", "Capa del Abismo",
            "Manto del Señor Demonio"),
    "dra": ("Túnica Dorada", "Escamas Imperiales", "Manto del Dragón",
            "Atuendo Celestial"),
    "mon": ("Túnica de Montaña", "Coraza de Roca", "Capa de Nieve",
            "Armadura del Titán"),
    "pil": ("Túnica de Alquimista", "Delantal de Fuego", "Bata Medicinal",
            "Manto del Inmortal Alquimista"),
    "tru": ("Túnica del Rayo", "Armadura de Tormenta", "Capa Eléctrica",
            "Manto del Dios del Trueno"),
    "bam": ("Túnica de Bambú", "Sombrero del Bosque", "Capa de Hojas",
            "Manto del Bosque Eterno"),
}

_TRAJES_PREMIUM: dict[str, tuple[str, ...]] = {
    "esp": ("Armadura del Alba", "Vestiduras del Inmortal de la Espada"),
    "lot": ("Seda de Primavera", "Manto de la Flor Inmortal"),
    "tal": ("Hábito de Mil Sellos", "Manto del Sello Celestial"),
    "lun": ("Velo de las Mareas", "Atuendo de la Luna Llena"),
    "val": ("Armadura de Obsidiana", "Manto del Rey Demonio"),
    "dra": ("Escamas de Fuego", "Atuendo del Dragón Primordial"),
    "mon": ("Armadura de Granito", "Manto del Corazón de la Montaña"),
    "pil": ("Bata del Horno Eterno", "Manto del Alquimista Celestial"),
    "tru": ("Armadura de Tormenta Violeta", "Atuendo del Rayo Celestial"),
    "bam": ("Capa de Bambú Dorado", "Manto del Bosque Inmortal"),
}

#: Efecto `(tipo, valor)` de cada traje, en el mismo orden (`OAT`).
_EFECTOS: dict[str, tuple[tuple[str, int], ...]] = {
    "esp": (("hp", 2), ("at", 1), ("fd", 3), ("pa", 1), ("at", 2), ("pa", 2)),
    "lot": (("hp", 2), ("rg", 1), ("sh", 1), ("rg", 2), ("sh", 2), ("hp", 5)),
    "tal": (("hp", 2), ("q", 1), ("fd", 2), ("q", 2), ("sh", 1), ("q", 3)),
    "lun": (("hp", 2), ("q", 1), ("sh", 1), ("fd", 3), ("q", 2), ("sh", 2)),
    "val": (("hp", 2), ("fd", 2), ("at", 1), ("fd", 4), ("pa", 1), ("at", 2)),
    "dra": (("hp", 3), ("at", 1), ("pa", 1), ("hp", 5), ("at", 2), ("pa", 2)),
    "mon": (("hp", 3), ("sh", 1), ("ph", 1), ("hp", 5), ("sh", 2), ("ph", 2)),
    "pil": (("hp", 2), ("rg", 1), ("q", 1), ("rg", 2), ("q", 2), ("hp", 5)),
    "tru": (("hp", 2), ("fd", 2), ("at", 1), ("q", 2), ("fd", 4), ("at", 2)),
    "bam": (("hp", 2), ("ph", 1), ("rg", 1), ("hp", 4), ("ph", 2), ("rg", 2)),
}


def descripcion_efecto(tipo: str, valor: int) -> str:
    """Descripción del efecto (`oaD(t, v)` del JS)."""
    return {
        "hp": f"+{valor} vida máxima",
        "sh": f"+{valor} escudo al inicio de cada turno",
        "q": f"+{valor} Qi en tu primer turno",
        "rg": (
            f"ganas {valor} de escudo al inicio de cada turno "
            "(desde el 2º)"
        ),
        "at": (
            f"+{valor} daño a tus técnicas y +{ceil(valor / 2)} ataque "
            "a tus criaturas al entrar"
        ),
        "pa": f"tus criaturas atacan con +{valor} de ataque",
        "ph": f"tus criaturas entran con +{valor} de vida",
        "fd": f"al empezar el combate, daña {valor} al héroe rival",
    }[tipo]


def nombre_efecto(secta: str, indice: int) -> str:
    """Nombre del efecto del traje (`OA(k, i).n` del JS).

    Las repeticiones del mismo tipo se numeran con II/III según cuántas
    veces aparece ese tipo antes (`OAT[k].slice(0, i)`).
    """
    tipos = [t for t, _ in _EFECTOS[secta][:indice]]
    tipo = _EFECTOS[secta][indice][0]
    repeticion = tipos.count(tipo)
    romano = ("", "II", "III")[repeticion]
    sufijo = _SUFIXO_SECTA[secta]
    return f"{_NOMBRE_TIPO[tipo]} {sufijo}{(' ' + romano) if romano else ''}"


@dataclass(frozen=True, slots=True)
class TrajeData:
    """Traje del armario (fila de `OF[k]` con su efecto de `OA`)."""

    indice: int
    nombre: str
    umbral: int
    tipo: str
    valor: int
    efecto: str
    descripcion: str


def _trajes_secta(secta: str) -> tuple[TrajeData, ...]:
    nombres = _TRAJES_BASE[secta] + _TRAJES_PREMIUM[secta]
    return tuple(
        TrajeData(
            indice=indice,
            nombre=nombre,
            umbral=UMBRAL_VICTORIAS[indice],
            tipo=_EFECTOS[secta][indice][0],
            valor=_EFECTOS[secta][indice][1],
            efecto=nombre_efecto(secta, indice),
            descripcion=descripcion_efecto(*_EFECTOS[secta][indice]),
        )
        for indice, nombre in enumerate(nombres)
    )


#: Armario completo: secta → trajes en orden de desbloqueo.
TRAJES: dict[str, tuple[TrajeData, ...]] = {
    secta: _trajes_secta(secta) for secta in _TRAJES_BASE
}


def traje(secta: str, indice: int) -> TrajeData | None:
    """Traje de esa secta e índice, o `None` si no existe."""
    lista = TRAJES.get(secta)
    if lista is None or not 0 <= indice < len(lista):
        return None
    return lista[indice]
