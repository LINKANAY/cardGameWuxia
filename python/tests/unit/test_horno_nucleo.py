"""Núcleo del Horno — paridad de fórmulas con `js/11-horno.js:131-230`.

El azar se inyecta con un callable fijo (lista de valores); los
resultados numéricos están calculados a mano siguiendo las fórmulas del
JS (`redondear_js` = `Math.round`, mitad hacia arriba).
"""

from __future__ import annotations

import pytest

from app.data.hierbas import MENSAJES_FALLO
from app.engine.horno import (
    botin,
    botin_combate,
    clasificar,
    cura_pct,
    rango_calidad,
    rango_danio,
    refinar,
    resumen_combinacion,
)


def _rngs(valores):
    """Callable fijo: devuelve los valores en orden y truena al agotarse."""
    it = iter(valores)

    def falso():
        return next(it)

    return falso


class TestResumenCombinacion:
    def test_armonia_suma_bono_y_calidad(self):
        # hs+hs: base 30 + 12 hierbas + 5 armonía = 47 %; puntos 1+1+2
        r = resumen_combinacion(["hs", "hs"], 0)
        assert r["prob"] == 47
        assert r["puntos"] == 4
        assert r["armonia"] is True
        assert r["discordia"] is False
        assert r["tipo"] == "heal"
        assert r["desglose"] == [
            ["Base", 30],
            ["Hierbas", 12],
            ["Armonía", 5],
        ]

    def test_discordia_resta_y_no_da_calidad(self):
        # hs (heal) + hn (shield) + ll (gold): 3 afinidades distintas
        r = resumen_combinacion(["hs", "hn", "ll"], 0)
        assert r["prob"] == 30 + 6 + 3 + 2 - 6  # 35
        assert r["puntos"] == 1 + 2 + 4  # sin bono de armonía
        assert r["armonia"] is False
        assert r["discordia"] is True
        assert r["desglose"] == [
            ["Base", 30],
            ["Hierbas", 11],
            ["Discordia", -6],
        ]
        # tipo = afinidad con más votos: ll aporta 4 de calidad
        assert r["tipo"] == "gold"

    def test_reino_suma_un_por_nivel(self):
        r = resumen_combinacion(["hs", "hs"], 3)
        assert r["prob"] == 47 + 3
        assert r["desglose"][-1] == ["Reino", 3]

    def test_sin_afinidades_es_restauradora(self):
        # hv no vota (afinidad null): tipo por defecto heal
        r = resumen_combinacion(["hv", "hv"], 0)
        assert r["tipo"] == "heal"
        assert r["armonia"] is False
        assert r["discordia"] is False
        assert r["prob"] == 30 - 16  # 14 %

    def test_ids_desconocidos_se_ignoran(self):
        r = resumen_combinacion(["hs", "zzz", "hs"], 0)
        assert r["prob"] == 47
        assert r["desglose"][1] == ["Hierbas", 12]

    def test_prob_clamp_5_95(self):
        # techo: 4× nf (15) + armonía gold + reino 5 → 100 → 95
        alto = resumen_combinacion(["nf", "nf", "nf", "nf"], 5)
        assert alto["prob"] == 95
        # suelo: 4× hv (-8) → -2 → 5
        bajo = resumen_combinacion(["hv", "hv", "hv", "hv"], 0)
        assert bajo["prob"] == 5


class TestClasificarYRangos:
    def test_clasificar_umbrales(self):
        # UMBRALES_CALIDAD: media 7, alta 13, suprema 20 (línea 41)
        assert clasificar(6) == "baja"
        assert clasificar(7) == "media"
        assert clasificar(12.99) == "media"
        assert clasificar(13) == "alta"
        assert clasificar(19.99) == "alta"
        assert clasificar(20) == "suprema"
        assert clasificar(100) == "suprema"

    def test_rango_calidad_aplica_ruido_y_margen(self):
        # [puntos − 4, puntos + 4 + 3] (líneas 182-184)
        assert rango_calidad(10) == ["baja", "alta"]
        assert rango_calidad(20) == ["alta", "suprema"]


class TestRangoDanio:
    def test_formula_con_vida_30(self):
        # m = 1 + (1 − 50/100) × 0.5 = 1.25; 30×6%×1.25 = 2.25 → 2
        #                            30×14%×1.25 = 5.25 → 5
        assert rango_danio(50, 30) == (2, 5)

    def test_suelo_nunca_cero(self):
        # 4×6%×1.25 = 0.3 → 0 → suelo 1; 4×14%×1.25 = 0.7 → 1
        assert rango_danio(50, 4) == (1, 1)
        # prob 5 → m = 1 + 0.95×0.5 = 1.475; 1×14%×1.475 ≈ 0.21 → 1
        assert rango_danio(5, 1) == (1, 1)


class TestCuraPct:
    def test_por_calidad_y_tipo(self):
        assert cura_pct({"tipo": "heal", "calidad": "media"}) == 25.0
        # gold (×0.90): 40 × 0.9 = 36
        assert cura_pct({"tipo": "gold", "calidad": "alta"}) == 36.0
        # qi (×0.75): 65 × 0.75 = 48.75 → round → 48.8
        assert cura_pct({"tipo": "qi", "calidad": "suprema"}) == 48.8

    def test_perfecta_multiplica_1_25(self):
        # 65 × 1.25 × 1.0 = 81.25 → Math.round(812.5/10) → 81.3
        assert cura_pct({"tipo": "heal", "calidad": "perfecta"}) == 81.3

    def test_waste_es_uno_por_ciento(self):
        assert cura_pct({"tipo": "waste", "calidad": "fallida"}) == 1

    def test_tipo_desconocido_usa_heal(self):
        # JS: `TIPOS[p.tipo] || TIPOS.heal` (línea 198)
        assert cura_pct({"tipo": "zzz", "calidad": "media"}) == 25.0

    def test_calidad_desconocida_no_cura(self):
        # `CURA_POR_CALIDAD[...] || 0` (línea 197)
        assert cura_pct({"tipo": "heal", "calidad": "fallida"}) == 0.0


