"""Catálogo de equipo de la Herrería (`GEAR` de js/06-contenido.js:47-53).

Puerto literal de las 17 piezas del monolito: cada pieza ocupa un
hueco (`slot`), da bonos de Ataque/Qi (o revivir, en los artefactos)
y se forja pagando materiales. El desbloqueo (`u`) es un índice de
victoria de campaña (`wins`): `null` = siempre disponible.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.data.tipos import Material

#: Huecos de equipo en orden de la UI (`SLOTS` del JS: los tres
#: primeros van en la columna izquierda del panel, el resto a la
#: derecha).
SLOTS: tuple[str, ...] = (
    "cabeza",
    "cuerpo",
    "guantes",
    "botas",
    "reliquia",
    "artefacto",
)

#: Nombre legible de cada hueco (`SLN` de js/08-efectos.js:104).
SLOT_NOMBRE: dict[str, str] = {
    "cabeza": "Cabeza",
    "cuerpo": "Cuerpo",
    "guantes": "Guantes",
    "botas": "Botas",
    "reliquia": "Reliquia",
    "artefacto": "Artefacto",
}

#: Icono SVG del hueco (`SLI` de js/08-efectos.js:103; viewBox 24×24).
SLOT_ICONO: dict[str, str] = {
    "cabeza": '<path d="M5 20V12a7 7 0 0 1 14 0v8Z"/>',
    "cuerpo": '<path d="M6 4h12l3 5-3 2v9H6v-9L3 9Z"/>',
    "guantes": (
        '<path d="M7 21V11L5 8l2-1 2 3V4h2v7V3h2v8V5h2v8V8h2v8l-3 5Z"/>'
    ),
    "botas": '<path d="M8 3h6v9l6 3v5H8Z"/>',
    "reliquia": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/>',
    "artefacto": (
        '<path d="M12 2l3 7 7 1-5 5 1 7-6-4-6 4 1-7-5-5 7-1Z"/>'
    ),
}


@dataclass(frozen=True, slots=True)
class PiezaData:
    """Pieza de equipo (fila del `GEAR` del monolito).

    Attributes:
        identificador: id corto (`G1`…`G17`; también es la clave de
            guardado en `gr`/`eq`/`du`).
        nombre: nombre visible.
        slot: hueco que ocupa (clave de `SLOTS`).
        ataque: bono `a` (suma al ataque, tope +4 en equipo).
        qi: bono `q` (suma Qi máximo y Qi inicial, tope +4).
        coste: precio de forja en materiales (orden como el JS, que
            fija el texto de `cs`).
        desbloqueo: índice de victoria que lo desbloquea (`u`); `None`
            = sin bloqueo.
        revive: vida con la que revivir si es artefacto (`rv`).
        usos: cargas iniciales del artefacto (`du`).
        secta: secta con la que se identifica la pieza (`SC`).
    """

    identificador: str
    nombre: str
    slot: str
    ataque: int
    qi: int
    coste: dict[Material, int]
    desbloqueo: int | None
    revive: int | None = None
    usos: int | None = None
    secta: str = "neu"


GEAR: tuple[PiezaData, ...] = (
    # --- cabeza ---------------------------------------------------------
    PiezaData("G1", "Diadema de Jade", "cabeza", 0, 1,
              {Material.POLVO_JADE: 3, Material.HIERBAS: 2}, None,
              secta="lot"),
    PiezaData("G2", "Casco del Dragón", "cabeza", 1, 1,
              {Material.POLVO_JADE: 6, Material.NUCLEOS: 2}, 17,
              secta="dra"),
    PiezaData("G3", "Corona Celestial", "cabeza", 2, 2,
              {Material.POLVO_JADE: 12, Material.NUCLEOS: 5}, 35,
              secta="dra"),
    # --- cuerpo ---------------------------------------------------------
    PiezaData("G4", "Túnica Reforzada", "cuerpo", 1, 0,
              {Material.POLVO_JADE: 3, Material.HIERBAS: 2}, None,
              secta="mon"),
    PiezaData("G5", "Armadura de Escamas", "cuerpo", 2, 1,
              {Material.POLVO_JADE: 8, Material.NUCLEOS: 3}, 17,
              secta="dra"),
    PiezaData("G6", "Armadura del Inmortal", "cuerpo", 3, 1,
              {Material.POLVO_JADE: 16, Material.NUCLEOS: 6}, 35,
              secta="neu"),
    # --- reliquia -------------------------------------------------------
    PiezaData("G7", "Brazalete de Qi", "reliquia", 0, 1,
              {Material.HIERBAS: 3, Material.POLVO_JADE: 2}, None,
              secta="pil"),
    PiezaData("G8", "Anillo del Trueno", "reliquia", 2, 0,
              {Material.POLVO_JADE: 6, Material.NUCLEOS: 2}, 17,
              secta="tru"),
    PiezaData("G9", "Talismán del Dao", "reliquia", 1, 2,
              {Material.POLVO_JADE: 12, Material.NUCLEOS: 5}, 35,
              secta="lun"),
    # --- artefacto (revive con usos) ------------------------------------
    PiezaData("G10", "Campana del Alma", "artefacto", 0, 0,
              {Material.POLVO_JADE: 14, Material.NUCLEOS: 6}, 23,
              revive=10, usos=3, secta="lun"),
    PiezaData("G11", "Espejo del Destino", "artefacto", 0, 0,
              {Material.POLVO_JADE: 22, Material.NUCLEOS: 10}, 41,
              revive=18, usos=2, secta="lun"),
    # --- guantes --------------------------------------------------------
    PiezaData("G12", "Guantes de Cuero", "guantes", 1, 0,
              {Material.HIERBAS: 3, Material.POLVO_JADE: 2}, None,
              secta="esp"),
    PiezaData("G13", "Guanteletes de Escamas", "guantes", 2, 0,
              {Material.POLVO_JADE: 6, Material.NUCLEOS: 2}, 17,
              secta="dra"),
    PiezaData("G14", "Manoplas del Dragón", "guantes", 2, 1,
              {Material.POLVO_JADE: 12, Material.NUCLEOS: 5}, 35,
              secta="dra"),
    # --- botas ----------------------------------------------------------
    PiezaData("G15", "Botas de Tela", "botas", 0, 1,
              {Material.HIERBAS: 3, Material.POLVO_JADE: 2}, None,
              secta="lot"),
    PiezaData("G16", "Botas del Viento", "botas", 1, 1,
              {Material.POLVO_JADE: 6, Material.NUCLEOS: 2}, 17,
              secta="lun"),
    PiezaData("G17", "Botas del Inmortal", "botas", 1, 2,
              {Material.POLVO_JADE: 12, Material.NUCLEOS: 5}, 35,
              secta="lun"),
)

#: Índice por id (`GEAR.find(x => x.id == …)` del JS).
PIEZAS: dict[str, PiezaData] = {p.identificador: p for p in GEAR}

#: Tabla de equipo enemigo por fila (`R` de `enemyGear()` en
#: js/02-motor.js:54): cada fila se resuelve con la columna
#: ``min(2, score // 16)`` y aporta sus bonos al enemigo.
FILAS_EQUIPO_ENEMIGO: tuple[tuple[str, str, str], ...] = (
    ("G4", "G5", "G6"),
    ("G12", "G13", "G14"),
    ("G15", "G16", "G17"),
    ("G1", "G2", "G3"),
)


def pieza(identificador: str) -> PiezaData | None:
    """Devuelve la pieza con ese id, o `None` si no existe."""
    return PIEZAS.get(identificador)


def piezas_por_slot() -> list[PiezaData]:
    """Catálogo ordenado por hueco (el orden de la Herrería del JS)."""
    orden = {slot: indice for indice, slot in enumerate(SLOTS)}
    return sorted(GEAR, key=lambda p: orden[p.slot])
