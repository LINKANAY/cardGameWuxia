"""Narrativa del juego — paridad con `PRO`, `ST`, `EN`, `FIN` de `js/01-datos.js`.

Textos fijos de la campaña de Lin Yu. Se mantienen literales (incluidos
los signos de interrogación angulares y los puntos suspensivos) para no
alterar la voz del juego.
"""

from __future__ import annotations

import math


def redondear_js(valor: float) -> int:
    """Redondea como `Math.round` de JavaScript (mitad hacia arriba).

    Python usa redondeo bancario (``round(12.5) == 12``), pero el JS
    redondea las mitades hacia ``+infinito`` (``Math.round(12.5) == 13``).
    Las fórmulas de vida de enemigos dependen de esto (p. ej.
    ``round(25 * 0.5)``). Equivalente exacto: ``floor(valor + 0.5)``.
    """
    return math.floor(valor + 0.5)


#: Prólogo mostrado en la portada/splash (`PRO` del JS).
PROLOGO: str = (
    "Lin Yu, hijo de un leñador de la aldea Piedra Gris, despierta una "
    "raíz espiritual la noche en que una espada cae del cielo. Su maestro, "
    "el anciano Bai Heng, le advierte: «El Dao no se regala, se arrebata, "
    "tribulación a tribulación». Nueve reinos separan al mortal del Cielo, "
    "y más allá del Cielo aguardan otros seis."
)

#: Historia de cada nivel índice 0–7 (`ST` del JS). Se muestra en la
#: pantalla de presentación del combate cuando el enemigo no tiene
#: `story` propia (sólo los jefes de mazmorra la llevan).
TEXTO_INTRO_NIVEL: tuple[str, ...] = (
    "La noche del despertar, bandidos y un rival envidioso acechan la "
    "aldea. Lin Yu debe proteger la espada caída.",
    "Bai Heng lo lleva a la secta del Loto de Jade. Para entrar, Lin Yu "
    "debe superar las pruebas de sus discípulas.",
    "Un anciano demoníaco codicia la espada. Lin Yu cruza el Valle de los "
    "Demonios para impedir que caiga en sus manos.",
    "En el Palacio de la Luna, las sombras guardan el secreto del origen "
    "de la espada, y la Emperatriz de los Mil Fantasmas lo reclama.",
    "Para romper su límite, Lin Yu debe soportar la tribulación celestial. "
    "En el rayo aparece alguien del pasado de Bai Heng.",
    "Más allá de la tribulación se extiende el Mar de Nubes. Solo quien "
    "cruza el Puente Celestial alcanza el Reino Inmortal.",
    "En el abismo, la espada de Lin Yu vibra: es un fragmento del "
    "Soberano de las Mil Espadas, y quiere reunirse con él.",
    "Ante el trono celestial, el Dao Primordial espera. Si Lin Yu cae, "
    "ningún cultivador volverá a ascender.",
)

#: Texto de victoria de cada nivel (`EN` del JS). Se muestra al vencer
#: al jefe de dificultad 5 de cada nivel principal.
TEXTO_FIN_NIVEL: tuple[str, ...] = (
    "La aldea está a salvo, pero Lin Yu ya no es un mortal.",
    "La secta del Loto lo acepta como discípulo.",
    "El Anciano huye herido; el Valle jura venganza.",
    "La Emperatriz se disuelve y revela una pista: el Inmortal Caído.",
    "Lin Yu sobrevive a la tribulación y asciende al fin de la mortalidad.",
    "El Puente Celestial se abre ante él.",
    "La espada y su fragmento se unen: Lin Yu empuña el Filo Eterno.",
    "El trono queda vacío, y el Cielo, a la espera.",
)

#: Final del juego mostrado al vencer al enemigo índice 47 (`FIN` del JS;
#: el enemigo 47 es el Dao Primordial, último de nivel 8).
FINAL: str = (
    "Con el Dao Primordial disuelto, el Cielo se abre. Lin Yu y Bai Heng "
    "ven por fin el Reino Celestial. La espada caída vuelve a casa, y el "
    "Camino continúa."
)

#: Nombres de dificultad por índice 0–5 (`DF` de `js/01-datos.js`).
DIFICULTADES: tuple[str, ...] = (
    "Muy fácil",
    "Fácil",
    "Normal",
    "Difícil",
    "Muy difícil",
    "Boss final",
)

#: Colores hex de dificultad por índice (`DC` de `js/01-datos.js`).
COLOR_DIFICULTAD: tuple[str, ...] = (
    "#8fd9b6",
    "#6cc4a1",
    "#d9b55b",
    "#e09a4a",
    "#c4483d",
    "#b070e0",
)

#: Vida base del héroe por índice de nivel (`B` de `js/01-datos.js`).
VIDA_BASE_NIVEL: tuple[int, ...] = (16, 20, 25, 30, 34, 38, 42, 44)

