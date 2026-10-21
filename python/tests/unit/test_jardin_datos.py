"""Datos del Jardín Medicinal: CFG, catálogos y sanitizado de estado.

Módulo nuevo (sin monolito), así que aquí no hay citas de líneas del
JS: lo que se fija es la decisión de diseño acordada. Si alguien
toca `data/jardin.py` y cambia un número, este test debe saltar.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from app.data.jardin import (
    CFG,
    CLAVE_FORMACIONES,
    CLAVE_JARDIN,
    CLAVE_SEMILLAS,
    FORMACION,
    FORMACIONES,
    MEJORAS,
    descuento_formacion,
    desde_formaciones,
    desde_jardin,
    desde_semillas,
    duracion_base,
    nuevo_jardin,
    reino_minimo,
    rendimiento_base,
    semillas_de_especie,
)


class TestCfg:
    def test_crecimiento(self):
        # 2 / 6 / 12 / 25 / 45 minutos por rareza 0..4
        assert CFG["DURACION_POR_RAREZA"] == {
            0: 120_000,
            1: 360_000,
            2: 720_000,
            3: 1_500_000,
            4: 2_700_000,
        }
        assert CFG["RENDIMIENTO_POR_RAREZA"] == {0: 1, 1: 1, 2: 2, 3: 2, 4: 3}
        assert CFG["DESCUENTO_POR_RAREZA"] == {
            0: 0.05,
            1: 0.10,
            2: 0.15,
            3: 0.20,
            4: 0.30,
        }
        assert CFG["REDUCCION_PIEDRA"] == 0.05
        assert CFG["UMBRAL_LISTO_MS"] == 1000

    def test_desbloqueo_y_arranque(self):
        assert CFG["REINO_POR_RAREZA"] == {0: 0, 1: 1, 2: 3, 3: 5, 4: 7}
        assert CFG["SEMILLAS_INICIALES"] == {"hs": 2}
        assert CFG["CASILLAS_BASE"] == 4

    def test_botin_boticario(self):
        assert CFG["BOTIN_SEMILLAS_MIN"] == 1
        assert CFG["BOTIN_SEMILLAS_MAX"] == 2
        assert CFG["BOTIN_PROB_SEGUNDA"] == 0.35
        assert CFG["BOTIN_INCREM_POR_DIF"] == 0.05
        assert CFG["BOTIN_PROB_FORMACION"] == 0.30
        assert CFG["PESO_RAREZA_POR_DIF"] == 0.25
        assert CFG["FORMACIONES_PESO"] == {0: 40, 1: 25, 2: 12, 3: 5, 4: 2}
        assert CFG["BOTIN_MAT_H_BASE"] == 2
        assert CFG["BOTIN_MAT_H_DIF"] == 1
        assert CFG["BOTIN_MAT_P_BASE"] == 1
        assert CFG["BOTIN_MAT_N_DIF"] == 3
        assert CFG["REGALO_FORMACION_DIVISOR"] == 3

    def test_claves_de_guardado(self):
        # Claves nuevas del xcg3 backend (junto a `xn` del horno).
        assert (CLAVE_JARDIN, CLAVE_SEMILLAS, CLAVE_FORMACIONES) == (
            "jdn",
            "sd",
            "fg",
        )


class TestFormaciones:
    TABLA: ClassVar[list[tuple]] = [
        # id, nombre, glifo, rareza
        ("fc1", "Círculo de Rocío", "露", 0),
        ("fc2", "Tierra Fértil", "壤", 0),
        ("fc3", "Sello de Raíces", "根", 1),
        ("fc4", "Rueda de las Cuatro Estaciones", "四", 2),
        ("fc5", "Sello del Jardín Celeste", "园", 3),
        ("fc6", "Dao de la Cosecha Eterna", "收", 4),
    ]

    def test_tabla(self):
        assert [
            (f.identificador, f.nombre, f.glifo, f.rareza)
            for f in FORMACIONES
        ] == self.TABLA

    def test_indice_y_descripciones(self):
        assert set(FORMACION) == {f.identificador for f in FORMACIONES}
        assert all(f.descripcion for f in FORMACIONES)

    def test_todas_las_rarezas_cubiertas(self):
        assert {f.rareza for f in FORMACIONES} == {0, 1, 2, 3, 4}

    def test_descuento_formacion(self):
        assert descuento_formacion(None) == 0.0
        assert descuento_formacion("zz") == 0.0
        assert descuento_formacion("fc1") == 0.05
        assert descuento_formacion("fc3") == 0.10
        assert descuento_formacion("fc4") == 0.15
        assert descuento_formacion("fc6") == 0.30


class TestMejoras:
    def test_escalera(self):
        assert [m.casillas for m in MEJORAS] == [4, 6, 9, 12]
        assert [m.nivel for m in MEJORAS] == [0, 1, 2, 3]

    def test_costes_y_reinos(self):
        assert MEJORAS[0].coste == {}
        assert MEJORAS[0].reino_min == 0
        assert MEJORAS[1].coste == {"h": 15, "n": 5, "p": 5}
        assert MEJORAS[1].reino_min == 2
        assert MEJORAS[2].coste == {"h": 30, "n": 15, "p": 15}
        assert MEJORAS[2].reino_min == 5
        assert MEJORAS[3].coste == {"h": 60, "n": 30, "p": 30}
        assert MEJORAS[3].reino_min == 8


class TestHelpersDeCatalogo:
    def test_duracion_por_rareza(self):
        assert duracion_base("hs") == 120_000  # rareza 0
        assert duracion_base("ff") == 360_000  # rareza 1
        assert duracion_base("gm") == 720_000  # rareza 2
        assert duracion_base("ed") == 1_500_000  # rareza 3
        assert duracion_base("nf") == 2_700_000  # rareza 4

    def test_desconocida_lanza(self):
        with pytest.raises(KeyError):
            duracion_base("zz")
        with pytest.raises(KeyError):
            rendimiento_base("zz")
        with pytest.raises(KeyError):
            reino_minimo("zz")

    def test_rendimiento_y_reino(self):
        assert rendimiento_base("hs") == 1
        assert rendimiento_base("gm") == 2
        assert rendimiento_base("nf") == 3
        assert reino_minimo("hs") == 0
        assert reino_minimo("ff") == 1
        assert reino_minimo("gm") == 3
        assert reino_minimo("ed") == 5
        assert reino_minimo("nf") == 7

    def test_semillas_de_especie(self):
        agrupadas = semillas_de_especie()
        assert agrupadas[0] == ["hs", "rj", "hn"]
        assert agrupadas[1] == ["ff", "rd", "ll", "hv"]
        assert agrupadas[2] == ["gm", "lu"]
        assert agrupadas[3] == ["ed"]
        assert agrupadas[4] == ["nf"]
        assert sum(len(v) for v in agrupadas.values()) == 11


class TestEstado:
    def test_nuevo_jardin(self):
        estado = nuevo_jardin()
        assert estado == {
            "nivel": 0,
            "casillas": [None, None, None, None],
            "formacion": None,
        }
        # copias independientes: mutar una no contamina la siguiente
        estado["casillas"][0] = {"planta": "hs", "siembra": 1, "reducido": 0}
        assert nuevo_jardin()["casillas"] == [None, None, None, None]

    def test_desde_jardin_basura(self):
        assert desde_jardin(None) == nuevo_jardin()
        assert desde_jardin("rip") == nuevo_jardin()
        assert desde_jardin({}) == nuevo_jardin()

    def test_desde_jardin_nivel_y_tamano(self):
        # nivel fuera de rango se recorta a 3 (12 casillas)
        estado = desde_jardin({"nivel": 99, "casillas": []})
        assert estado["nivel"] == 3
        assert len(estado["casillas"]) == 12
        # nivel negativo → base
        assert desde_jardin({"nivel": -1})["nivel"] == 0
        # casillas de más se recortan al tamaño del nivel
        estado = desde_jardin({"nivel": 1, "casillas": [None] * 20})
        assert len(estado["casillas"]) == 6
        # casillas de menos se rellenan
        estado = desde_jardin({"nivel": 2, "casillas": [None]})
        assert estado["casillas"] == [None] * 9
        # casillas no lista → vacías
        assert desde_jardin({"casillas": "hola"})["casillas"] == [None] * 4

    def test_desde_jardin_filtra_casillas(self):
        estado = desde_jardin(
            {
                "nivel": 3,
                "casillas": [
                    {"planta": "hs", "siembra": 1700000000000, "reducido": 5},
                    {"planta": "zz", "siembra": 1},
                    {"planta": "rj", "siembra": -1},
                    {"planta": "hn"},  # sin siembra
                    "no-soy-casilla",
                    {"planta": "gm", "siembra": 10, "reducido": -4},
                ],
            }
        )
        assert estado["casillas"][0] == {
            "planta": "hs",
            "siembra": 1_700_000_000_000,
            "reducido": 5,
        }
        assert estado["casillas"][1] is None  # planta desconocida
        assert estado["casillas"][2] is None  # siembra negativa
        assert estado["casillas"][3] is None  # sin siembra
        assert estado["casillas"][4] is None  # no es dict
        # reducido inválido se rescata a 0
        assert estado["casillas"][5] == {
            "planta": "gm",
            "siembra": 10,
            "reducido": 0,
        }

    def test_desde_jardin_formacion(self):
        assert desde_jardin({"formacion": "fc6"})["formacion"] == "fc6"
        assert desde_jardin({"formacion": "zz"})["formacion"] is None
        assert desde_jardin({"formacion": 7})["formacion"] is None

    def test_desde_semillas(self):
        # clave ausente o corrupta → semillas iniciales
        assert desde_semillas(None) == {"hs": 2}
        assert desde_semillas(["no"]) == {"hs": 2}
        # clave presente (aunque vacía) → se respeta
        assert desde_semillas({}) == {}
        assert desde_semillas({"hs": 3, "zz": 5, "hv": 0, "nf": -2, "lu": "2"}) == {
            "hs": 3,
            "lu": 2,
        }

    def test_desde_formaciones(self):
        assert desde_formaciones(None) == {}
        assert desde_formaciones({"fc1": 2, "zz": 9, "fc6": 0, "fc2": "1"}) == {
            "fc1": 2,
            "fc2": 1,
        }
