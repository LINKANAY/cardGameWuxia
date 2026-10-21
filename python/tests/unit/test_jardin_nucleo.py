"""Núcleo del Jardín Medicinal: tiempos, piedras espirituales y botines.

Reloj simulado como epoch ms y `rng` inyectado en todos los sorteos
(con el contrato de `Math.random`), igual que `test_horno_nucleo.py`.
"""

from __future__ import annotations

import math

import pytest

from app.data.hierbas import HIERBAS
from app.data.jardin import FORMACIONES, duracion_base
from app.engine.jardin import (
    aplicar_piedras,
    botin_boticario,
    coste_max_piedras,
    desbloqueada,
    duracion_efectiva,
    esta_listo,
    progreso,
    regalo_ascenso,
    rendimiento,
    restante_ms,
    siguiente_mejora,
)

AHORA = 1_760_000_000_000
HS = {"planta": "hs", "siembra": AHORA, "reducido": 0}
NF = {"planta": "nf", "siembra": AHORA, "reducido": 0}


def _fijo(valor: float):
    return lambda: valor


def _varios(*valores: float):
    """rng que devuelve cada valor en orden de llamada."""
    it = iter(valores)
    return lambda: next(it)


class TestDuracionEfectiva:
    def test_sin_formacion_es_la_base(self):
        assert duracion_efectiva("hs", None) == duracion_base("hs")
        assert duracion_efectiva("nf", None) == 2_700_000

    def test_descuento_de_la_formacion(self):
        # fc1 = −5 % → ceil(120000 × 0.95)
        assert duracion_efectiva("hs", "fc1") == 114_000
        # fc6 = −30 % sobre el jardín más largo
        assert duracion_efectiva("nf", "fc6") == 1_890_000
        # fc4 = −15 % → ceil(720000 × 0.85) … y fc3 (rareza 1) = −10 %
        assert duracion_efectiva("gm", "fc4") == 612_000
        assert duracion_efectiva("gm", "fc3") == 648_000

    def test_formacion_desconocida_no_descuenta(self):
        assert duracion_efectiva("hs", "zz") == duracion_base("hs")
        assert duracion_efectiva("hs", "") == duracion_base("hs")


class TestProgreso:
    def test_recien_sembrada(self):
        assert restante_ms(HS, AHORA, None) == 120_000
        assert progreso(HS, AHORA, None) == 0.0
        assert not esta_listo(HS, AHORA, None)

    def test_a_mitad_de_camino(self):
        assert restante_ms(HS, AHORA + 60_000, None) == 60_000
        assert progreso(HS, AHORA + 60_000, None) == 0.5

    def test_formacion_acelera_las_en_curso(self):
        # Con fc1 (−5 %) la misma plantación rinde 11 s antes
        assert restante_ms(HS, AHORA, "fc1") == 114_000
        assert progreso(HS, AHORA, "fc1") == 0.0

    def test_cumplido(self):
        tras = AHORA + 120_000
        assert restante_ms(HS, tras, None) == 0
        assert progreso(HS, tras, None) == 1.0
        assert esta_listo(HS, tras, None)

    def test_umbral_de_un_segundo(self):
        # resto 1001 ms → aún no; 1000 ms → sí
        assert not esta_listo(HS, AHORA + 118_999, None)
        assert esta_listo(HS, AHORA + 119_000, None)
        # y no puede bajar de 0
        assert restante_ms(HS, AHORA + 10**9, None) == 0
        assert progreso(HS, AHORA + 10**9, None) == 1.0

    def test_casilla_vacia(self):
        assert restante_ms(None, AHORA, "fc6") == 0
        assert progreso(None, AHORA, "fc6") == 0.0
        assert esta_listo(None, AHORA, None) is False

    def test_planta_mas_larga(self):
        assert restante_ms(NF, AHORA, None) == 2_700_000
        assert restante_ms(NF, AHORA, "fc6") == 1_890_000


