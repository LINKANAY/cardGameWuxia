"""Píldoras, forja y talismanes — paridad con `PIL`/`FC`/`DESIGN`/`MN`.

Fuente: `js/01-datos.js`.

- `PILDORAS`: 24 entradas (13 de inicio + Talismán de Escape + 10 de
  combate con flag `b`). Las de inicio se equipan antes del combate
  (máx. 3); las de combate van a la bolsa (máx. 4, 2 usos por partida).
- `COSTE_FORJA`: coste de forjar una carta aleatoria de cada rareza
  (`FC` del JS; índice = rareza).
- `DISENOS_TALISMAN`: diseños fabricables de la capa v47 (`DESIGN`).
- `NOMBRE_MATERIAL`: etiquetas de los 3 materiales (`MN`).

Los costes se escriben con palabras (`_materiales(hierbas=3,
polvo_jade=1)`), no con las claves `h`/`n`/`p` del JS. Las claves
cortas solo sobreviven en el enum `Material` (son las que usan los
guards xcg3).
"""

from __future__ import annotations

from .tipos import DisenioTalisman, Material, PildoraData

#: Nombres de material por clave corta (`MN` del JS).
NOMBRE_MATERIAL: dict[Material, str] = {
    Material.HIERBAS: "hierbas",
    Material.NUCLEOS: "núcleos",
    Material.POLVO_JADE: "polvo de jade",
}


def _materiales(
    hierbas: int = 0,
    nucleos: int = 0,
    polvo_jade: int = 0,
) -> dict[Material, int]:
    """Coste de fabricación, con el nombre completo de cada material.

    Sustituye al helper JS `_coste(h=3, p=1)`: los materiales con
    cantidad 0 se omiten (mismo comportamiento que el dict literal del
    monolito, que solo incluía las claves presentes).

    Args:
        hierbas: cantidad de hierbas comunes (`h` en el JS).
        nucleos: cantidad de núcleos espirituales (`n` en el JS).
        polvo_jade: cantidad de polvo de jade (`p` en el JS).

    Returns:
        Diccionario material → cantidad (sin entradas a cero).
    """
    coste: dict[Material, int] = {}
    if hierbas:
        coste[Material.HIERBAS] = hierbas
    if nucleos:
        coste[Material.NUCLEOS] = nucleos
    if polvo_jade:
        coste[Material.POLVO_JADE] = polvo_jade
    return coste


