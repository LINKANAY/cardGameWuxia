"""Reglas de equipo (Herrería) y trajes — puertos de `js/06-contenido.js`."""

from __future__ import annotations

import pytest

from app.data.equipo import GEAR, PIEZAS, SLOTS, piezas_por_slot
from app.data.tipos import Material
from app.data.trajes import TRAJES, nombre_efecto, traje
from app.engine import rules


def _inventario(**cantidades: int) -> dict[str, int]:
    return {"h": 0, "n": 0, "p": 0, **cantidades}


class TestCatalogoEquipo:
    def test_las_17_piezas_y_sus_huecos(self):
        assert len(GEAR) == 17
        assert len({p.identificador for p in GEAR}) == 17
        assert all(p.slot in SLOTS for p in GEAR)

    def test_orden_de_la_herreria_por_hueco(self):
        orden = [p.slot for p in piezas_por_slot()]
        assert orden == sorted(
            orden, key=lambda slot: SLOTS.index(slot)
        )

    def test_los_artefactos_reviven_con_usos(self):
        for identificador in ("G10", "G11"):
            pieza = PIEZAS[identificador]
            assert pieza.slot == "artefacto"
            assert pieza.revive and pieza.usos

    def test_los_costes_son_materiales_del_guardado(self):
        for pieza in GEAR:
            assert set(pieza.coste) <= {
                Material.HIERBAS,
                Material.NUCLEOS,
                Material.POLVO_JADE,
            }
            assert all(cantidad > 0 for cantidad in pieza.coste.values())


class TestDesbloqueoYForja:
    def test_pieza_sin_plano_esta_desbloqueada(self):
        assert rules.pieza_desbloqueada(PIEZAS["G1"], [])

    def test_pieza_con_plano_requiere_su_victoria(self):
        assert not rules.pieza_desbloqueada(PIEZAS["G2"], [16])
        assert rules.pieza_desbloqueada(PIEZAS["G2"], [17])

    def test_forjar_paga_y_auto_equipa_en_hueco_vacio(self):
        materiales = _inventario(p=3, h=2)
        equipo, equipado, usos = {}, {}, {}
        rules.forjar_pieza(equipo, equipado, usos, materiales, [], "G1")
        assert equipo == {"G1": 1}
        assert equipado == {"cabeza": "G1"}
        assert materiales == {"h": 0, "n": 0, "p": 0}

    def test_forjar_no_sustituye_un_hueco_ocupado(self):
        equipo, equipado = {"G1": 1}, {"cabeza": "G1"}
        rules.forjar_pieza(
            equipo, equipado, {}, _inventario(p=6, n=2), [17], "G2"
        )
        assert equipado["cabeza"] == "G1"
        assert equipo["G1"] == 1 and equipo["G2"] == 1

    def test_forjar_un_artefacto_inicia_sus_usos(self):
        equipo, equipado, usos = {}, {}, {}
        rules.forjar_pieza(
            equipo, equipado, usos, _inventario(p=14, n=6), [23], "G10"
        )
        assert usos == {"G10": 3}
        assert equipado["artefacto"] == "G10"

    def test_no_se_puede_forjar_sin_materiales_ni_dos_veces(self):
        with pytest.raises(ValueError):
            rules.forjar_pieza({}, {}, {}, _inventario(), [], "G1")
        with pytest.raises(ValueError):
            rules.forjar_pieza(
                {"G1": 1}, {}, {}, _inventario(p=3, h=2), [], "G1"
            )

    def test_forjar_desconocido_lanza(self):
        with pytest.raises(ValueError):
            rules.forjar_pieza({}, {}, {}, _inventario(), [], "G99")


class TestEquipar:
    def test_alternar_equipa_y_retira(self):
        equipado: dict = {}
        rules.equipar_pieza(equipado, "G1")
        assert equipado["cabeza"] == "G1"
        rules.equipar_pieza(equipado, "G1")
        assert equipado["cabeza"] is None

    def test_sustituye_la_pieza_del_mismo_hueco(self):
        equipado = {"cabeza": "G1"}
        rules.equipar_pieza(equipado, "G2")
        assert equipado["cabeza"] == "G2"

    def test_equipo_desconocido_lanza(self):
        with pytest.raises(ValueError):
            rules.equipar_pieza({}, "G99")


class TestGearStat:
    def test_suma_solo_piezas_poseidas_y_equipadas(self):
        equipado = {"cabeza": "G3", "cuerpo": "G6"}
        completo = rules.gear_stat(equipado, {"G3": 1, "G6": 1})
        assert completo == {"a": 4, "q": 3, "ra": 5, "rq": 3}

        sin_poseer = rules.gear_stat(equipado, {})
        assert sin_poseer == {"a": 0, "q": 0, "ra": 0, "rq": 0}

        equipado_vacio = {"cabeza": None}
        assert rules.gear_stat(equipado_vacio, {"G3": 1})["ra"] == 0

    def test_tope_de_4_con_reserva_sin_topear(self):
        equipado = {
            "cabeza": "G3",   # a2 q2
            "cuerpo": "G6",   # a3 q1
            "guantes": "G14",  # a2 q1
        }
        estado = rules.gear_stat(equipado, {"G3": 1, "G6": 1, "G14": 1})
        assert estado["a"] == 4
        assert estado["ra"] == 7

    def test_ignora_ids_desconocidos_en_el_guardado(self):
        assert rules.gear_stat({"cabeza": "G99"}, {"G99": 1}) == {
            "a": 0,
            "q": 0,
            "ra": 0,
            "rq": 0,
        }


class TestTrajes:
    def test_six_trajes_por_secta_con_umbral(self):
        assert all(len(lista) == 6 for lista in TRAJES.values())
        assert len(TRAJES) == 10
        assert [t.umbral for t in TRAJES["esp"]] == [
            0,
            3,
            12,
            30,
            45,
            60,
        ]

    def test_nombre_del_traje_y_efecto_como_el_oa_del_js(self):
        inicial = traje("esp", 0)
        assert inicial is not None
        assert inicial.nombre == "Túnica del Discípulo"
        assert inicial.efecto == "Cuerpo de la Espada"
        assert inicial.descripcion == "+2 vida máxima"

    def test_el_mismo_efecto_se_numera_con_ii(self):
        assert nombre_efecto("esp", 1) == "Filo de la Espada"
        assert nombre_efecto("esp", 4) == "Filo de la Espada II"
        assert nombre_efecto("esp", 5) == "Furia de la Espada II"

    def test_desbloqueo_por_victorias(self):
        # el umbral es sobre el recuento total de victorias (`W >= TU[i]`)
        assert rules.puede_vestir_traje("esp", 0, [])
        assert not rules.puede_vestir_traje("esp", 1, [0, 1])
        assert rules.puede_vestir_traje("esp", 1, [0, 1, 2])

    def test_vestir_escribe_el_atuendo(self):
        atuendo: dict[str, int] = {}
        victorias = [0, 1, 2]
        rules.vestir_traje(atuendo, victorias, "esp", 1)
        assert atuendo == {"esp": 1}
        with pytest.raises(ValueError):
            rules.vestir_traje(atuendo, victorias, "esp", 2)
        with pytest.raises(ValueError):
            rules.vestir_traje(atuendo, [], "zzz", 0)