class TestPiedrasEspirituales:
    def test_una_piedra_quita_el_5_por_ciento(self):
        resultado = aplicar_piedras(HS, 1, AHORA, None)
        assert resultado == {
            "reducido": 6_000,
            "restante_ms": 114_000,
            "gastadas": 1,
        }

    def test_acumulable_y_exacto(self):
        resultado = aplicar_piedras(HS, 2, AHORA, None)
        # 120000 × 0.95² → ceil = 108300
        assert resultado["restante_ms"] == 108_300
        assert resultado["gastadas"] == 2
        assert resultado["reducido"] == 11_700

    def test_golpe_unico_hasta_dejarla_lista(self):
        resultado = aplicar_piedras(NF, 200, AHORA, None)
        assert resultado["restante_ms"] == 0
        assert resultado["gastadas"] == 200

    def test_ya_lista_no_gasta(self):
        llena = {"planta": "hs", "siembra": AHORA, "reducido": 120_000}
        resultado = aplicar_piedras(llena, 5, AHORA, None)
        assert resultado["restante_ms"] == 0
        assert resultado["gastadas"] == 0

    def test_no_muta_la_casilla(self):
        antes = dict(HS)
        aplicar_piedras(HS, 3, AHORA, "fc1")
        assert antes == HS

    def test_con_formacion_puesta(self):
        # El resto que se descuenta es el que ya lleva el descuento
        resultado = aplicar_piedras(HS, 1, AHORA, "fc1")
        assert resultado["restante_ms"] == 108_300  # ceil(114000 × 0.95)

    def test_lanza_sin_piedras(self):
        with pytest.raises(ValueError):
            aplicar_piedras(HS, 0, AHORA, None)
        with pytest.raises(ValueError):
            aplicar_piedras(HS, -2, AHORA, None)


class TestCosteDePiedras:
    def test_recien_sembrada(self):
        # 0.95⁹⁴ = 0.95⁹³ = 0.95⁹⁴ deja el resto ≤ 1 s
        assert coste_max_piedras(HS, AHORA, None) == 94
        resultado = aplicar_piedras(HS, 94, AHORA, None)
        assert resultado["restante_ms"] == 0
        # con una menos no basta
        assert aplicar_piedras(HS, 93, AHORA, None)["restante_ms"] > 0

    def test_con_formacion_el_coste_baja(self):
        assert coste_max_piedras(HS, AHORA, "fc6") < coste_max_piedras(
            HS, AHORA, None
        )

    def test_casi_lista(self):
        casi = {"planta": "hs", "siembra": AHORA, "reducido": 119_500}
        # resto 500 ms < umbral → 0 piedras
        assert coste_max_piedras(casi, AHORA, None) == 0
        assert coste_max_piedras(HS, AHORA + 120_000, None) == 0
        assert coste_max_piedras(None, AHORA, None) == 0

    def test_concuerda_con_aplicar(self):
        for planta, margen in (("hs", 0), ("gm", 1), ("nf", 2)):
            casilla = {"planta": planta, "siembra": AHORA, "reducido": 0}
            k = coste_max_piedras(casilla, AHORA + margen, None)
            assert aplicar_piedras(casilla, k, AHORA + margen, None)[
                "restante_ms"
            ] == 0


class TestRendimientoYDesbloqueo:
    def test_rendimiento(self):
        assert rendimiento("hs") == 1
        assert rendimiento("rj") == 1
        assert rendimiento("gm") == 2
        assert rendimiento("lu") == 2
        assert rendimiento("nf") == 3

    def test_desbloqueada_por_reino(self):
        assert desbloqueada(0, 0)
        assert not desbloqueada(1, 0)
        assert desbloqueada(1, 1)
        assert not desbloqueada(4, 6)
        assert desbloqueada(4, 7)

    def test_desbloqueada_sin_reino(self):
        assert desbloqueada(0, None)


class TestSiguienteMejora:
    def test_escalera_completa(self):
        primera = siguiente_mejora(0)
        assert primera == {
            "nivel": 1,
            "casillas": 6,
            "coste": {"h": 15, "n": 5, "p": 5},
            "reino_min": 2,
        }
        assert siguiente_mejora(1)["casillas"] == 9
        assert siguiente_mejora(2)["casillas"] == 12

    def test_al_tope(self):
        assert siguiente_mejora(3) is None
        assert siguiente_mejora(99) is None

    def test_no_muta_el_catalogo(self):
        mejora = siguiente_mejora(0)
        mejora["coste"]["h"] = 999
        assert siguiente_mejora(0)["coste"]["h"] == 15