#: Multiplicador de vida por dificultad (`MU` de `js/01-datos.js`).
MULT_DIFICULTAD: tuple[float, ...] = (0.5, 0.7, 0.9, 1.1, 1.35, 1.7)

#: Nombres de los reinos de cultivo, del mortal al soberano (`R` del JS).
REINOS: tuple[str, ...] = (
    "Mortal",
    "Refinamiento de Qi",
    "Fundación",
    "Núcleo Dorado",
    "Alma Naciente",
    "Transformación Divina",
    "Ascensión",
    "Inmortal",
    "Celestial",
    "Formación del Alma",
    "Reino de la Tribulación",
    "Inmortal Falso",
    "Inmortal Verdadero",
    "Rey Inmortal",
    "Soberano del Dao",
)

# --- Frases de combate (`SAY` de `js/01-datos.js`) --------------------------
# El enemigo dice una frase al actuar. El tipo de frase depende de la
# situación (`say(kind, nombre_carta, nombre_criatura)` del JS):
#   a = ataque (carta con daño/área/tribulación/drenaje/daño a criatura)
#   s = invocación (criatura)
#   d = defensa (carta sin efecto ofensivo ni criatura)
#   h = burla / charla
#   c = ataque con criatura propia
#   t = dañar una criatura rival con técnica (añadido con Object.assign)
# Las plantillas usan {n} = nombre de la carta y {m} = nombre de la
# criatura objetivo (sustituidos en tiempo de ejecución por el motor).

#: Frases por secta y situación. Cada lista es una de las opciones entre
#: las que el motor elige con `random()`.
FRASES_COMBATE: dict[str, dict[str, tuple[str, ...]]] = {
    "esp": {
        "ataque": (
            "¡Prueba mi «{n}»!",
            "«{n}»... ¿lograrás esquivarlo?",
        ),
        "invocacion": ("¡Acude a mi filo, {n}!",),
        "defensa": ("Mi espada se sirve de «{n}».",),
        "burla": ("¿«{n}» es lo mejor que tienes?",),
        "criatura": (
            "¡{n}, corta sin piedad!",
            "¡{n}, a la carga!",
        ),
        "criatura_objetivo": ("«{n}» parte en dos a tu {m}.",),
    },
    "lot": {
        "ataque": (
            "Que «{n}» te enseñe humildad.",
            "«{n}» florece... y también hiere.",
        ),
        "invocacion": ("Ven, {n}, protégeme.",),
        "defensa": ("«{n}» me renueva, mortal.",),
        "burla": ("«{n}» solo moja mis pétalos.",),
        "criatura": (
            "{n}, golpea con suavidad letal.",
            "Adelante, {n}.",
        ),
        "criatura_objetivo": ("«{n}» envuelve a tu {m}.",),
    },
    "tal": {
        "ataque": (
            "Talismán activado: «{n}».",
            "«{n}» ya estaba escrito en tu destino.",
        ),
        "invocacion": ("Sello roto: surge {n}.",),
        "defensa": ("«{n}» refuerza mi formación.",),
        "burla": ("«{n}» cae en mi trampa.",),
        "criatura": (
            "{n}, ¡cumple tu sello!",
            "{n}, ¡atrápalo!",
        ),
        "criatura_objetivo": ("«{n}» sella a tu {m}.",),
    },
    "lun": {
        "ataque": (
            "«{n}»... ¿era real lo que viste?",
            "Mira la luna: «{n}».",
        ),
        "invocacion": ("Del reflejo nace {n}.",),
        "defensa": ("«{n}» te engaña otra vez.",),
        "burla": ("«{n}» solo atraviesa humo.",),
        "criatura": (
            "{n}, desde la sombra.",
            "{n}, ¡atácalo en silencio!",
        ),
        "criatura_objetivo": ("«{n}» confunde a tu {m}.",),
    },
    "val": {
        "ataque": (
            "¡Prueba la sangre de «{n}»!",
            "«{n}» exige su tributo.",
        ),
        "invocacion": ("¡Devora, {n}!",),
        "defensa": ("Pago con sangre: «{n}».",),
        "burla": ("Tu «{n}» alimenta mi furia.",),
        "criatura": (
            "{n}, ¡destroza su alma!",
            "¡{n}, sin piedad!",
        ),
        "criatura_objetivo": ("«{n}» devora a tu {m}.",),
    },
    "dra": {
        "ataque": (
            "«{n}» arde con la furia del dragón.",
            "Tiembla ante «{n}».",
        ),
        "invocacion": ("¡Álzate, {n}!",),
        "defensa": ("«{n}» refuerza mis escamas.",),
        "burla": ("Tu «{n}» no araña mis escamas.",),
        "criatura": (
            "{n}, ¡aplástalo!",
            "¡{n}, ruge!",
        ),
        "criatura_objetivo": ("«{n}» aplasta a tu {m}.",),
    },
}