PILDORAS: dict[str, PildoraData] = {
    # --- Píldoras de inicio (se equipan antes del combate) ---
    "vit": PildoraData(
        identificador="vit",
        nombre="Elixir de Vitalidad",
        coste=_materiales(hierbas=3),
        efecto="Empiezas con +8 de vida",
    ),
    "dra": PildoraData(
        identificador="dra",
        nombre="Píldora del Dragón",
        coste=_materiales(nucleos=2),
        efecto="+3 Qi en tu primer turno",
    ),
    "cla": PildoraData(
        identificador="cla",
        nombre="Píldora de Claridad",
        coste=_materiales(hierbas=2, polvo_jade=1),
        efecto="Robas 2 cartas extra al inicio",
    ),
    "esc": PildoraData(
        identificador="esc",
        nombre="Píldora de Jade",
        coste=_materiales(polvo_jade=2),
        efecto="Empiezas con 6 de escudo",
    ),
    "reg": PildoraData(
        identificador="reg",
        nombre="Elixir Regenerador",
        coste=_materiales(hierbas=4, polvo_jade=2),
        efecto=(
            "Ganas 2 de escudo al inicio de cada turno (la vida solo se "
            "cura con cartas)"
        ),
    ),
    "dsp": PildoraData(
        identificador="dsp",
        nombre="Píldora del Despertar",
        coste=_materiales(hierbas=3, nucleos=1),
        efecto="+1 Qi máximo durante el combate",
    ),
    "fur": PildoraData(
        identificador="fur",
        nombre="Píldora de la Furia",
        coste=_materiales(nucleos=2, polvo_jade=2),
        efecto="Haces 4 de daño al héroe enemigo al empezar",
    ),
    "ven": PildoraData(
        identificador="ven",
        nombre="Veneno de Mil Hojas",
        coste=_materiales(hierbas=3, polvo_jade=3),
        efecto="El enemigo empieza con 6 de vida menos",
    ),
    "qi2": PildoraData(
        identificador="qi2",
        nombre="Elixir del Qi Infinito",
        coste=_materiales(nucleos=3, polvo_jade=3),
        efecto="Ganas 1 Qi extra cada turno",
    ),
    "dr2": PildoraData(
        identificador="dr2",
        nombre="Elixir de la Sabiduría",
        coste=_materiales(hierbas=4, nucleos=2, polvo_jade=2),
        efecto="Robas 1 carta extra cada turno",
    ),
    "tor": PildoraData(
        identificador="tor",
        nombre="Píldora de la Tortuga",
        coste=_materiales(polvo_jade=5),
        efecto="Empiezas con 12 de escudo",
    ),
    "rar": PildoraData(
        identificador="rar",
        nombre="Píldora del Destino",
        coste=_materiales(nucleos=4, polvo_jade=6),
        efecto="Recibes una carta Épica o mejor al empezar",
    ),
    "inm": PildoraData(
        identificador="inm",
        nombre="Píldora de Inmortalidad",
        coste=_materiales(hierbas=6, nucleos=5, polvo_jade=8),
        efecto="Si mueres, revives con 15 de vida (una sola vez)",
    ),
    # --- Talismán de Escape (píldora especial; se revela en misiones) ---
    "tes": PildoraData(
        identificador="tes",
        nombre="Talismán de Escape",
        coste=_materiales(polvo_jade=4, hierbas=2),
        efecto=(
            "Si fueras a morir, escapas del combate sin morir (se consume)"
        ),
    ),
    # --- Píldoras de combate (bolsa; flag `b` en el JS) ---
    "cur": PildoraData(
        identificador="cur",
        nombre="Píldora de Curación Rápida",
        coste=_materiales(hierbas=2, polvo_jade=1),
        efecto="En combate: curas 10 de vida",
        es_combate=True,
    ),
    "qiR": PildoraData(
        identificador="qiR",
        nombre="Píldora de Qi Instantáneo",
        coste=_materiales(nucleos=1, polvo_jade=2),
        efecto="En combate: +4 Qi este turno",
        es_combate=True,
    ),
    "rob": PildoraData(
        identificador="rob",
        nombre="Elixir de Visión",
        coste=_materiales(hierbas=2, nucleos=1),
        efecto="En combate: robas 3 cartas",
        es_combate=True,
    ),
    "fue": PildoraData(
        identificador="fue",
        nombre="Píldora de Fuego Interior",
        coste=_materiales(nucleos=2, polvo_jade=2),
        efecto="En combate: 6 de daño al héroe enemigo",
        es_combate=True,
    ),
    "pet": PildoraData(
        identificador="pet",
        nombre="Píldora de Piel de Piedra",
        coste=_materiales(polvo_jade=3),
        efecto="En combate: +10 de escudo",
        es_combate=True,
    ),
    "cng": PildoraData(
        identificador="cng",
        nombre="Píldora Congelante",
        coste=_materiales(nucleos=2, polvo_jade=3),
        efecto="En combate: congela a todas las criaturas rivales",
        es_combate=True,
    ),
    "pur": PildoraData(
        identificador="pur",
        nombre="Píldora Purificadora",
        coste=_materiales(hierbas=3, polvo_jade=1),
        efecto=(
            "En combate: quita congelación y sellos de Qi, y cura 3"
        ),
        es_combate=True,
    ),
    "fur2": PildoraData(
        identificador="fur2",
        nombre="Elixir de Furia",
        coste=_materiales(hierbas=2, nucleos=2, polvo_jade=2),
        efecto="En combate: tus criaturas ganan +2 de ataque",
        es_combate=True,
    ),
    "hea2": PildoraData(
        identificador="hea2",
        nombre="Píldora de Raíz Viva",
        coste=_materiales(hierbas=3, polvo_jade=2),
        efecto="En combate: tus criaturas ganan +5 de vida",
        es_combate=True,
    ),
    "vnn": PildoraData(
        identificador="vnn",
        nombre="Veneno Instantáneo",
        coste=_materiales(hierbas=2, nucleos=2, polvo_jade=2),
        efecto="En combate: 4 de daño a todas las criaturas rivales",
        es_combate=True,
    ),
    # --- Píldoras de recuperación (flag `o`; Cueva de Reclusión) ---
    # Object.assign(PIL, …) de js/12-v47-init.js:60-64.
    "rcA": PildoraData(
        identificador="rcA",
        nombre="Píldora de Recuperación Menor",
        coste=_materiales(hierbas=3),
        efecto=(
            "Fuera de combate (Cueva de Reclusión): recupera el 25% "
            "de la vida máxima"
        ),
        es_recuperacion=True,
        porcentaje_recuperacion=25,
    ),
    "rcB": PildoraData(
        identificador="rcB",
        nombre="Píldora de Recuperación Media",
        coste=_materiales(hierbas=4, polvo_jade=2),
        efecto=(
            "Fuera de combate (Cueva de Reclusión): recupera el 45% "
            "de la vida máxima"
        ),
        es_recuperacion=True,
        porcentaje_recuperacion=45,
    ),
    "rcC": PildoraData(
        identificador="rcC",
        nombre="Elixir de Recuperación Mayor",
        coste=_materiales(hierbas=5, nucleos=2, polvo_jade=3),
        efecto=(
            "Fuera de combate (Cueva de Reclusión): recupera el 70% "
            "de la vida máxima"
        ),
        es_recuperacion=True,
        porcentaje_recuperacion=70,
    ),
}

