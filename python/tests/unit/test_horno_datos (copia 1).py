"""Paridad de las constantes del Horno con `js/11-horno.js`.

Cada aserción cita la línea del monolito de la que sale el valor
escrito a mano. Si el JS cambia, este test falla y obliga a decidir si
el backend debe seguirlo.
"""

from __future__ import annotations

from typing import ClassVar

from app.data.hierbas import (
    CALIDADES,
    CFG,
    HIERBA,
    HIERBAS,
    INVENTARIO_INICIAL,
    MENSAJES_FALLO,
    ORDEN_CALIDAD,
    TIPOS,
    clave_pildora,
    desde_horno,
    nuevo_horno,
    parsear_pildora,
)


class TestCfg:
    """`CFG` de js/11-horno.js:29-66 (literales, sin redondeos)."""

    def test_exito(self):
        # líneas 31-38
        assert CFG["EXITO_BASE"] == 30
        assert CFG["EXITO_MIN"] == 5
        assert CFG["EXITO_MAX"] == 95
        assert CFG["EXITO_POR_REINO"] == 1
        assert CFG["BONO_ARMONIA"] == 5
        assert CFG["PENA_DISCORDIA"] == 6
        assert CFG["MIN_HIERBAS"] == 2
        assert CFG["MAX_HIERBAS"] == 4

    def test_calidad(self):
        # líneas 41-45
        assert CFG["UMBRALES_CALIDAD"] == {"media": 7, "alta": 13, "suprema": 20}
        assert CFG["BONO_ARMONIA_CALIDAD"] == 2
        assert CFG["PESO_MARGEN"] == 3
        assert CFG["RUIDO_CALIDAD"] == 4
        assert CFG["PROB_PERFECTA"] == 0.08

    def test_curacion(self):
        # líneas 48-50
        assert CFG["CURA_POR_CALIDAD"] == {
            "baja": 12,
            "media": 25,
            "alta": 40,
            "suprema": 65,
        }
        assert CFG["MULT_PERFECTA"] == 1.25
        assert CFG["CURA_DESECHO_PCT"] == 1

    def test_fallo(self):
        # líneas 53-55
        assert CFG["DANIO_FALLO_PCT"] == (6, 14)
        assert CFG["FACTOR_RIESGO"] == 0.5
        assert CFG["PUEDE_MATAR"] is False

    def test_botin(self):
        # líneas 58-61
        assert CFG["BOTIN_ACTIVO"] is True
        assert CFG["BOTIN_VICTORIA"] == (1, 2)
        assert CFG["BOTIN_BONUS_JEFE"] == 1
        assert CFG["BOTIN_RAREZA_POR_DIF"] == 0.25

    def test_arranque(self):
        # líneas 64-65
        assert CFG["DURACION_MS"] == 900
        assert CFG["INVENTARIO_INICIAL"] == {
            "hs": 6,
            "rj": 4,
            "hn": 3,
            "ff": 2,
            "ll": 2,
            "rd": 2,
            "gm": 1,
            "lu": 1,
            "hv": 1,
        }
        assert CFG["INVENTARIO_INICIAL"] == INVENTARIO_INICIAL


class TestHierbas:
    """`HIERBAS` de js/11-horno.js:81-93 (tabla literal)."""

    TABLA: ClassVar[dict[str, tuple]] = {
        # id: (nombre, glifo, rareza, exito, calidad, afinidad, peso)
        "hs": ("Hierba Espiritual", "灵", 0, 6, 1, "heal", 40),
        "rj": ("Raíz de Jade Verde", "玉", 0, 4, 2, "heal", 30),
        "hn": ("Hongo de Niebla", "雾", 0, 3, 2, "shield", 24),
        "ff": ("Fruto de Escarcha", "霜", 1, 5, 3, "ice", 14),
        "rd": ("Rocío del Amanecer", "露", 1, 4, 3, "draw", 14),
        "ll": ("Loto Carmesí", "莲", 1, 2, 4, "gold", 12),
        "hv": ("Hongo Sombrío (veneno)", "毒", 1, -8, 7, None, 10),
        "gm": ("Ginseng de Mil Años", "参", 2, 10, 4, "heal", 6),
        "lu": ("Esencia de Luz Lunar", "月", 2, 4, 6, "qi", 6),
        "ed": ("Escama de Dragón Molida", "龙", 3, 8, 7, "gold", 3),
        "nf": ("Núcleo de Fénix", "凤", 4, 15, 9, "gold", 1),
    }

    def test_orden_y_ids(self):
        assert [h.identificador for h in HIERBAS] == [
            "hs", "rj", "hn", "ff", "rd", "ll", "hv", "gm", "lu", "ed", "nf",
        ]

    def test_valores(self):
        assert len(HIERBAS) == len(self.TABLA)
        for hierba in HIERBAS:
            esperado = self.TABLA[hierba.identificador]
            assert (
                hierba.nombre,
                hierba.glifo,
                hierba.rareza,
                hierba.exito,
                hierba.calidad,
                hierba.afinidad,
                hierba.peso,
            ) == esperado

    def test_indice_por_id(self):
        assert set(HIERBA) == set(self.TABLA)


