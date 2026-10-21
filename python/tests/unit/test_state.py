"""Tests de `Partida`, serialización xcg3 y reglas puras de Fase 1."""

from __future__ import annotations

import json

import pytest

from app.data import CARTAS, ENEMIGOS, PILDORAS, PRECIO_RAREZA, SECTAS
from app.data.pildoras import Material
from app.engine.rng import GeneradorAleatorio
from app.engine.rules import (
    construir_mazo,
    generar_rareza_recompensa,
    pagar,
    precio_compra,
    puede_comprar_carta,
    puede_pagar,
    rareza_de,
)
from app.engine.state import (
    Partida,
    crear_carta_juego,
    nuevas_misiones,
)

CLAVES_XCG3 = {
    "realm", "hp", "wins", "col", "sect", "mat", "stn", "dk", "ad",
    "pil", "of", "rec", "be", "gr", "eq", "sc", "du", "dt", "bt",
    "qs", "qd", "gt", "gp",
    # clave backend del xcg_horno del monolito (horno de alquimia)
    "xn",
}


# --- Partida: defaults y roundtrip ------------------------------------------


def test_defaults_partida_nueva():
    partida = Partida()
    assert partida.nivel_reino == 0
    assert partida.vida_hroe is None
    assert partida.victorias == []
    assert partida.coleccion == {}
    assert partida.secta == "esp"
    assert partida.materiales == {"h": 0, "n": 0, "p": 0}
    assert partida.piedras_espirituales == 30
    assert partida.mazos == []
    assert partida.mazo_activo == -1
    assert partida.pildoras == {}
    assert partida.recetas == {"vit": 1, "tes": 1}
    assert partida.secta_elegida_confirmada is None
    assert partida.muertes == 0
    assert partida.mejor_racha == 0
    assert partida.misiones == nuevas_misiones()


def test_a_dict_tiene_claves_xcg3():
    assert set(Partida().a_dict()) == CLAVES_XCG3


def test_roundtrip_sin_perdida():
    partida = Partida(
        nivel_reino=3,
        vida_hroe=12,
        victorias=[0, 1, 66],
        coleccion={"cf": 2, "pr": 1},
        secta="lot",
        materiales={"h": 5, "n": 2, "p": 9},
        piedras_espirituales=123,
        mazos=[["cf", "ev"]],
        mazo_activo=0,
        pildoras={"vit": 2, "cur": 1},
        atuendo={"esp": 1},
        recetas={"vit": 1, "tes": 1, "dra": 1},
        bestia_equipada=None,
        equipo_guardado={"ward": 1},
        equipado={"focus": 1},
        secta_elegida_confirmada="lot",
        usos_equipo={"ember": 2},
        muertes=4,
        mejor_racha=7,
        misiones=nuevas_misiones() | {"w": 3, "ek": {"esp": 2}},
        misiones_reclamadas={"m1": 1},
        entradas_gacha={"ticket_common": 5, "ticket_premium": 2},
        piedad_gacha={"standard_pity": 0, "premium_pity": 0},
    )
    original = partida.a_dict()
    # serializar a JSON y volver (como el save real)
    via_json = json.loads(json.dumps(original, ensure_ascii=False))
    recargada = Partida.desde_dict(via_json)
    assert recargada.a_dict() == original


def test_desde_dict_defaults():
    partida = Partida.desde_dict({})
    assert partida.piedras_espirituales == 30
    assert partida.recetas == {"vit": 1, "tes": 1}
    # sin victorias ni colección no se deduce secta
    assert partida.secta_elegida_confirmada is None

    # con victorias deduce secta
    partida_deducida = Partida.desde_dict({"wins": [0], "sect": "val"})
    assert partida_deducida.secta_elegida_confirmada == "val"


def test_desde_dict_recorta_reino():
    partida = Partida.desde_dict({"realm": 99})
    assert partida.nivel_reino == 14


def test_desde_dict_legacy_xcg2():
    """Convierte índices de wins antiguos como el JS (`old ? …`)."""
    partida = Partida.desde_dict(
        {"wins": [0, 1, 2]}, legacy_xcg2=True
    )
    # floor(0/3)*6 + [1,3,5][0] = 1; floor(1/3)*6+[1,3,5][1]=3; floor(2/3)*6+5=5
    assert partida.victorias == [1, 3, 5]


