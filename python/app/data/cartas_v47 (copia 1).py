"""Cartas v47 — las 129 cartas creadas por los bucles de `js/06-contenido.js`.

Port campo a campo de los seis bloques del monolito, en su orden de
ejecución: `NS` (52 cartas de secta), `XC` (32), `XF` (22), `XR` (12),
`XH` (4) y `XV` (7). El JS los registra con
``C[id] = { n, c, t, ...fx }; SC[id] = k``; aquí cada carta se construye
con el `_carta` de `app.data.cartas`, así que una clave de efecto mal
escrita revienta con `TypeError` al importar.

Ciclo de imports evitado: este módulo importa `_carta` de
`app.data.cartas`, y `cartas.py` importa `_CARTAS_V47` sólo al final,
cuando `_carta` y `CARTAS` ya están definidos (ahí el módulo parcial
basta para resolver el import). Si alguien importa `cartas_v47` el
primero, Python ejecuta antes `app.data.__init__`, que importa
`cartas`, así que el orden real siempre es el seguro.

Traducción no trivial: `Y05` usa `ts: ['x', 1]` (auto-daño al dueño
de la formación, `hurt(s, n)` de `fmTurn`), que aquí es
`TipoEfecto.AUTO_DANO`.
"""

from __future__ import annotations

from .cartas import _carta
from .tipos import (
    AlEntrar,
    CartaData,
    HabilidadActiva,
    MejoraAliada,
    TipoCarta,
    TipoEfecto,
    UltimoAliento,
)

# Alias locales (mismo truco que `cartas.py`, más F/R, que sólo existen
# en estos bloques: `t` del JS es 'C'/'T'/'P'/'F'/'R').
CRIATURA = TipoCarta.CRIATURA
TECNICA = TipoCarta.TECNICA
PILDORA = TipoCarta.PILDORA
FORMACION = TipoCarta.FORMACION
RUNA = TipoCarta.RUNA


# ---------------------------------------------------------------------------
# NS — cartas de secta v47 (js/06-contenido.js:2-11). Las 5 primeras de
# cada secta son el mazo inicial: `if (i < 5) S[k].l.push(id)`.
# ---------------------------------------------------------------------------