class TestCalidadesTiposMensajes:
    def test_calidades(self):
        # CALIDADES de js/11-horno.js:99-106
        assert set(CALIDADES) == {
            "fallida", "baja", "media", "alta", "suprema", "perfecta",
        }
        assert CALIDADES["fallida"].nombre == "Desecho"
        assert CALIDADES["fallida"].clase == ""
        assert CALIDADES["baja"].clase == "r1"
        assert CALIDADES["media"].clase == "r2"
        assert CALIDADES["alta"].clase == "r3"
        assert CALIDADES["suprema"].clase == "r4"
        assert CALIDADES["perfecta"].nombre == "Suprema ✦ Perfecta"
        assert CALIDADES["perfecta"].clase == "r5"
        # ORDEN_CALIDAD, línea 107
        assert ORDEN_CALIDAD == (
            "perfecta", "suprema", "alta", "media", "baja", "fallida",
        )

    def test_tipos(self):
        # TIPOS de js/11-horno.js:113-121 (clase, nombre, mult)
        assert set(TIPOS) == {
            "heal", "gold", "qi", "draw", "shield", "ice", "waste",
        }
        assert (TIPOS["heal"].clase, TIPOS["heal"].mult) == ("heal", 1.00)
        assert (TIPOS["gold"].clase, TIPOS["gold"].mult) == ("gold", 0.90)
        assert TIPOS["qi"].mult == 0.75
        assert TIPOS["draw"].mult == 0.75
        assert TIPOS["shield"].mult == 0.75
        assert TIPOS["ice"].mult == 0.75
        assert (TIPOS["waste"].clase, TIPOS["waste"].mult) == ("waste", 0)
        assert TIPOS["heal"].nombre == "Restauradora"
        assert TIPOS["gold"].nombre == "Dorada"

    def test_mensajes_fallo(self):
        # MENSAJES_FALLO de js/11-horno.js:123-129 (orden literal)
        assert MENSAJES_FALLO == (
            "El Qi del horno se desborda y te golpea el pecho.",
            "Las hierbas se repelen: una onda de energía te desgarra "
            "los meridianos.",
            "El caldero ruge, el humo se vuelve negro y la reacción "
            "te quema las manos.",
            "La llama se vuelve contra ti: el fuego te muerde el dantian.",
            "Una grieta recorre el horno y el Qi inestable te lanza "
            "hacia atrás.",
        )


class TestClavesYPersistencia:
    def test_clave_pildora(self):
        # claveP de js/11-horno.js:278
        assert clave_pildora("heal", "media") == "heal.media"
        assert clave_pildora("gold", "perfecta") == "gold.perfecta"
        # el desecho siempre es waste.fallida (ignora la calidad)
        assert clave_pildora("waste", "fallida") == "waste.fallida"
        assert clave_pildora("waste", "perfecta") == "waste.fallida"

    def test_parsear_pildora(self):
        # parseP de js/11-horno.js:279
        assert parsear_pildora("heal.media") == ("heal", "media")
        assert parsear_pildora("waste.fallida") == ("waste", "fallida")
        assert parsear_pildora("roto") is None

    def test_nuevo_horno_inventario_inicial(self):
        # estadoNuevo() de js/11-horno.js:262-264
        estado = nuevo_horno()
        assert estado == {
            "hierbas": dict(INVENTARIO_INICIAL),
            "pildoras": {},
            "refinadas": 0,
            "fallos": 0,
        }
        # copias independientes: mutar una no toca el catálogo
        estado["hierbas"]["hs"] = 99
        assert nuevo_horno()["hierbas"]["hs"] == 6

    def test_desde_horno_filtra_como_cargar(self):
        # cargar() de js/11-horno.js:265-275
        assert desde_horno(None) == nuevo_horno()
        assert desde_horno({}) == nuevo_horno()
        # `d.hierbas = {}` es truthy en JS: se conserva vacío (no resetea)
        assert desde_horno({"hierbas": {}}) == {
            "hierbas": {},
            "pildoras": {},
            "refinadas": 0,
            "fallos": 0,
        }
        estado = desde_horno(
            {
                "hierbas": {"hs": 3, "zz": 5, "hv": 0, "nf": -2, "lu": "2"},
                "pildoras": {"heal.media": 4},
                "refinadas": 7.9,
                "fallos": "3",
                "clave_rara": {"x": 1},
            }
        )
        assert estado["hierbas"] == {"hs": 3, "lu": 2}
        assert estado["pildoras"] == {"heal.media": 4}
        assert estado["refinadas"] == 7
        assert estado["fallos"] == 3
