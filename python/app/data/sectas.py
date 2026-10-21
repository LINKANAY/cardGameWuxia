"""Sectas jugables — paridad con `S` de `js/01-datos.js` y `js/05-arte.js`.

Cada secta define su mazo inicial de 5 cartas (en las v47 mon/pil/tru/bam
las 5 primeras cartas del bloque `NS` de `js/06-contenido.js`). El mapa
inverso carta→secta (`SECTA_DE_CARTA`; `SC` en el JS) se deriva igual
que en `js/05-arte.js:18`:
``for (const k in S) S[k].l.forEach(i => SC[i] = k)``, más los assigns
del monolito y los `SC[id] = k` de `js/06-contenido.js`.
"""

from __future__ import annotations

from .tipos import SectaData

SECTAS: dict[str, SectaData] = {
    "esp": SectaData(
        identificador="esp",
        nombre="Espada Celestial",
        descripcion=(
            "Daño rápido. Cada 3 técnicas de espada: Intención de Espada "
            "(+3 a la siguiente)."
        ),
        cartas_iniciales=("cf", "ev", "ld", "ma", "te"),
    ),
    "lot": SectaData(
        identificador="lot",
        nombre="Loto de Jade",
        descripcion="Curación, escudo y control del ritmo.",
        cartas_iniciales=("lc", "ej", "gr", "ml", "ab"),
    ),
    "tal": SectaData(
        identificador="tal",
        nombre="Mil Talismanes",
        descripcion="Efectos baratos, drenaje de Qi y daño de área.",
        cartas_iniciales=("tf", "tl", "fe", "mt", "gd"),
    ),
    "lun": SectaData(
        identificador="lun",
        nombre="Palacio de la Luna",
        descripcion="Robo de cartas, ilusiones y Qi rival reducido.",
        cartas_iniciales=("il", "em", "zl", "vs", "pl"),
    ),
    "val": SectaData(
        identificador="val",
        nombre="Valle de los Demonios",
        descripcion="Sacrifica vida por Qi y criaturas pesadas.",
        cartas_iniciales=("sa", "dm", "co", "cd", "av"),
    ),
    "dra": SectaData(
        identificador="dra",
        nombre="Palacio del Dragón",
        descripcion="Criaturas enormes y Qi extra.",
        cartas_iniciales=("dc", "ad", "rd", "pf", "fn"),
    ),
    # Sectas v47 añadidas con `Object.assign(S, …)` en js/05-arte.js:194
    # (`l: []`); después `js/06-contenido.js:12` les empuja sus 5
    # primeras cartas de NS con `if (i < 5) S[k].l.push(id)`, que aquí
    # son `cartas_iniciales`.
    "mon": SectaData(
        identificador="mon",
        nombre="Montaña Inmortal",
        descripcion="Defensa total: Provocar, escudos y criaturas enormes.",
        cartas_iniciales=("M01", "M02", "M03", "M04", "M05"),
    ),
    "pil": SectaData(
        identificador="pil",
        nombre="Pabellón de Alquimia",
        descripcion="Píldoras, curación, robo de cartas y Qi extra.",
        cartas_iniciales=("P01", "P02", "P03", "P04", "P05"),
    ),
    "tru": SectaData(
        identificador="tru",
        nombre="Templo del Trueno",
        descripcion="Rayos, daño de área e Ímpetu para ganar rápido.",
        cartas_iniciales=("T01", "T02", "T03", "T04", "T05"),
    ),
    "bam": SectaData(
        identificador="bam",
        nombre="Bosque de Bambú",
        descripcion="Bestias que crecen, Ímpetu y control con raíces.",
        cartas_iniciales=("B01", "B02", "B03", "B04", "B05"),
    ),
}

#: Mapa carta → secta (`SC` de `js/05-arte.js:18` + los
#: `Object.assign(SC, …)` de las extensiones en `js/05-arte.js:86,98,128`).
#: Las cartas no listadas aquí son neutrales de verdad (lista `NEU`);
#: las marcadas `'neu'` son coleccionables sin puesto de secta (se
#: comportan como neutrales en los filtros `SX`, pero no son gratis).
SECTA_DE_CARTA: dict[str, str] = {
    carta: secta.identificador
    for secta in SECTAS.values()
    for carta in secta.cartas_iniciales
}