class TestBotinBoticario:
    def test_rasante_en_el_reino_bajo(self):
        botin = botin_boticario(0, _fijo(0.0))
        # 0.0 < 0.35 → 2 semillas, ambas de rareza 0; 0.0 < 0.30 → fc1
        assert botin["semillas"] == {"hs": 2}
        assert botin["formacion"] == "fc1"
        assert botin["materiales"] == {"h": 2, "p": 1, "n": 0}

    def test_justo_en_el_umbral(self):
        # 0.35 < 0.35 no → 1 semilla; 0.30 < 0.30 no → sin formación
        botin = botin_boticario(0, _fijo(0.35))
        assert sum(botin["semillas"].values()) == 1
        assert botin["formacion"] is None
        assert set(botin["semillas"]) <= {h.identificador for h in HIERBAS}

    def test_dificultad_alta(self):
        # prob 2ª semilla = 0.35 + 0.05×5 = 0.60; materiales suben
        botin = botin_boticario(5, _fijo(0.5))
        assert sum(botin["semillas"].values()) == 2
        assert botin["materiales"] == {"h": 7, "p": 3, "n": 1}
        # 0.5 < 0.30 no → sin formación
        assert botin["formacion"] is None

    def test_con_ruido_de_aleatorio(self):
        # Llamadas en orden: 2ª semilla (0.0 → sí), especie 1, especie
        # 2, prob. de formación (0.29 < 0.30 → sí) y su sorteo (0.99
        # → última, fc6). Con rng fijo alto la formación no sale: su
        # probabilidad propia es 30 %.
        botin = botin_boticario(0, _varios(0.0, 0.0, 0.0, 0.29, 0.99))
        assert botin["semillas"] == {"hs": 2}
        assert botin["formacion"] == "fc6"

    def test_propiedades_generales(self):
        ids = {h.identificador for h in HIERBAS}
        formaciones = {f.identificador for f in FORMACIONES}
        for dif in range(6):
            for disparo in range(20):
                botin = botin_boticario(
                    dif, lambda disparo=disparo: (disparo % 19) / 20
                )
                assert set(botin["semillas"]) <= ids
                assert 1 <= sum(botin["semillas"].values()) <= 2
                assert botin["formacion"] in formaciones | {None}
                assert botin["materiales"]["h"] >= 2
                assert botin["materiales"]["p"] >= 1

    def test_materiales_se_frenan(self):
        botin = botin_boticario(10, _fijo(0.0))
        # `n` solo a partir de dificultad 3, y `h` crece 1 a 1
        assert botin["materiales"] == {"h": 12, "p": 6, "n": 1}


class TestRegaloAscenso:
    def test_reino_que_desbloquea_especie(self):
        regalo = regalo_ascenso(1, _fijo(0.0))
        assert regalo["semilla"] in {"ff", "rd", "ll", "hv"}
        # formación de rareza 1 // 3 = 0
        assert regalo["formacion"] in {"fc1", "fc2"}

    def test_reino_sin_especie_nueva(self):
        regalo = regalo_ascenso(2, _fijo(0.0))
        assert regalo["semilla"] is None
        assert regalo["formacion"] in {"fc1", "fc2"}

    def test_reino_de_rareza_maxima(self):
        regalo = regalo_ascenso(7, _fijo(0.999999))
        assert regalo["semilla"] == "nf"
        # rareza de formación = 7 // 3 = 2 → última fc de esa rareza
        assert regalo["formacion"] == "fc4"

    def test_reino_de_cierre(self):
        regalo = regalo_ascenso(8, _fijo(0.0))
        assert regalo["semilla"] is None
        # 8 // 3 = 2 → fc4, única de rareza 2
        assert regalo["formacion"] == "fc4"

    def test_las_dos_especies_de_rareza(self):
        # reino 3 → rareza 2 → gm o lu según el rng
        assert regalo_ascenso(3, _fijo(0.0))["semilla"] == "gm"
        assert regalo_ascenso(3, _fijo(0.999999))["semilla"] == "lu"


class TestRedondeos:
    def test_nada_de_coma_flotante(self):
        # 120000 × 0.95 en coma flotante es 113999.99999…: si no se
        # redondea hacia arriba, la primera piedra «regala» 1 ms.
        resultado = aplicar_piedras(HS, 1, AHORA, None)
        assert resultado["reducido"] == 6_000
        assert math.ceil(120_000 * 0.95) == 114_000