_CARTAS_V47: tuple[CartaData, ...] = (
    # ── NS · Montaña Inmortal ───────────────────────────────────────────
    _carta(
        "M01", "Aprendiz de la Montaña",
        coste_qi=1, tipo=CRIATURA, ataque=1, vida=3, provocar=True,
    ),
    _carta(
        "M02", "Escudo de Piedra",
        coste_qi=2, tipo=TECNICA, escudo=6,
    ),
    _carta(
        "M03", "Gólem Menor",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=5, provocar=True,
    ),
    _carta(
        "M04", "Terremoto",
        coste_qi=4, tipo=TECNICA, dano_area=3, dano_hroe=2,
    ),
    _carta(
        "M05", "Guardián de la Cumbre",
        coste_qi=5, tipo=CRIATURA, ataque=4, vida=8, provocar=True,
    ),
    _carta(
        "M06", "Avalancha",
        coste_qi=3, tipo=TECNICA, dano_criatura=4,
    ),
    _carta(
        "M07", "Armadura de Roca",
        coste_qi=2, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=0, vida=4),
    ),
    _carta(
        "M08", "Monje de la Cumbre",
        coste_qi=2, tipo=CRIATURA, ataque=2, vida=4, provocar=True,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.ESCUDO, valor=2,
            descripcion="Escudo 2",
        ),
    ),
    _carta(
        "M09", "Peña Inamovible",
        coste_qi=3, tipo=TECNICA, escudo=8,
    ),
    _carta(
        "M10", "Titán de Piedra",
        coste_qi=6, tipo=CRIATURA, ataque=6, vida=9, provocar=True,
    ),
    _carta(
        "M11", "Aliento de la Montaña",
        coste_qi=2, tipo=TECNICA, curar=4, escudo=2,
    ),
    _carta(
        "M12", "Grieta Abismal",
        coste_qi=4, tipo=TECNICA, dano_criatura=6, congelar=True,
    ),
    _carta(
        "M13", "Montaña Viviente",
        coste_qi=7, tipo=CRIATURA, ataque=8, vida=11, provocar=True,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.ESCUDO, valor=6),
    ),
    # ── NS · Pabellón de Alquimia ───────────────────────────────────────
    _carta(
        "P01", "Discípulo del Pabellón",
        coste_qi=1, tipo=CRIATURA, ataque=1, vida=2, robar=1,
    ),
    _carta(
        "P02", "Píldora Restauradora",
        coste_qi=1, tipo=PILDORA, curar=3, robar=1,
    ),
    _carta(
        "P03", "Horno de Jade",
        coste_qi=2, tipo=TECNICA, ganar_qi=2, robar=1,
    ),
    _carta(
        "P04", "Elixir Explosivo",
        coste_qi=3, tipo=PILDORA, dano_hroe=5,
    ),
    _carta(
        "P05", "Maestro Alquimista",
        coste_qi=4, tipo=CRIATURA, ataque=3, vida=5, robar=1, curar=2,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.CURAR, valor=2,
            descripcion="Curar 2",
        ),
    ),
    _carta(
        "P06", "Hierba Espiritual",
        coste_qi=1, tipo=PILDORA, ganar_qi=2,
    ),
    _carta(
        "P07", "Veneno Lento",
        coste_qi=2, tipo=TECNICA, dano_criatura=3,
    ),
    _carta(
        "P08", "Caldero Burbujeante",
        coste_qi=3, tipo=TECNICA, robar=2, curar=3,
    ),
    _carta(
        "P09", "Píldora de Poder",
        coste_qi=2, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=2, vida=2),
    ),
    _carta(
        "P10", "Perla Medicinal",
        coste_qi=2, tipo=PILDORA, curar=5,
    ),
    _carta(
        "P11", "Gólem de Pociones",
        coste_qi=4, tipo=CRIATURA, ataque=4, vida=5, curar=2,
    ),
    _carta(
        "P12", "Elixir de Mil Años",
        coste_qi=5, tipo=PILDORA, curar=10, ganar_qi=2,
    ),
    _carta(
        "P13", "Inmortal Alquimista",
        coste_qi=7, tipo=CRIATURA, ataque=6, vida=8, robar=2, curar=4,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.CURAR, valor=4,
            descripcion="Curar 4",
        ),
    ),
    # ── NS · Templo del Trueno ──────────────────────────────────────────
    _carta(
        "T01", "Monje del Rayo",
        coste_qi=1, tipo=CRIATURA, ataque=2, vida=1, impetu=True,
    ),
    _carta(
        "T02", "Chispa",
        coste_qi=1, tipo=TECNICA, dano_hroe=2, robar=1,
    ),
    _carta(
        "T03", "Nube de Tormenta",
        coste_qi=2, tipo=TECNICA, dano_area=2,
    ),
    _carta(
        "T04", "Martillo del Trueno",
        coste_qi=3, tipo=TECNICA, dano_hroe=5,
    ),
    _carta(
        "T05", "Ave del Trueno",
        coste_qi=4, tipo=CRIATURA, ataque=4, vida=3, impetu=True,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.DANO_HROE, valor=2),
    ),
    _carta(
        "T06", "Relámpago Dirigido",
        coste_qi=2, tipo=TECNICA, dano_criatura=4,
    ),
    _carta(
        "T07", "Cadena de Rayos",
        coste_qi=3, tipo=TECNICA, dano_area=3, dano_hroe=2,
    ),
    _carta(
        "T08", "Tambor de Guerra",
        coste_qi=2, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=2, vida=1),
    ),
    _carta(
        "T09", "Tormenta Eléctrica",
        coste_qi=4, tipo=TECNICA, dano_area=4,
    ),
    _carta(
        "T10", "Dios del Trueno",
        coste_qi=6, tipo=CRIATURA, ataque=6, vida=6, impetu=True,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.DANO_HROE, valor=3,
            descripcion="Rayo 3",
        ),
    ),
    _carta(
        "T11", "Rayo Paralizante",
        coste_qi=3, tipo=TECNICA, dano_criatura=3, congelar=True,
    ),
    _carta(
        "T12", "Cielo de Tormenta",
        coste_qi=5, tipo=TECNICA, dano_hroe=7, dano_area=2,
    ),
    _carta(
        "T13", "Tribulación de Rayos",
        coste_qi=7, tipo=TECNICA, dano_area=5, dano_hroe=6,
    ),
    # ── NS · Bosque de Bambú ────────────────────────────────────────────
    _carta(
        "B01", "Brote de Bambú",
        coste_qi=1, tipo=CRIATURA, ataque=1, vida=2, crece=1,
    ),
    _carta(
        "B02", "Hoja Cortante",
        coste_qi=1, tipo=TECNICA, dano_hroe=3,
    ),
    _carta(
        "B03", "Panda Espiritual",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=5, provocar=True,
    ),
    _carta(
        "B04", "Tigre del Bosque",
        coste_qi=3, tipo=CRIATURA, ataque=4, vida=3, impetu=True,
    ),
    _carta(
        "B05", "Guardián del Bosque",
        coste_qi=5, tipo=CRIATURA, ataque=5, vida=6, crece=1,
    ),
    _carta(
        "B06", "Savia Vital",
        coste_qi=2, tipo=TECNICA, curar=4, robar=1,
    ),
    _carta(
        "B07", "Enredadera",
        coste_qi=2, tipo=TECNICA, dano_criatura=2, congelar=True,
    ),
    _carta(
        "B08", "Zorro de Bambú",
        coste_qi=2, tipo=CRIATURA, ataque=2, vida=2, impetu=True,
    ),
    _carta(
        "B09", "Rugido del Bosque",
        coste_qi=3, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=2, vida=2),
    ),
    _carta(
        "B10", "Mono Sabio",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=4, robar=1,
    ),
    _carta(
        "B11", "Lluvia de Hojas",
        coste_qi=4, tipo=TECNICA, dano_area=3, dano_hroe=2,
    ),
    _carta(
        "B12", "Dragón de Bambú",
        coste_qi=6, tipo=CRIATURA, ataque=6, vida=7, crece=1,
    ),
    _carta(
        "B13", "Espíritu del Bosque Eterno",
        coste_qi=7, tipo=CRIATURA, ataque=7, vida=9, crece=2,
    ),
    # ── XC · Extensiones por secta + neutras (js/06-contenido.js:13-23) ─
    _carta(
        "Z01", "Filo del Alba",
        coste_qi=3, tipo=TECNICA, dano_hroe=4, es_espada=True, robar=1,
    ),
    _carta(
        "Z02", "Sombra de Mil Filos",
        coste_qi=6, tipo=TECNICA, dano_hroe=7, dano_area=2,
        es_espada=True, rareza_fija=4, reliquia=True,
    ),
    _carta(
        "Z03", "Espada Inmortal Despierta",
        coste_qi=7, tipo=CRIATURA, ataque=7, vida=7, impetu=True,
        robar_vida=True, crece=1, rareza_fija=5, reliquia=True,
    ),
    _carta(
        "Z04", "Rocío del Loto Blanco",
        coste_qi=3, tipo=TECNICA, curar=4, escudo=3,
    ),
    _carta(
        "Z05", "Corona de Mil Pétalos",
        coste_qi=6, tipo=TECNICA, curar=10, escudo=6, robar=2,
        rareza_fija=4, reliquia=True,
    ),
    _carta(
        "Z06", "Madre del Loto Eterno",
        coste_qi=7, tipo=CRIATURA, ataque=5, vida=10, provocar=True,
        rareza_fija=5, reliquia=True,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.CURAR, valor=5,
            descripcion="Curar 5",
        ),
    ),
    _carta(
        "Z07", "Cadena de Sellos",
        coste_qi=3, tipo=TECNICA, dano_criatura=3, congelar=True,
        drenar_qi_rival=1,
    ),
    _carta(
        "Z08", "Gran Sello Celestial",
        coste_qi=6, tipo=TECNICA, dano_area=5, dano_hroe=3,
        drenar_qi_rival=2, rareza_fija=4, reliquia=True,
    ),
    _carta(
        "Z09", "Maestro de Mil Talismanes",
        coste_qi=7, tipo=CRIATURA, ataque=5, vida=8, provocar=True,
        rareza_fija=5, reliquia=True,
        al_entrar=AlEntrar(tipo=TipoEfecto.DANO_CRIATURA_AL_AZAR, valor=4),
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.DANO_HROE, valor=4,
            descripcion="Rayo 4",
        ),
    ),
    _carta(
        "Z10", "Danza de Luciérnagas",
        coste_qi=3, tipo=TECNICA, drenar_qi_rival=2, robar=2,
    ),
    _carta(
        "Z11", "Reina de las Mareas",
        coste_qi=6, tipo=CRIATURA, ataque=5, vida=7, rareza_fija=4,
        reliquia=True,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.ROBAR, valor=2),
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.DRENAR_QI, valor=2,
            descripcion="Drenar 2 Qi",
        ),
    ),
    _carta(
        "Z12", "Luna Sangrienta",
        coste_qi=7, tipo=TECNICA, drenar_qi_rival=4, dano_hroe=8,
        robar=2, rareza_fija=5, reliquia=True,
    ),
    _carta(
        "Z13", "Rito de Sangre",
        coste_qi=3, tipo=TECNICA, dano_hroe=5, sacrificar_vida=2,
    ),
    _carta(
        "Z14", "Archidemonio Hambriento",
        coste_qi=6, tipo=CRIATURA, ataque=7, vida=5, robar_vida=True,
        sacrificar_vida=2, rareza_fija=4, reliquia=True,
    ),
    _carta(
        "Z15", "Emperador Demonio",
        coste_qi=7, tipo=CRIATURA, ataque=9, vida=7, robar_vida=True,
        impetu=True, sacrificar_vida=3, rareza_fija=5, reliquia=True,
    ),
    _carta(
        "Z16", "Cría de Dragón Dorado",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=4, ganar_qi=1,
    ),
    _carta(
        "Z17", "Rey de las Cenizas",
        coste_qi=6, tipo=CRIATURA, ataque=7, vida=7, rareza_fija=4,
        reliquia=True,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.DANO_HROE, valor=4),
    ),
    _carta(
        "Z18", "Dragón Primordial",
        coste_qi=7, tipo=CRIATURA, ataque=9, vida=9, ganar_qi=2,
        rareza_fija=5, reliquia=True,
        habilidad_activa=HabilidadActiva(
            coste_qi=3, tipo=TipoEfecto.DANO_HROE, valor=6,
            descripcion="Fuego 6",
        ),
    ),
    _carta(
        "Z19", "Muralla de Roca Viva",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=7, provocar=True,
    ),
    _carta(
        "Z20", "Coloso de la Cumbre",
        coste_qi=6, tipo=CRIATURA, ataque=6, vida=9, provocar=True,
        crece=1, rareza_fija=4, reliquia=True,
    ),
    _carta(
        "Z21", "Corazón de la Montaña",
        coste_qi=7, tipo=TECNICA, escudo=14, curar=8, dano_area=3,
        rareza_fija=5, reliquia=True,
    ),
    _carta(
        "Z22", "Horno de Nueve Fuegos",
        coste_qi=3, tipo=TECNICA, dano_hroe=3, ganar_qi=2, robar=1,
    ),
    _carta(
        "Z23", "Alquimista Supremo",
        coste_qi=5, tipo=CRIATURA, ataque=4, vida=6, robar=2,
        rareza_fija=4, reliquia=True,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.GANAR_QI, valor=2,
            descripcion="+2 Qi",
        ),
    ),
    _carta(
        "Z24", "Píldora del Dao Perfecto",
        coste_qi=6, tipo=TECNICA, curar=12, escudo=8, ganar_qi=4,
        robar=2, rareza_fija=5, reliquia=True,
    ),
    _carta(
        "Z25", "Chispa Serpenteante",
        coste_qi=3, tipo=TECNICA, dano_criatura=4, dano_hroe=2,
    ),
    _carta(
        "Z26", "Avatar del Rayo",
        coste_qi=6, tipo=CRIATURA, ataque=7, vida=5, impetu=True,
        rareza_fija=4, reliquia=True,
        al_entrar=AlEntrar(tipo=TipoEfecto.DANO_CRIATURA_AL_AZAR, valor=3),
    ),
    _carta(
        "Z27", "Tribulación Púrpura",
        coste_qi=7, tipo=TECNICA, dano_hroe=10, dano_area=6,
        rareza_fija=5, reliquia=True,
    ),
    _carta(
        "Z28", "Brote de Jade",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=5, crece=1,
    ),
    _carta(
        "Z29", "Guardián Milenario",
        coste_qi=6, tipo=CRIATURA, ataque=5, vida=9, provocar=True,
        crece=2, rareza_fija=4, reliquia=True,
    ),
    _carta(
        "Z30", "Árbol del Mundo",
        coste_qi=8, tipo=CRIATURA, ataque=8, vida=14, crece=2,
        rareza_fija=5, reliquia=True,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.CURAR, valor=10),
    ),
    _carta(
        "Z31", "Maestro Errante",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=4, robar=1,
    ),
    _carta(
        "Z32", "Talismán del Vacío",
        coste_qi=4, tipo=TECNICA, dano_hroe=6, drenar_qi_rival=1,
    ),
    # ── XF · Formaciones y runas (js/06-contenido.js:25-27) ─────────────
    _carta(
        "Y01", "Formación de los Cinco Filos",
        coste_qi=3, tipo=FORMACION, mejora_ataque_al_trazar=1,
    ),
    _carta(
        "Y02", "Formación del Loto Sereno",
        coste_qi=3, tipo=FORMACION,
        efecto_inicio_turno=(TipoEfecto.CURAR, 2),
    ),
    _carta(
        "Y03", "Formación de los Ocho Trigramas",
        coste_qi=3, tipo=FORMACION,
        efecto_inicio_turno=(TipoEfecto.DANO_CRIATURA_AL_AZAR, 1),
    ),
    _carta(
        "Y04", "Formación de la Luna Creciente",
        coste_qi=4, tipo=FORMACION,
        efecto_inicio_turno=(TipoEfecto.ESCUDO, 3),
    ),
    _carta(
        "Y05", "Formación de Sangre Hirviente",
        coste_qi=3, tipo=FORMACION, mejora_ataque_al_trazar=2,
        efecto_inicio_turno=(TipoEfecto.AUTO_DANO, 1),
    ),
    _carta(
        "Y06", "Formación del Dragón Enroscado",
        coste_qi=4, tipo=FORMACION, mejora_vida_al_trazar=3,
    ),
    _carta(
        "Y07", "Formación de la Tortuga de Roca",
        coste_qi=3, tipo=FORMACION, mejora_vida_al_trazar=2,
        efecto_inicio_turno=(TipoEfecto.ESCUDO, 1),
    ),
    _carta(
        "Y08", "Formación del Caldero de Nueve Fuegos",
        coste_qi=5, tipo=FORMACION,
        efecto_inicio_turno=(TipoEfecto.GANAR_QI, 1),
    ),
    _carta(
        "Y09", "Formación del Trueno Circular",
        coste_qi=3, tipo=FORMACION,
        efecto_inicio_turno=(TipoEfecto.DANO_HROE, 1),
    ),
    _carta(
        "Y10", "Formación del Bosque Vivo",
        coste_qi=3, tipo=FORMACION, mejora_vida_al_trazar=1,
        efecto_inicio_turno=(TipoEfecto.CURAR, 1),
    ),
    _carta(
        "Y11", "Runa del Filo Rápido",
        coste_qi=2, tipo=RUNA, duracion_turnos=3,
        efecto_inicio_turno=(TipoEfecto.DANO_HROE, 2),
    ),
    _carta(
        "Y12", "Runa de Savia",
        coste_qi=1, tipo=RUNA, duracion_turnos=3,
        efecto_inicio_turno=(TipoEfecto.CURAR, 2),
    ),
    _carta(
        "Y13", "Runa de Sello",
        coste_qi=2, tipo=RUNA, duracion_turnos=3,
        efecto_inicio_turno=(TipoEfecto.DANO_CRIATURA_AL_AZAR, 2),
    ),
    _carta(
        "Y14", "Runa del Eclipse",
        coste_qi=2, tipo=RUNA, duracion_turnos=2,
        efecto_inicio_turno=(TipoEfecto.ROBAR, 1),
    ),
    _carta(
        "Y15", "Runa de Sangre",
        coste_qi=1, tipo=RUNA, duracion_turnos=2, sacrificar_vida=2,
        efecto_inicio_turno=(TipoEfecto.DANO_HROE, 3),
    ),
    _carta(
        "Y16", "Runa del Dragón",
        coste_qi=2, tipo=RUNA, duracion_turnos=2,
        efecto_inicio_turno=(TipoEfecto.GANAR_QI, 1),
    ),
    _carta(
        "Y17", "Runa de Piedra",
        coste_qi=2, tipo=RUNA, duracion_turnos=3,
        efecto_inicio_turno=(TipoEfecto.ESCUDO, 3),
    ),
    _carta(
        "Y18", "Runa de Alquimia",
        coste_qi=2, tipo=RUNA, duracion_turnos=2,
        efecto_inicio_turno=(TipoEfecto.CURAR, 3),
    ),
    _carta(
        "Y19", "Runa del Rayo",
        coste_qi=2, tipo=RUNA, duracion_turnos=2,
        efecto_inicio_turno=(TipoEfecto.DANO_HROE, 3),
    ),
    _carta(
        "Y20", "Runa del Bambú",
        coste_qi=1, tipo=RUNA, duracion_turnos=3,
        efecto_inicio_turno=(TipoEfecto.ESCUDO, 2),
    ),
    _carta(
        "Y21", "Disipar Formación",
        coste_qi=2, tipo=TECNICA, disipa=True, robar=1,
    ),
    _carta(
        "Y22", "Runa de Guardia",
        coste_qi=1, tipo=RUNA, duracion_turnos=2,
        efecto_inicio_turno=(TipoEfecto.ESCUDO, 2),
    ),
    # ── XR · Renovar la mano (js/06-contenido.js:29) ────────────────────
    _carta(
        "X01", "Renovar la Mano",
        coste_qi=1, tipo=TECNICA, renovar=3,
    ),
    _carta(
        "X02", "Giro del Destino",
        coste_qi=2, tipo=TECNICA, renovar=4,
    ),
    _carta(
        "X03", "Filo Renacido",
        coste_qi=2, tipo=TECNICA, dano_hroe=2, renovar=3,
    ),
    _carta(
        "X04", "Loto que Renace",
        coste_qi=2, tipo=TECNICA, curar=3, renovar=3,
    ),
    _carta(
        "X05", "Sello del Eterno Retorno",
        coste_qi=2, tipo=TECNICA, escudo=2, renovar=3,
    ),
    _carta(
        "X06", "Espejo del Destino",
        coste_qi=2, tipo=TECNICA, drenar_qi_rival=1, renovar=3,
    ),
    _carta(
        "X07", "Pacto de Renovación",
        coste_qi=1, tipo=TECNICA, sacrificar_vida=2, renovar=4,
    ),
    _carta(
        "X08", "Muda del Dragón",
        coste_qi=3, tipo=TECNICA, ganar_qi=1, renovar=4,
    ),
    _carta(
        "X09", "Montaña que Cambia",
        coste_qi=2, tipo=TECNICA, escudo=3, renovar=3,
    ),
    _carta(
        "X10", "Píldora de Renacimiento",
        coste_qi=2, tipo=TECNICA, curar=2, renovar=3,
    ),
    _carta(
        "X11", "Trueno Renovador",
        coste_qi=2, tipo=TECNICA, dano_area=1, renovar=3,
    ),
    _carta(
        "X12", "Brote Nuevo",
        coste_qi=2, tipo=TECNICA, ganar_qi=1, renovar=3,
    ),
    # ── XH · Curación por porcentaje (js/06-contenido.js:41) ────────────
    _carta(
        "H01", "Caldo Nutritivo",
        coste_qi=2, tipo=TECNICA, curar=4, curar_porcentaje=12,
    ),
    _carta(
        "H02", "Píldora de Jade Restauradora",
        coste_qi=2, tipo=PILDORA, curar=5, curar_porcentaje=20, robar=1,
    ),
    _carta(
        "H03", "Píldora del Loto Dorado",
        coste_qi=3, tipo=PILDORA, curar=8, curar_porcentaje=32,
    ),
    _carta(
        "H04", "Elixir de la Médula Espiritual",
        coste_qi=5, tipo=PILDORA, curar=12, curar_porcentaje=55,
        ganar_qi=1,
    ),
    # ── XV · Agujero Negro y Samsara (js/06-contenido.js:43-44) ─────────
    _carta(
        "V01", "Susurro del Vacío",
        coste_qi=2, tipo=TECNICA, vacio_descarte=1,
    ),
    _carta(
        "V02", "Voracidad del Abismo",
        coste_qi=3, tipo=TECNICA, vacio_descarte=2, rareza_fija=2,
    ),
    _carta(
        "V03", "Ciclo del Samsara",
        coste_qi=2, tipo=TECNICA, ciclo=1, rareza_fija=2,
    ),
    _carta(
        "V04", "Eco del Vacío",
        coste_qi=2, tipo=TECNICA, abismo_traer=1, abismo_elegir=True,
        rareza_fija=3,
    ),
    _carta(
        "V05", "Resurgir del Abismo",
        coste_qi=4, tipo=TECNICA, abismo_traer=2, abismo_elegir=True,
        rareza_fija=4,
    ),
    _carta(
        "V06", "Marea del Samsara",
        coste_qi=3, tipo=TECNICA, samsara=2, rareza_fija=3,
    ),
    _carta(
        "V07", "Pozo de Reencarnación",
        coste_qi=3, tipo=TECNICA, abismo_traer=1, samsara=1,
        rareza_fija=4,
    ),
)