#: Extensiones de `SC` (v47): cartas de secta añadidas después del set
#: base, en el mismo orden que los tres `Object.assign` del monolito.
SECTA_DE_CARTA.update(
    {
        # js/05-arte.js:86
        "se": "esp", "ex": "esp", "ta": "tal", "fr": "dra", "dt": "dra",
        "lm": "lot", "gh": "lun", "pi": "neu", "ca": "neu", "ac": "neu",
        "pr": "val", "mp": "neu",
        # js/05-arte.js:98
        "qe": "esp", "dh": "esp", "ee": "esp", "cp": "esp", "bl": "lot",
        "mj": "lot", "ep": "lot", "dl": "lot", "th": "tal", "bt": "tal",
        "ft": "tal", "gc": "tal", "ra": "lun", "sl": "lun", "ec": "lun",
        "dg": "lun", "sd": "val", "pd": "val", "ba": "val", "sn": "val",
        "eg": "dra", "sf": "dra", "dy": "dra", "sb": "dra",
        # js/05-arte.js:128
        "ce": "esp", "ae": "esp", "ru": "esp", "bn": "lot", "rl": "lot",
        "gl": "lot", "tn": "tal", "sg": "tal", "mg": "tal", "ei": "lun",
        "ls": "lun", "vn": "lun", "ap": "val", "cn": "val", "rk": "val",
        "gz": "dra", "ed": "dra", "cb": "dra",
    }
)

#: Cartas de secta creadas por los bucles de `js/06-contenido.js`
#: (`SC[id] = k`, sólo si `k` no es null). Aquí sólo entran NS, XC, XF,
#: XR y XH: XV (V01–V07) y las neutras Z31/Z32, Y21/Y22, X01/X02 y
#: H01/H02 llevan `k = null` en el monolito. Las 5 primeras de NS
#: duplican `cartas_iniciales` (donde el JS hace el `push`), igual que
#: en el `SC[id] = k` de la línea 12.
SECTA_DE_CARTA.update(
    {
        # js/06-contenido.js:3-10 — NS (M/P/T/B 01-13)
        "M01": "mon", "M02": "mon", "M03": "mon", "M04": "mon",
        "M05": "mon", "M06": "mon", "M07": "mon", "M08": "mon",
        "M09": "mon", "M10": "mon", "M11": "mon", "M12": "mon",
        "M13": "mon",
        "P01": "pil", "P02": "pil", "P03": "pil", "P04": "pil",
        "P05": "pil", "P06": "pil", "P07": "pil", "P08": "pil",
        "P09": "pil", "P10": "pil", "P11": "pil", "P12": "pil",
        "P13": "pil",
        "T01": "tru", "T02": "tru", "T03": "tru", "T04": "tru",
        "T05": "tru", "T06": "tru", "T07": "tru", "T08": "tru",
        "T09": "tru", "T10": "tru", "T11": "tru", "T12": "tru",
        "T13": "tru",
        "B01": "bam", "B02": "bam", "B03": "bam", "B04": "bam",
        "B05": "bam", "B06": "bam", "B07": "bam", "B08": "bam",
        "B09": "bam", "B10": "bam", "B11": "bam", "B12": "bam",
        "B13": "bam",
        # js/06-contenido.js:13-23 — XC (Z01-Z30; Z31-Z32 sin secta)
        "Z01": "esp", "Z02": "esp", "Z03": "esp",
        "Z04": "lot", "Z05": "lot", "Z06": "lot",
        "Z07": "tal", "Z08": "tal", "Z09": "tal",
        "Z10": "lun", "Z11": "lun", "Z12": "lun",
        "Z13": "val", "Z14": "val", "Z15": "val",
        "Z16": "dra", "Z17": "dra", "Z18": "dra",
        "Z19": "mon", "Z20": "mon", "Z21": "mon",
        "Z22": "pil", "Z23": "pil", "Z24": "pil",
        "Z25": "tru", "Z26": "tru", "Z27": "tru",
        "Z28": "bam", "Z29": "bam", "Z30": "bam",
        # js/06-contenido.js:25-27 — XF (Y01-Y20; Y21-Y22 sin secta)
        "Y01": "esp", "Y02": "lot", "Y03": "tal", "Y04": "lun",
        "Y05": "val", "Y06": "dra", "Y07": "mon", "Y08": "pil",
        "Y09": "tru", "Y10": "bam", "Y11": "esp", "Y12": "lot",
        "Y13": "tal", "Y14": "lun", "Y15": "val", "Y16": "dra",
        "Y17": "mon", "Y18": "pil", "Y19": "tru", "Y20": "bam",
        # js/06-contenido.js:29 — XR (X03-X12; X01-X02 sin secta)
        "X03": "esp", "X04": "lot", "X05": "tal", "X06": "lun",
        "X07": "val", "X08": "dra", "X09": "mon", "X10": "pil",
        "X11": "tru", "X12": "bam",
        # js/06-contenido.js:41 — XH (H03-H04; H01-H02 sin secta)
        "H03": "pil", "H04": "pil",
        # js/06-contenido.js:45 — XV: todas con k = null, sin secta.
    }
)

#: Sectas con puesto de mercado propio (`MK` de `js/03-cartas-mercado.js`;
#: `neu` es el puesto General y no es una secta jugable).
SECTAS_CON_MERCADO: tuple[str, ...] = (
    "esp", "lot", "tal", "lun", "val", "dra", "mon", "pil", "tru", "bam", "neu",
)
