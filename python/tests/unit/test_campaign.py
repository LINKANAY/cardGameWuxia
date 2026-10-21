"""Tests de campaña pura — victoria, muerte, recompensas."""

from __future__ import annotations

from app.data.niveles import ENEMIGOS, MISIONES_SECUNDARIAS
from app.engine import campaign
from app.engine.state import Partida, nuevas_misiones


def _rng_constante(valor: float = 0.0):
    """Callback que siempre devuelve el mismo float."""
    return lambda: valor


def _enemigo(indice: int = 0):
    return ENEMIGOS[indice]


class TestAscenderReino:
    def test_asciende_y_aumenta_vida_max(self):
        partida = Partida(nivel_reino=0, vida_hroe=25)
        assert campaign.ascender_reino(partida) is True
        assert partida.nivel_reino == 1
        assert partida.vida_hroe == 25 + 2

    def test_no_asciende_en_tope(self):
        partida = Partida(nivel_reino=14)
        assert campaign.ascender_reino(partida) is False


class TestContadoresVictoria:
    def test_incremente_w_y_ek(self):
        partida = Partida()
        enemigo = _enemigo(0)  # esp, dificultad 0
        campaign.contadores_victoria(partida, enemigo)
        assert partida.misiones["w"] == 1
        assert partida.misiones["ek"]["esp"] == 1

    def test_bs_en_jefe_nivel(self):
        # índice 5 = último del nivel 0, dificultad 5
        enemigo = ENEMIGOS[5]
        assert enemigo.dificultad == 5
        partida = Partida()
        campaign.contadores_victoria(partida, enemigo)
        assert partida.misiones["bs"] == 1

    def test_bestia_por_secta_bam(self):
        enemigo = next(
            e for e in ENEMIGOS if e.secta in ("bam", "dra")
        )
        partida = Partida()
        campaign.contadores_victoria(partida, enemigo)
        assert partida.misiones["bk"] == 1


class TestMaterialesVictoria:
    def test_formulas_con_rng_cero(self):
        enemigo = ENEMIGOS[1]  # nivel 0, d=1
        m = campaign.materiales_victoria(
            enemigo, _rng_constante(0.0), primera=False
        )
        # d=1: h = 1 + 0 + 0 = 1; p = 1 + 1 + 0 = 2; n = 0 (d<2)
        # s = 2 + 2 + 0 = 4
        assert m["h"] == 1
        assert m["p"] == 2
        assert m["n"] == 0
        assert m["s"] == 4

    def test_primera_victoria_bonus_piedras(self):
        enemigo = ENEMIGOS[0]
        m = campaign.materiales_victoria(
            enemigo, _rng_constante(0.0), primera=True
        )
        m2 = campaign.materiales_victoria(
            enemigo, _rng_constante(0.0), primera=False
        )
        assert m["s"] == m2["s"] + 5  # 5*(0+1)


class TestMuertePermanente:
    def test_resetea_partida_y_cuenta_muerte(self):
        partida = Partida(
            nivel_reino=3,
            victorias=[0, 1, 2],
            coleccion={"cf": 3},
            piedras_espirituales=999,
            muertes=0,
            mejor_racha=1,
        )
        resumen = campaign.muerte_permanente(partida, ENEMIGOS[0])
        assert partida.muertes == 1
        assert partida.mejor_racha == 3
        assert partida.nivel_reino == 0
        assert partida.victorias == []
        assert partida.coleccion == {}
        assert partida.piedras_espirituales == 30
        assert resumen["r"] == 3
        assert resumen["w"] == 3


class TestAplicarVictoria:
    def test_primera_victoria_registra_y_da_recursos(self):
        partida = Partida(piedras_espirituales=0)
        enemigo = ENEMIGOS[0]
        resumen = campaign.aplicar_victoria(
            partida, enemigo, 0, 20, _rng_constante(0.0)
        )
        assert resumen["primera"] is True
        assert partida.victorias == [0]
        assert len(resumen["recompensas"]) == 3
        assert partida.piedras_espirituales > 0
        assert partida.misiones["w"] == 1

    def test_jefe_final_nivel_asciende_y_resetea_hp(self):
        partida = Partida(nivel_reino=0, vida_hroe=10)
        enemigo = ENEMIGOS[5]  # d=5, no mazmorra
        resumen = campaign.aplicar_victoria(
            partida, enemigo, 5, 12, _rng_constante(0.0)
        )
        assert resumen["ascenso"] is True
        assert resumen["vida_max_reseteada"] is True
        assert partida.vida_hroe is None
        assert partida.nivel_reino == 1

    def test_victoria_repetida_no_duplica_wins(self):
        partida = Partida(victorias=[0])
        enemigo = ENEMIGOS[0]
        resumen = campaign.aplicar_victoria(
            partida, enemigo, 0, 15, _rng_constante(0.0)
        )
        assert resumen["primera"] is False
        assert partida.victorias == [0]


class TestMazoParaCombate:
    def test_automatico_si_no_hay_mazo(self):
        partida = Partida(secta="esp")
        mazo = campaign.mazo_para_combate(partida, _rng_constante(0.5))
        assert len(mazo) == 40

    def test_mazo_activo_si_es_valido(self):
        from app.engine.rules import construir_mazo

        mazo = construir_mazo("esp", aleatorio=lambda: 0.3)
        conteo = {}
        for ident in mazo:
            conteo[ident] = conteo.get(ident, 0) + 1
        partida = Partida(
            secta="esp",
            mazos=[{"n": "t", "c": conteo}],
            mazo_activo=0,
        )
        plano = campaign.mazo_para_combate(partida, _rng_constante(0.5))
        assert sorted(plano) == sorted(mazo)


class TestEsJefeFinalMazmorra:
    def test_indices_de_mazmorra(self):
        # 48 = primer jefe de mazmorra; 50 = tercero
        assert campaign.es_jefe_final_mazmorra(48) is False
        assert campaign.es_jefe_final_mazmorra(49) is False
        assert campaign.es_jefe_final_mazmorra(50) is True
        assert campaign.es_jefe_final_mazmorra(53) is True