class TestRefinar:
    def test_exito_con_ruido_y_margen(self):
        # hs+hn: prob 39, puntos 3, tipo shield (votos: hn 2 > hs 1)
        # rng: tirada 0 → margen 1.0; ruido (1+1−1)×4 = 4
        # puntos = 3 + 3 + 4 = 10 → media
        r = refinar(["hs", "hn"], _rngs([0.0, 1.0, 1.0]), {"reino": 0})
        assert r["exito"] is True
        assert r["prob"] == 39
        assert r["tirada"] == 0.0
        assert r["puntos"] == 10.0
        assert r["pildora"] == {"tipo": "shield", "calidad": "media"}

    def test_exito_perfecta_con_ruido_maximo(self):
        # nf+gm: prob 55, puntos 13, tipo gold; margen 1 → +3; ruido +4
        # puntos 20 → suprema; tirada de perfecta 0.05 < 0.08 → perfecta
        r = refinar(
            ["nf", "gm"],
            _rngs([0.0, 1.0, 1.0, 0.05]),
            {"reino": 0},
        )
        assert r["exito"] is True
        assert r["puntos"] == 20.0
        assert r["pildora"] == {"tipo": "gold", "calidad": "perfecta"}

    def test_perfecta_no_pasa_con_ruido_alto(self):
        # mismos dados pero la tirada de perfecta falla (0.5 ≥ 0.08)
        r = refinar(
            ["nf", "gm"],
            _rngs([0.0, 1.0, 1.0, 0.5]),
            {"reino": 0},
        )
        assert r["pildora"] == {"tipo": "gold", "calidad": "suprema"}

    def test_fallo_danio_y_mensaje(self):
        # hv+hv: prob 14. rng: tirada 99 → fallo; pct lerp(6,14,0.5)=10;
        # mult = 1 + (1 − 0.14)×0.5 = 1.43; 30×10%×1.43 = 4.29 → 4
        r = refinar(
            ["hv", "hv"], _rngs([0.99, 0.5, 0.0]), {"maxHp": 30}
        )
        assert r["exito"] is False
        assert r["prob"] == 14
        assert r["tirada"] == 99.0
        assert r["danio"] == 4
        assert r["mensaje"] == MENSAJES_FALLO[0]
        assert r["pildora"] == {"tipo": "waste", "calidad": "fallida"}

    def test_fallo_danio_suelo_uno(self):
        # maxHp 1: 1×10%×1.43 = 0.143 → 0 → suelo 1
        r = refinar(["hv", "hv"], _rngs([0.99, 0.5, 0.0]), {"maxHp": 1})
        assert r["danio"] == 1

    def test_fallo_maxhp_por_defecto_30(self):
        # ctx vacío → `ctx.maxHp || 30` (línea 218)
        r = refinar(["hv", "hv"], _rngs([0.99, 0.5, 0.0]), {})
        assert r["danio"] == 4

    def test_fallo_elige_mensaje_por_rng(self):
        # índice floor(0.6 × 5) = 3
        r = refinar(
            ["hv", "hv"], _rngs([0.99, 0.5, 0.6]), {"maxHp": 30}
        )
        assert r["mensaje"] == MENSAJES_FALLO[3]

    def test_tirada_justa_bajo_prob_es_exito(self):
        # prob 47: tirada 46.9 < 47 → éxito (línea 211, estricto)
        r = refinar(
            ["hs", "hs"], _rngs([0.469, 0.5, 0.5]), {"reino": 0}
        )
        assert r["exito"] is True
        # tirada 47.0 = prob → fallo
        r2 = refinar(
            ["hs", "hs"], _rngs([0.47, 0.5, 0.0]), {"reino": 0}
        )
        assert r2["exito"] is False


class TestBotin:
    def test_botin_dificultad_cero_una_hierba(self):
        # n = 1 + floor(0×2) + 0 = 1; t = 0 → primera hierba (hs)
        assert botin_combate(0, _rngs([0.0, 0.0])) == {"hs": 1}

    def test_botin_dificultad_jefe_dos_hierbas(self):
        # dif ≥ 4 → +1 bonus (línea 305)
        assert botin_combate(4, _rngs([0.0, 0.0, 0.0])) == {"hs": 2}
        assert botin_combate(5, _rngs([0.0, 0.0, 0.0])) == {"hs": 2}

    def test_botin_es_jefe_fuerza_bonus(self):
        # bonus también con `es_jefe` explícito (decisión del backend)
        assert botin_combate(0, _rngs([0.0, 0.0, 0.0]), es_jefe=True) == {
            "hs": 2
        }

    def test_botin_rng_alto_elige_rara(self):
        # con dif 0 el peso total es 160 y t ≈ 160 cae en nf (peso 1)
        assert botin(1, _rngs([0.999999]), 0) == {"nf": 1}

    def test_botin_suma_n(self):
        resultado = botin(5, _rngs([0.1, 0.2, 0.3, 0.4, 0.5]), 0)
        assert sum(resultado.values()) == 5

    def test_botin_n_cero_sortea_una(self):
        # `n || 1` del JS (línea 294)
        assert botin(0, _rngs([0.0]), 0) == {"hs": 1}
