"""Tests de integridad y paridad de los datos del juego.

Los fixtures `cartas_parity.json` y `enemigos_parity.json` se generan
desde el monolito con `tools/gen_cards_fixture.mjs` y
`tools/gen_enemies_fixture.mjs`. Si se regeneran, estos tests validan
que la portada Python sigue siendo idéntica.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.data import (
    CARTAS,
    CARTAS_NEUTRALES,
    COLOR_DIFICULTAD,
    COLOR_RAREZA,
    COSTE_FORJA,
    DIFICULTADES,
    DISENOS_TALISMAN,
    ENEMIGOS,
    FINAL,
    FRASES_COMBATE,
    MAZMORRAS,
    MISIONES_SECUNDARIAS,
    MULT_DIFICULTAD,
    NIVELES,
    NOMBRE_MATERIAL,
    OFFSET_MISIONES_SECUNDARIAS,
    PILDORAS,
    PRECIO_RAREZA,
    PROLOGO,
    RAREZAS,
    REINOS,
    SECTA_DE_CARTA,
    SECTAS,
    TEXTO_FIN_NIVEL,
    TEXTO_HABILIDAD_ENEMIGO,
    TEXTO_INTRO_NIVEL,
    VIDA_BASE_NIVEL,
    Material,
    TipoCarta,
    cartas_de_rareza,
    clave_mision_secundaria,
    crear_carta,
    rareza_de,
)

_FIXDIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture(scope="module")
def fixture_cartas() -> dict:
    return json.loads((_FIXDIR / "cartas_parity.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fixture_enemigos() -> dict:
    return json.loads((_FIXDIR / "enemigos_parity.json").read_text(encoding="utf-8"))


# --- Catálogo de cartas ------------------------------------------------------


def test_total_cartas(fixture_cartas):
    # 106 base (js/01-datos.js) + 129 v47 (js/06-contenido.js)
    assert len(CARTAS) == 235 == fixture_cartas["total"]


def test_cartas_identica_al_js(fixture_cartas):
    """Cada carta serializada con `a_js()` coincide con el objeto JS."""
    for identificador, bruto in fixture_cartas["cartas"].items():
        assert (
            CARTAS[identificador].a_js() == bruto
        ), f"carta {identificador!r}"


def test_cartas_base_cinco_por_secta():
    """Las 10 sectas (6 base + 4 v47) tienen 5 cartas iniciales.

    En las v47 las 5 primeras cartas de NS llegan con
    `if (i < 5) S[k].l.push(id)` (js/06-contenido.js:12).
    """
    assert len(SECTAS) == 10
    for secta in SECTAS.values():
        assert len(secta.cartas_iniciales) == 5, secta.identificador
        for carta in secta.cartas_iniciales:
            assert carta in CARTAS


def test_sectas_identica_al_js(fixture_cartas):
    """Las 10 sectas (6 base + 4 v47) coinciden con `S` del JS."""
    js = fixture_cartas["sectas"]
    assert set(SECTAS) == set(js)
    for identificador, bruto in js.items():
        propia = SECTAS[identificador]
        assert propia.nombre == bruto["n"], identificador
        assert propia.descripcion == bruto["i"], identificador
        assert list(propia.cartas_iniciales) == bruto["l"], identificador


def test_sc_derivado_de_sectas(fixture_cartas):
    assert fixture_cartas["sc"] == SECTA_DE_CARTA


def test_tipos_y_costes_validos():
    for carta in CARTAS.values():
        assert carta.tipo in TipoCarta
        assert 0 <= carta.coste_qi <= 8
        assert carta.nombre
        if carta.tipo == TipoCarta.CRIATURA:
            assert carta.ataque is not None and carta.vida is not None


def test_rareza_por_coste():
    """Tabla `[0,0,1,2,3,3,4,4,5][min(c,8)]` con rareza_fija mandando."""
    # cf: coste 1, sin r → rareza 0
    assert rareza_de(CARTAS["cf"]) == 0
    # ta: coste 2 pero r=2 → rareza 2
    assert rareza_de(CARTAS["ta"]) == 2
    # pr: coste 8, r=5 → rareza 5
    assert rareza_de(CARTAS["pr"]) == 5


def test_cartas_de_rareza_excluye_reliquias():
    for rareza in range(6):
        identificadores = cartas_de_rareza(rareza)
        assert all(
            not CARTAS[identificador].reliquia
            for identificador in identificadores
        )
    # toda carta no-reliquia aparece en exactamente una rareza
    total = sum(
        len(cartas_de_rareza(nivel)) for nivel in range(6)
    )
    no_reliquias = sum(
        1 for carta in CARTAS.values() if not carta.reliquia
    )
    assert total == no_reliquias


def test_crear_carta_instancia():
    carta = crear_carta("ev")
    assert carta.identificador == "ev"
    assert carta.ataque == 3 and carta.vida == 1
    assert carta.lista_para_atacar is False
    # la copia no comparte mutabilidad con la definición
    carta.ataque = 99
    assert CARTAS["ev"].ataque == 3


def test_neutrales_estan_en_catalogo(fixture_cartas):
    """`NEU`: 9 base (js/01-datos.js:51) + 7 de js/06-contenido.js."""
    assert len(CARTAS_NEUTRALES) == 16 == len(fixture_cartas["neu"])
    assert list(CARTAS_NEUTRALES) == fixture_cartas["neu"]
    for ident in CARTAS_NEUTRALES:
        assert ident in CARTAS


def test_colores_y_nombres_rareza(fixture_enemigos):
    assert list(RAREZAS) == fixture_enemigos["rN"]
    assert list(COLOR_RAREZA) == fixture_enemigos["rC"]
    assert list(PRECIO_RAREZA) == [6, 12, 24, 45, 90, 180]


# --- Enemigos y mundo --------------------------------------------------------


def test_total_enemigos(fixture_enemigos):
    assert len(ENEMIGOS) == 90 == fixture_enemigos["total_enemigos"]


def test_enemigos_identico_al_js(fixture_enemigos):
    """Campo a campo, cada enemigo aplanado coincide con `CH` del JS."""
    for indice, (enemigo_js, enemigo_py) in enumerate(
        zip(fixture_enemigos["enemigos"], ENEMIGOS, strict=True)
    ):
        assert enemigo_py.nombre_enemigo == enemigo_js["e"], indice
        assert enemigo_py.secta == enemigo_js["s"], indice
        assert list(enemigo_py.habilidades) == enemigo_js["rl"], indice
        assert enemigo_py.frase_inicio == enemigo_js["i"], indice
        assert enemigo_py.frase_derrota == enemigo_js["x"], indice
        assert enemigo_py.receta == enemigo_js.get("rcp"), indice
        assert enemigo_py.nombre_nivel == enemigo_js["n"], indice
        assert enemigo_py.indice_nivel == enemigo_js["li"], indice
        assert enemigo_py.dificultad == enemigo_js["d"], indice
        assert enemigo_py.indice_mazmorra == enemigo_js.get("dg"), indice
        assert enemigo_py.indice_mision == enemigo_js.get("sq"), indice
        assert enemigo_py.fase_mision == enemigo_js.get("sqf"), indice
        assert enemigo_py.vida == enemigo_js["hp"], indice
        assert enemigo_py.capacidad == enemigo_js["cap"], indice
        assert enemigo_py.rareza_recompensa == enemigo_js["rw"], indice
        assert enemigo_py.texto_habilidades == enemigo_js["r"], indice


def test_habilidades_enemigo(fixture_enemigos):
    assert dict(TEXTO_HABILIDAD_ENEMIGO) == fixture_enemigos["rt"]
    # toda habilidad referenciada existe
    for enemigo in ENEMIGOS:
        for habilidad in enemigo.habilidades:
            assert habilidad in TEXTO_HABILIDAD_ENEMIGO


def test_formulas_vida_y_rareza():
    """Fórmulas exactas del JS para vida, capacidad y rareza."""
    for enemigo in ENEMIGOS:
        vida_esperada = int(
            VIDA_BASE_NIVEL[enemigo.indice_nivel]
            * MULT_DIFICULTAD[enemigo.dificultad]
            + 0.5
        )
        assert enemigo.vida == vida_esperada
        if enemigo.indice_mazmorra:
            assert enemigo.capacidad in (7, 8, 9)
        elif enemigo.indice_mision:
            assert enemigo.capacidad in (6, 7, 8)
        else:
            assert enemigo.capacidad == (5, 6, 7, 8, 9, 10)[enemigo.dificultad]


def test_offsets_misiones():
    assert OFFSET_MISIONES_SECUNDARIAS == 48 + 18
    assert clave_mision_secundaria(0, 0) == 66
    assert clave_mision_secundaria(7, 2) == 89


def test_recetas_de_mazmorras_apuntan_a_pildoras():
    for mazmorra in MAZMORRAS:
        for jefe in mazmorra.jefes:
            assert jefe.receta in PILDORAS


def test_conteos_mundo():
    assert len(NIVELES) == 8
    assert all(len(nivel.combates) == 6 for nivel in NIVELES)
    assert len(MAZMORRAS) == 6
    assert all(len(mazmorra.jefes) == 3 for mazmorra in MAZMORRAS)
    assert len(MISIONES_SECUNDARIAS) == 8
    assert all(len(mision.fases) == 3 for mision in MISIONES_SECUNDARIAS)


def test_dificultades_y_colores(fixture_enemigos):
    assert list(DIFICULTADES) == fixture_enemigos["df"]
    assert list(COLOR_DIFICULTAD) == fixture_enemigos["dc"]
    assert len(VIDA_BASE_NIVEL) == 8
    assert len(MULT_DIFICULTAD) == 6


def test_gradientes_de_nivel(fixture_enemigos):
    """`LV[i].sky` (escena de la intro de combate)."""
    assert [list(nivel.gradiente_color) for nivel in NIVELES] == [
        nivel["sky"] for nivel in fixture_enemigos["niveles"]
    ]


def test_reinos():
    assert len(REINOS) == 15
    assert REINOS[0] == "Mortal"
    assert REINOS[-1] == "Soberano del Dao"


def test_narrativa(fixture_enemigos):
    assert fixture_enemigos["pro"] == PROLOGO
    assert list(TEXTO_INTRO_NIVEL) == fixture_enemigos["st"]
    assert list(TEXTO_FIN_NIVEL) == fixture_enemigos["en"]
    assert fixture_enemigos["fin"] == FINAL
    assert len(TEXTO_INTRO_NIVEL) == 8
    assert len(TEXTO_FIN_NIVEL) == 8


def test_frases_combate(fixture_enemigos):
    for secta, esperado in fixture_enemigos["say"].items():
        nuestras = FRASES_COMBATE[secta]
        assert nuestras["ataque"] == tuple(esperado["a"]), secta
        assert nuestras["invocacion"] == tuple(esperado["s"]), secta
        assert nuestras["defensa"] == tuple(esperado["d"]), secta
        assert nuestras["burla"] == tuple(esperado["h"]), secta
        assert nuestras["criatura"] == tuple(esperado["c"]), secta
        assert (
            nuestras["criatura_objetivo"] == tuple(esperado["t"])
        ), secta


# --- Píldoras y forja --------------------------------------------------------


def test_pildoras(fixture_enemigos):
    assert len(PILDORAS) == 27
    for identificador, pildora_js in fixture_enemigos["pil"].items():
        pildora = PILDORAS[identificador]
        assert pildora.nombre == pildora_js["n"], identificador
        assert pildora.efecto == pildora_js["t"], identificador
        assert {
            material.value: cantidad
            for material, cantidad in pildora.coste.items()
        } == pildora_js["c"], identificador
        assert pildora.es_combate == bool(pildora_js.get("b")), identificador
        assert pildora.es_recuperacion == bool(pildora_js.get("o")), (
            identificador
        )
        assert pildora.porcentaje_recuperacion == pildora_js.get("rcv"), (
            identificador
        )


def test_pildoras_material_valido():
    for pildora in PILDORAS.values():
        assert pildora.coste, pildora.identificador
        for material in pildora.coste:
            assert material in Material


def test_coste_forja(fixture_enemigos):
    assert len(COSTE_FORJA) == 6
    for rareza, coste_js in enumerate(fixture_enemigos["fc"]):
        coste_nuestro = {
            material.value: cantidad
            for material, cantidad in COSTE_FORJA[rareza].items()
        }
        assert coste_nuestro == coste_js, rareza


def test_disenios_talisman():
    assert len(DISENOS_TALISMAN) == 4
    assert "ward" in DISENOS_TALISMAN
    assert DISENOS_TALISMAN["ward"].nombre == "Talismán de Protección"


def test_nombres_material(fixture_enemigos):
    assert {
        material.value: nombre
        for material, nombre in NOMBRE_MATERIAL.items()
    } == fixture_enemigos["mn"]
