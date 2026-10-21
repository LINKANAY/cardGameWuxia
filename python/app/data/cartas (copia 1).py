"""Catálogo de cartas — 235 cartas, paridad con `js/01-datos.js` (106
base) y `js/06-contenido.js` (129 v47, portadas en `cartas_v47.py`).

Cada carta se define con **nombres completos** de campo (los mismos que
`CartaData`), no con las claves crípticas del monolito. El puente con el
formato JS está en dos sitios, ambos documentados:

- `CartaData.a_js()`: serializa al formato corto del JS (lo usa el test
  de paridad contra `tests/fixtures/cartas_parity.json`).
- `CartaData.desde_js()`: parsea el formato corto (por si se cargan
  datos del monolito o fixtures).

Los efectos compuestos (`UltimoAliento`, `HabilidadActiva`,
`MejoraAliada`, `AlEntrar`) se construyen con sus nombres de campo
completos. En el original JS estos datos venían repartidos en `C`,
`AB` y varios `Object.assign`; aquí van todos juntos en la definición
de la carta, que es donde tiene sentido leerlos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .tipos import (
    AlEntrar,
    CartaData,
    HabilidadActiva,
    MejoraAliada,
    TipoCarta,
    TipoEfecto,
    UltimoAliento,
)

if TYPE_CHECKING:
    from app.engine.state import CartaJuego

# Alias locales para no repetir `TipoCarta.` en cada línea del catálogo.
TECNICA = TipoCarta.TECNICA
CRIATURA = TipoCarta.CRIATURA
PILDORA = TipoCarta.PILDORA


def _carta(
    identificador: str,
    nombre: str,
    *,
    coste_qi: int,
    tipo: TipoCarta,
    **efectos,
) -> CartaData:
    """Constructor compacto del catálogo.

    Los `**efectos` van con los nombres de campo de `CartaData`
    (p. ej. `dano_hroe=3, es_espada=True`). Un nombre de campo
    equivocado lanza `TypeError` al importar el módulo: no hay formas
    de escribir una carta mal y que pase desapercibido.
    """
    return CartaData(
        identificador=identificador,
        nombre=nombre,
        coste_qi=coste_qi,
        tipo=tipo,
        **efectos,
    )


# ---------------------------------------------------------------------------
# Catálogo completo (orden por secta/tema, como en el monolito).
# ---------------------------------------------------------------------------

_CARTAS_LISTA: tuple[CartaData, ...] = (
    # ── Espada Celestial (base) ─────────────────────────────────────────
    _carta(
        "cf", "Corte Fugaz",
        coste_qi=1, tipo=TECNICA, dano_hroe=3, es_espada=True,
    ),
    _carta(
        "ev", "Espada Voladora",
        coste_qi=2, tipo=CRIATURA, ataque=3, vida=1,
        impetu=True, ultimo_aliento=UltimoAliento(tipo=TipoEfecto.DANO_HROE, valor=1),
    ),
    _carta(
        "ld", "Luz de Espada",
        coste_qi=3, tipo=TECNICA, dano_hroe=5, es_espada=True,
    ),
    _carta(
        "ma", "Maestro de la Espada",
        coste_qi=4, tipo=CRIATURA, ataque=4, vida=3, crece=1,
    ),
    _carta(
        "te", "Tormenta de Espadas",
        coste_qi=5, tipo=TECNICA, dano_hroe=6, es_espada=True,
    ),
    # ── Loto de Jade (base) ─────────────────────────────────────────────
    _carta(
        "lc", "Loto Curativo",
        coste_qi=2, tipo=TECNICA, curar=5,
    ),
    _carta(
        "ej", "Escudo de Jade",
        coste_qi=2, tipo=TECNICA, escudo=6,
    ),
    _carta(
        "gr", "Grulla de Loto",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=5,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.CURAR, valor=2, descripcion="Curar 2"
        ),
    ),
    _carta(
        "ml", "Mar de Pétalos",
        coste_qi=3, tipo=TECNICA, curar=3, robar=1,
    ),
    _carta(
        "ab", "Abrazo Sereno",
        coste_qi=4, tipo=TECNICA, escudo=6, curar=4,
    ),
    # ── Mil Talismanes (base) ───────────────────────────────────────────
    _carta(
        "tf", "Talismán de Fuego",
        coste_qi=1, tipo=TECNICA, dano_hroe=3,
    ),
    _carta(
        "tl", "Talismán Sellador",
        coste_qi=2, tipo=TECNICA, dano_hroe=1, drenar_qi_rival=2,
    ),
    _carta(
        "fe", "Formación Espiritual",
        coste_qi=3, tipo=TECNICA, dano_area=3,
    ),
    _carta(
        "mt", "Mil Talismanes",
        coste_qi=5, tipo=TECNICA, dano_hroe=3, dano_area=3,
    ),
    _carta(
        "gd", "Guardián Talismán",
        coste_qi=2, tipo=CRIATURA, ataque=1, vida=4, provocar=True,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.DANO_HROE, valor=2),
    ),
    # ── Palacio de la Luna (base) ───────────────────────────────────────
    _carta(
        "il", "Ilusión Lunar",
        coste_qi=2, tipo=TECNICA, drenar_qi_rival=2, robar=1,
    ),
    _carta(
        "em", "Espejo Lunar",
        coste_qi=2, tipo=TECNICA, robar=2,
    ),
    _carta(
        "zl", "Zorro Lunar",
        coste_qi=2, tipo=CRIATURA, ataque=2, vida=2, robar=1,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.ROBAR, valor=1, descripcion="Robar 1"
        ),
    ),
    _carta(
        "vs", "Velo de Sombra",
        coste_qi=1, tipo=TECNICA, escudo=3,
    ),
    _carta(
        "pl", "Hechicera Lunar",
        coste_qi=4, tipo=CRIATURA, ataque=3, vida=4, drenar_qi_rival=1,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.DRENAR_QI, valor=1, descripcion="Drenar 1 Qi"
        ),
    ),
    # ── Valle de los Demonios (base) ────────────────────────────────────
    _carta(
        "sa", "Sacrificio de Sangre",
        coste_qi=0, tipo=TECNICA, sacrificar_vida=3, ganar_qi=3,
    ),
    _carta(
        "dm", "Demonio Menor",
        coste_qi=3, tipo=CRIATURA, ataque=4, vida=3,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.DANO_HROE, valor=2),
    ),
    _carta(
        "co", "Corrupción",
        coste_qi=2, tipo=TECNICA, dano_hroe=4, sacrificar_vida=1,
    ),
    _carta(
        "cd", "Cultivador Demoníaco",
        coste_qi=2, tipo=CRIATURA, ataque=3, vida=2, sacrificar_vida=2,
        robar_vida=True,
        al_entrar=AlEntrar(
            tipo=TipoEfecto.DANO_CRIATURA_AL_AZAR, valor=2
        ),
    ),
    _carta(
        "av", "Avatar Demoníaco",
        coste_qi=5, tipo=CRIATURA, ataque=6, vida=5, sacrificar_vida=2,
        robar_vida=True,
        ultimo_aliento=UltimoAliento(
            tipo=TipoEfecto.DANO_HROE, valor=4
        ),
    ),
    # ── Palacio del Dragón (base) ───────────────────────────────────────
    _carta(
        "dc", "Dragoncillo",
        coste_qi=2, tipo=CRIATURA, ataque=2, vida=2, ganar_qi=1, crece=1,
    ),
    _carta(
        "ad", "Aliento de Dragón",
        coste_qi=4, tipo=TECNICA, dano_hroe=6,
    ),
    _carta(
        "rd", "Rey Dragón Joven",
        coste_qi=6, tipo=CRIATURA, ataque=6, vida=6,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.DANO_HROE, valor=3, descripcion="Aliento 3"
        ),
    ),
    _carta(
        "pf", "Perla del Dragón",
        coste_qi=1, tipo=PILDORA, ganar_qi=2, robar=1,
    ),
    _carta(
        "fn", "Fénix Espiritual",
        coste_qi=4, tipo=CRIATURA, ataque=4, vida=3, curar=3,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.CURAR, valor=5),
    ),
    # ── Cartas neutrales ────────────────────────────────────────────────
    _carta(
        "pq", "Píldora de Qi",
        coste_qi=1, tipo=PILDORA, ganar_qi=3,
    ),
    _carta(
        "ph", "Píldora Curativa",
        coste_qi=1, tipo=PILDORA, curar=4,
    ),
    _carta(
        "gp", "Golpe Palmar",
        coste_qi=1, tipo=TECNICA, dano_hroe=2,
    ),
    _carta(
        "di", "Discípulo",
        coste_qi=1, tipo=CRIATURA, ataque=1, vida=2,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.ROBAR, valor=1),
    ),
    _carta(
        "ti", "Tigre Espiritual",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=3, crece=1,
    ),
    _carta(
        "es", "Estocada",
        coste_qi=2, tipo=TECNICA, dano_hroe=3,
    ),
    _carta(
        "ar", "Armadura Espiritual",
        coste_qi=2, tipo=TECNICA, escudo=4,
    ),
    _carta(
        "tc", "Tribulación Celestial",
        coste_qi=5, tipo=TECNICA, tribulacion=True,
    ),
    _carta(
        "mo", "Monje Errante",
        coste_qi=2, tipo=CRIATURA, ataque=2, vida=3,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.CURAR, valor=1, descripcion="Curar 1"
        ),
    ),
    # ── Cartas raras (rareza fija 2) ────────────────────────────────────
    _carta(
        "ta", "Talismán de Trueno",
        coste_qi=2, tipo=TECNICA, dano_hroe=4, rareza_fija=2,
    ),
    _carta(
        "mp", "Monje de Hierro",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=5, provocar=True,
        rareza_fija=2,
    ),
    _carta(
        "ca", "Caldero Celestial",
        coste_qi=3, tipo=TECNICA, robar=3, ganar_qi=2, rareza_fija=2,
    ),
    # ── Cartas épicas (rareza fija 3) ───────────────────────────────────
    _carta(
        "ex", "Espada Inmortal",
        coste_qi=4, tipo=TECNICA, dano_hroe=8, es_espada=True,
        rareza_fija=3,
    ),
    _carta(
        "fr", "Fénix Renacido",
        coste_qi=5, tipo=CRIATURA, ataque=5, vida=5, curar=5,
        rareza_fija=3,
    ),
    _carta(
        "lm", "Loto de los Mil Años",
        coste_qi=4, tipo=TECNICA, curar=8, escudo=4, rareza_fija=3,
    ),
    _carta(
        "pi", "Píldora Inmortal",
        coste_qi=2, tipo=PILDORA, ganar_qi=4, curar=6, robar=1,
        rareza_fija=3,
    ),
    # ── Cartas legendarias (rareza fija 4) ──────────────────────────────
    _carta(
        "se", "Soberano de la Espada",
        coste_qi=6, tipo=CRIATURA, ataque=7, vida=6, rareza_fija=4,
        al_entrar=AlEntrar(tipo=TipoEfecto.DANO_CRIATURA_AL_AZAR, valor=3),
    ),
    _carta(
        "dt", "Dragón de las Nueve Nubes",
        coste_qi=7, tipo=CRIATURA, ataque=8, vida=8, rareza_fija=4,
        habilidad_activa=HabilidadActiva(
            coste_qi=3, tipo=TipoEfecto.DANO_HROE, valor=5, descripcion="Rayo 5"
        ),
    ),
    _carta(
        "gh", "Emperatriz Fantasma",
        coste_qi=6, tipo=CRIATURA, ataque=5, vida=6, drenar_qi_rival=2,
        rareza_fija=4,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.DRENAR_QI, valor=2, descripcion="Drenar 2 Qi"
        ),
    ),
    # ── Cartas celestiales (rareza fija 5) ──────────────────────────────
    _carta(
        "ac", "Ascensión Celestial",
        coste_qi=7, tipo=TECNICA, dano_hroe=12, curar=6, rareza_fija=5,
    ),
    _carta(
        "pr", "Bestia Primordial",
        coste_qi=8, tipo=CRIATURA, ataque=10, vida=10, rareza_fija=5,
        crece=2,
    ),
    # ── Extensión Espada Celestial ──────────────────────────────────────
    _carta(
        "qe", "Qi de Espada",
        coste_qi=1, tipo=TECNICA, dano_hroe=2, es_espada=True, robar=1,
    ),
    _carta(
        "dh", "Danza de Hojas",
        coste_qi=3, tipo=TECNICA, dano_hroe=3, es_espada=True, dano_area=2,
    ),
    _carta(
        "ee", "Espadachín Errante",
        coste_qi=3, tipo=CRIATURA, ataque=4, vida=2, impetu=True, crece=1,
    ),
    _carta(
        "cp", "Cielo Partido",
        coste_qi=6, tipo=TECNICA, dano_hroe=9, es_espada=True,
    ),
    # ── Extensión Loto de Jade ──────────────────────────────────────────
    _carta(
        "bl", "Brisa de Loto",
        coste_qi=1, tipo=TECNICA, curar=2, robar=1,
    ),
    _carta(
        "mj", "Monje del Loto",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=6, curar=2,
        provocar=True,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.ESCUDO, valor=3, descripcion="Escudo 3"
        ),
    ),
    _carta(
        "ep", "Estanque Sereno",
        coste_qi=3, tipo=TECNICA, escudo=5, curar=3,
    ),
    _carta(
        "dl", "Diosa del Loto Blanco",
        coste_qi=6, tipo=CRIATURA, ataque=4, vida=8, curar=4,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.CURAR, valor=3, descripcion="Curar 3"
        ),
    ),
    # ── Extensión Mil Talismanes ────────────────────────────────────────
    _carta(
        "th", "Talismán de Hielo",
        coste_qi=2, tipo=TECNICA, dano_hroe=2, drenar_qi_rival=1,
    ),
    _carta(
        "bt", "Barrera de Talismanes",
        coste_qi=3, tipo=TECNICA, escudo=7,
    ),
    _carta(
        "ft", "Formación del Trueno",
        coste_qi=4, tipo=TECNICA, dano_area=4,
    ),
    _carta(
        "gc", "Gran Formación Celestial",
        coste_qi=6, tipo=TECNICA, dano_area=5, dano_hroe=4,
    ),
    # ── Extensión Palacio de la Luna ────────────────────────────────────
    _carta(
        "ra", "Reflejo de Agua",
        coste_qi=1, tipo=TECNICA, robar=1, escudo=1,
    ),
    _carta(
        "sl", "Sombra Lunar",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=3, drenar_qi_rival=1,
    ),
    _carta(
        "ec", "Eclipse",
        coste_qi=4, tipo=TECNICA, drenar_qi_rival=3, dano_hroe=3,
    ),
    _carta(
        "dg", "Diosa de la Luna",
        coste_qi=6, tipo=CRIATURA, ataque=5, vida=7, robar=1,
    ),
    # ── Extensión Valle de los Demonios ─────────────────────────────────
    _carta(
        "sd", "Sed de Sangre",
        coste_qi=1, tipo=TECNICA, dano_hroe=3, sacrificar_vida=1,
    ),
    _carta(
        "pd", "Pacto Demoníaco",
        coste_qi=2, tipo=TECNICA, ganar_qi=2, robar=1, sacrificar_vida=2,
    ),
    _carta(
        "ba", "Bestia del Abismo",
        coste_qi=4, tipo=CRIATURA, ataque=5, vida=4, sacrificar_vida=1,
        robar_vida=True,
    ),
    _carta(
        "sn", "Señor Demonio",
        coste_qi=7, tipo=CRIATURA, ataque=8, vida=6, sacrificar_vida=3,
        ultimo_aliento=UltimoAliento(tipo=TipoEfecto.DANO_HROE, valor=5),
    ),
    # ── Extensión Palacio del Dragón ────────────────────────────────────
    _carta(
        "eg", "Escama de Jade",
        coste_qi=2, tipo=TECNICA, escudo=4, ganar_qi=1,
    ),
    _carta(
        "sf", "Serpiente de Fuego",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=4,
        habilidad_activa=HabilidadActiva(
            coste_qi=1, tipo=TipoEfecto.DANO_HROE, valor=2, descripcion="Llama 2"
        ),
    ),
    _carta(
        "dy", "Dragón de Trueno",
        coste_qi=5, tipo=CRIATURA, ataque=5, vida=5,
        al_entrar=AlEntrar(tipo=TipoEfecto.DANO_CRIATURA_AL_AZAR, valor=3),
    ),
    _carta(
        "sb", "Soberano Dragón",
        coste_qi=7, tipo=CRIATURA, ataque=8, vida=8, ganar_qi=2,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.DANO_HROE, valor=3, descripcion="Fuego 3"
        ),
    ),
    # ── Extensión alquimia / misc ───────────────────────────────────────
    _carta(
        "aa", "Aprendiz de Alquimia",
        coste_qi=1, tipo=CRIATURA, ataque=1, vida=1, robar=1,
    ),
    _carta(
        "pg", "Píldora de Fuego",
        coste_qi=1, tipo=PILDORA, dano_hroe=3,
    ),
    _carta(
        "lb", "Lobo Espiritual",
        coste_qi=2, tipo=CRIATURA, ataque=3, vida=2, impetu=True,
    ),
    _carta(
        "as", "Anciano Sabio",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=4, robar=1,
    ),
    _carta(
        "md", "Meditación Profunda",
        coste_qi=2, tipo=TECNICA, ganar_qi=3, robar=1,
    ),
    _carta(
        "aj", "Armadura de Jade",
        coste_qi=3, tipo=TECNICA, escudo=8,
    ),
    _carta(
        "gi", "Gran Inmortal Errante",
        coste_qi=5, tipo=CRIATURA, ataque=5, vida=6,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.ROBAR, valor=2, descripcion="Robar 2"
        ),
    ),
    _carta(
        "pn", "Píldora de Nueve Revoluciones",
        coste_qi=3, tipo=PILDORA, curar=8, ganar_qi=2,
    ),
    _carta(
        "td", "Tribulación del Dao",
        coste_qi=8, tipo=TECNICA, dano_area=6, dano_hroe=8, rareza_fija=5,
    ),
    _carta(
        "ia", "Inmortal Ascendido",
        coste_qi=8, tipo=CRIATURA, ataque=9, vida=9, curar=5,
        rareza_fija=5,
        habilidad_activa=HabilidadActiva(
            coste_qi=2, tipo=TipoEfecto.CURAR, valor=4, descripcion="Curar 4"
        ),
    ),
    # ── Efectos v47+: daño a criatura, congelar, mejorar aliada ────────
    _carta(
        "ce", "Corte Certero",
        coste_qi=2, tipo=TECNICA, dano_criatura=4, es_espada=True,
    ),
    _carta(
        "ae", "Aura de Espada",
        coste_qi=2, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=2, vida=0), es_espada=True,
    ),
    _carta(
        "ru", "Ruptura de Filo",
        coste_qi=4, tipo=TECNICA, dano_criatura=7, es_espada=True,
    ),
    _carta(
        "bn", "Bendición del Loto",
        coste_qi=2, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=1, vida=3),
    ),
    _carta(
        "rl", "Raíces de Loto",
        coste_qi=3, tipo=TECNICA, dano_criatura=2, congelar=True,
    ),
    _carta(
        "gl", "Guardiana del Loto",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=5, provocar=True,
    ),
    _carta(
        "tn", "Talismán Inmovilizador",
        coste_qi=2, tipo=TECNICA, dano_criatura=1, congelar=True,
    ),
    _carta(
        "sg", "Sello de Muerte",
        coste_qi=4, tipo=TECNICA, dano_criatura=6,
    ),
    _carta(
        "mg", "Muralla de Talismanes",
        coste_qi=3, tipo=CRIATURA, ataque=1, vida=7, provocar=True,
    ),
    _carta(
        "ei", "Espejismo",
        coste_qi=2, tipo=TECNICA, dano_criatura=2, congelar=True,
    ),
    _carta(
        "ls", "Lágrima de Luna",
        coste_qi=3, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=2, vida=2),
    ),
    _carta(
        "vn", "Velo Nocturno",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=2, impetu=True,
    ),
    _carta(
        "ap", "Alma Prestada",
        coste_qi=3, tipo=TECNICA, dano_criatura=5, sacrificar_vida=1,
    ),
    _carta(
        "cn", "Colmillos Sedientos",
        coste_qi=3, tipo=CRIATURA, ataque=3, vida=3, robar_vida=True,
    ),
    _carta(
        "rk", "Rey de Sangre",
        coste_qi=5, tipo=CRIATURA, ataque=5, vida=5, robar_vida=True,
        crece=1,
    ),
    _carta(
        "gz", "Garra del Dragón",
        coste_qi=3, tipo=TECNICA, dano_criatura=5,
    ),
    _carta(
        "ed", "Escamas Doradas",
        coste_qi=2, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=0, vida=4),
    ),
    _carta(
        "cb", "Cría Rapaz",
        coste_qi=2, tipo=CRIATURA, ataque=2, vida=2, impetu=True,
    ),
    _carta(
        "tp", "Trampa Espiritual",
        coste_qi=2, tipo=TECNICA, dano_criatura=3,
    ),
    _carta(
        "bc", "Bendición Celestial",
        coste_qi=3, tipo=TECNICA,
        mejorar_aliada=MejoraAliada(ataque=2, vida=2), curar=2,
    ),
    _carta(
        "gu", "Guardián de Piedra",
        coste_qi=3, tipo=CRIATURA, ataque=2, vida=6, provocar=True,
    ),
)

#: Catálogo completo de cartas (id → `CartaData`).
CARTAS: dict[str, CartaData] = {
    carta.identificador: carta for carta in _CARTAS_LISTA
}

# Extensión v47: los 129 ids de `js/06-contenido.js` (NS/XC/XF/XR/XH/XV).
# El import va aquí, al final de la definición de CARTAS, porque
# `cartas_v47` necesita `_carta` y este módulo necesita `_CARTAS_V47`:
# con el import tardío el módulo auxiliar se resuelve contra
# `app.data.cartas` ya cargado y no hay ciclo (ver su docstring).
from .cartas_v47 import _CARTAS_V47  # noqa: E402

CARTAS.update({carta.identificador: carta for carta in _CARTAS_V47})


# --- Constantes de rareza / mercado (js/01-datos.js RN/RC; js/03 RP) -------

#: Nombres de rareza por índice 0–5 (`RN` del JS).
RAREZAS: tuple[str, ...] = (
    "Común",
    "Poco común",
    "Rara",
    "Épica",
    "Legendaria",
    "Celestial",
)

#: Colores hex de rareza por índice (`RC` del JS).
COLOR_RAREZA: tuple[str, ...] = (
    "#aab8b2",
    "#6cc4a1",
    "#5aa0e8",
    "#b070e0",
    "#e8a23a",
    "#ff6a6a",
)

#: Precio de compra en piedras espirituales por rareza (`RP` de `js/03`).
PRECIO_RAREZA: tuple[int, ...] = (6, 12, 24, 45, 90, 180)

#: Tabla de rareza por coste (`rar` del JS: `[0,0,1,2,3,3,4,4,5][min(c,8)]`).
_TABLA_RAREZA_POR_COSTE: tuple[int, ...] = (0, 0, 1, 2, 3, 3, 4, 4, 5)

#: Cartas neutrales del mazo base (`NEU` del JS): las 9 de
#: `js/01-datos.js:51` más las que `js/06-contenido.js` empuja al
#: final de sus bucles (Y21, X01, H01, H02, V01, V02, V03).
CARTAS_NEUTRALES: tuple[str, ...] = (
    "pq", "ph", "gp", "di", "ti", "es", "ar", "tc", "mo",
    "Y21", "X01", "H01", "H02", "V01", "V02", "V03",
)


def rareza_de(carta: CartaData) -> int:
    """Rareza de una carta (índice 0–5).

    Puerto de `rar(c)` en `js/01-datos.js`: si la carta tiene rareza
    fija, esa manda; si no, se mira la tabla por coste
    `[0,0,1,2,3,3,4,4,5][min(coste, 8)]`.

    Args:
        carta: definición de la carta.

    Returns:
        Índice de rareza (0=Común … 5=Celestial).
    """
    if carta.rareza_fija is not None:
        return carta.rareza_fija
    return _TABLA_RAREZA_POR_COSTE[min(carta.coste_qi, 8)]


def cartas_de_rareza(rareza: int) -> list[str]:
    """Ids de cartas de una rareza, excluyendo reliquias (`byR` del JS).

    Args:
        rareza: índice 0–5.

    Returns:
        Lista de ids en orden de inserción del catálogo.
    """
    return [
        ident
        for ident, carta in CARTAS.items()
        if rareza_de(carta) == rareza and not carta.reliquia
    ]


def crear_carta(identificador: str) -> CartaJuego:
    """Instancia jugable de una carta (`mk(id)` del JS).

    Delegado a `app.engine.state.crear_carta_juego` (import perezoso
    para no crear un ciclo de imports entre `data` y `engine`).
    """
    from app.engine.state import crear_carta_juego

    return crear_carta_juego(identificador)