#: Coste de forjar una carta aleatoria por rareza (`FC` del JS).
#: El índice es la rareza 0–5; el valor es un dict material→cantidad.
COSTE_FORJA: tuple[dict[Material, int], ...] = (
    _materiales(polvo_jade=2),
    _materiales(polvo_jade=4),
    _materiales(polvo_jade=7),
    _materiales(polvo_jade=10, nucleos=2),
    _materiales(polvo_jade=16, nucleos=4),
    _materiales(polvo_jade=24, nucleos=8),
)

#: Diseños de talismán aprendibles desde misiones y fabricables (`DESIGN`).
DISENOS_TALISMAN: dict[str, DisenioTalisman] = {
    "ward": DisenioTalisman(
        identificador="ward",
        nombre="Talismán de Protección",
        coste=_materiales(nucleos=4, polvo_jade=4),
        efecto="Pasivo: +5 de escudo al inicio del combate",
    ),
    "focus": DisenioTalisman(
        identificador="focus",
        nombre="Talismán de Concentración",
        coste=_materiales(nucleos=5, polvo_jade=5),
        efecto="Pasivo: +2 Qi por turno",
    ),
    "ember": DisenioTalisman(
        identificador="ember",
        nombre="Talismán de Ceniza",
        coste=_materiales(nucleos=3, polvo_jade=3),
        efecto="Consumible: 8 de daño al enemigo",
    ),
    "escape": DisenioTalisman(
        identificador="escape",
        nombre="Talismán de Escape",
        coste=_materiales(polvo_jade=4, hierbas=2),
        efecto="Consumible: escapa del combate",
    ),
}

#: Receta que la partida empieza conocida (`rec = { vit: 1 }` del JS).
RECETAS_INICIALES: frozenset[str] = frozenset({"vit"})

#: Receta del Talismán de Escape, que el JS fuerza al cargar
#: (`rec.tes = 1` en el bloque de lectura de save).
RECETA_TALISMAN_ESCAPE: str = "tes"

#: Tipo de icono por píldora (`PILK` de `js/07-campamento.js`).
#: El valor es la clase CSS del `<span class="pill …">` del monolito;
#: `'tal'` dibuja el talismán con el glifo 符 en vez de la poción.
ICONO_PILDKIND: dict[str, str] = {
    "vit": "heal",
    "dra": "gold",
    "cla": "draw",
    "esc": "shield",
    "reg": "heal",
    "dsp": "gold",
    "fur": "dmg",
    "ven": "poison",
    "qi2": "qi",
    "dr2": "draw",
    "tor": "shield",
    "rar": "gold",
    "inm": "gold",
    "cur": "heal",
    "qiR": "qi",
    "rob": "draw",
    "fue": "dmg",
    "pet": "shield",
    "cng": "ice",
    "pur": "heal",
    "fur2": "dmg",
    "hea2": "heal",
    "vnn": "poison",
    "tes": "tal",
    "rcA": "heal",
    "rcB": "heal",
    "rcC": "heal",
}