def test_qs_fusiona_sobre_defaults():
    """Un save viejo sin claves nuevas de qs las obtiene con default."""
    partida = Partida.desde_dict({"qs": {"w": 9}})
    assert partida.misiones["w"] == 9
    assert partida.misiones["track"] == ""  # default preservado
    assert partida.misiones["ek"] == {}  # default preservado


# --- CartaJuego --------------------------------------------------------------


def test_crear_carta_juego():
    carta = crear_carta_juego("ma")
    assert carta.identificador == "ma"
    assert carta.nombre == "Maestro de la Espada"
    assert carta.ataque == 4 and carta.vida == 3
    assert carta.lista_para_atacar is False
    assert carta.copias_apiladas == 1
    assert carta.es_bestia is False


def test_crear_bestia():
    """El flag `bst` no está en el catálogo (lo asigna el sistema de
    bestias en runtime, Fase 2); las criaturas normales lo tienen False."""
    carta = crear_carta_juego("pr")
    assert carta.es_bestia is False
    assert carta.ataque == 10 and carta.vida == 10


# --- Reglas puras: genRw -----------------------------------------------------


def test_genrw_primera_carta_merecida():
    """La primera carta sale con la rareza exacta del enemigo."""
    generador = GeneradorAleatorio("genrw")
    identificadores = generar_rareza_recompensa(
        generador.random, rareza_meritada=5
    )
    assert len(identificadores) == 3
    assert rareza_de(CARTAS[identificadores[0]]) == 5


def test_genrw_siempre_tres_o_menos():
    generador = GeneradorAleatorio("genrw2")
    identificadores = generar_rareza_recompensa(
        generador.random, rareza_meritada=2
    )
    assert 1 <= len(identificadores) <= 3
    assert len(set(identificadores)) == len(identificadores), "sin repetidos"


def test_genrw_rareza_no_negativa():
    """max(0, m - …) nunca baja de 0."""
    generador = GeneradorAleatorio("genrw3")
    for _ in range(20):
        identificadores = generar_rareza_recompensa(
            generador.random, rareza_meritada=0
        )
        for identificador in identificadores:
            assert rareza_de(CARTAS[identificador]) == 0


# --- Reglas puras: mercado ---------------------------------------------------


def test_puede_comprar_reglas():
    # Celestial (r5) nunca
    assert not puede_comprar_carta("pr", "esp")
    # de otra secta
    assert not puede_comprar_carta("lc", "esp")  # lc es de lot
    # de mi secta
    assert puede_comprar_carta("lc", "lot")
    # neutrales siempre
    assert puede_comprar_carta("gp", "esp")


def test_precio_compra():
    assert precio_compra("cf") == PRECIO_RAREZA[0] == 6
    assert precio_compra("pr") == PRECIO_RAREZA[5] == 180


def test_puede_pagar_y_pagar():
    materiales = {"h": 3, "n": 1, "p": 0}
    coste = {Material.HIERBAS: 3, Material.POLVO_JADE: 1}
    assert not puede_pagar(coste, materiales)
    materiales["p"] = 1
    assert puede_pagar(coste, materiales)
    pagar(coste, materiales)
    assert materiales == {"h": 0, "n": 1, "p": 0}


def test_pagar_insuficiente_lanza():
    with pytest.raises(ValueError):
        pagar({Material.HIERBAS: 5}, {"h": 1, "n": 0, "p": 0})


# --- Reglas puras: mazo ------------------------------------------------------


def test_construir_mazo_base():
    mazo = construir_mazo("esp", aleatorio=lambda: 0.5)
    assert len(mazo) == 40
    # las 5 cartas base aparecen 3 veces cada una
    for base in SECTAS["esp"].cartas_iniciales:
        assert mazo.count(base) == 3


def test_construir_mazo_con_coleccion():
    mazo = construir_mazo(
        "esp",
        con_coleccion=True,
        coleccion={"pr": 1},
        aleatorio=lambda: 0.0,
    )
    assert "pr" in mazo


def test_mazo_maximo_40():
    mazo = construir_mazo(
        "lot",
        con_coleccion=True,
        coleccion={
            identificador: 3 for identificador in CARTAS
        },
        extras=5,
        aleatorio=lambda: 0.3,
    )
    assert len(mazo) == 40
