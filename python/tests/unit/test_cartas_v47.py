"""Cartas v47 — paridad con los bloques de `js/06-contenido.js`.

Cubre las 129 cartas que el monolito crea con sus bucles (NS, XC, XF,
XR, XH y XV): presencia en `CARTAS`, sectas v47 con sus 5 iniciales en
orden, mapa `SC`/`SECTA_DE_CARTA`, lista `NEU` y un muestreo campo a
campo contra `tests/fixtures/cartas_parity.json` (regenerado con
`node tools/gen_cards_fixture.mjs`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.data import CARTAS, CARTAS_NEUTRALES, SECTA_DE_CARTA, SECTAS
from app.data.tipos import (
    CartaData,
    TipoEfecto,
    UltimoAliento,
)

_FIXDIR = Path(__file__).resolve().parent.parent / "fixtures"

# NS: 4 sectas × 13 cartas (M/P/T/B 01-13), en orden de definición.
_IDS_NS = [
    f"{secta}{numero:02d}" for secta in "MPTB" for numero in range(1, 14)
]
_IDS_Z = [f"Z{numero:02d}" for numero in range(1, 33)]
_IDS_Y = [f"Y{numero:02d}" for numero in range(1, 23)]
_IDS_X = [f"X{numero:02d}" for numero in range(1, 13)]
_IDS_H = ["H01", "H02", "H03", "H04"]
_IDS_V = [f"V{numero:02d}" for numero in range(1, 8)]

#: Cartas v47 con `k` distinto de null en el JS: entran en `SC`.
_SECTABLES = (
    _IDS_NS
    + _IDS_Z[:30]
    + _IDS_Y[:20]
    + _IDS_X[2:]
    + ["H03", "H04"]
)

#: Cartas v47 neutras (`k = null`): no entran en `SC`.
_NEUTRAS_V47 = ["Z31", "Z32", "Y21", "Y22", "X01", "X02", "H01", "H02"]

#: `ts: [codigo, valor]` de todas las cartas con `efecto_inicio_turno`
#: (19 formaciones/runas; el resto del catálogo no usa `ts`).
_TS_ESPERADO = {
    "Y02": ("h", 2),
    "Y03": ("m", 1),
    "Y04": ("s", 3),
    "Y05": ("x", 1),
    "Y07": ("s", 1),
    "Y08": ("q", 1),
    "Y09": ("d", 1),
    "Y10": ("h", 1),
    "Y11": ("d", 2),
    "Y12": ("h", 2),
    "Y13": ("m", 2),
    "Y14": ("r", 1),
    "Y15": ("d", 3),
    "Y16": ("q", 1),
    "Y17": ("s", 3),
    "Y18": ("h", 3),
    "Y19": ("d", 3),
    "Y20": ("s", 2),
    "Y22": ("s", 2),
}

#: Muestreo campo a campo pedido en la portada.
_MUESTRA = (
    "M05", "M13", "P12", "T10", "B13",
    "Z19", "Z20", "Z21",
    "Y05", "Y07", "Y17",
    "X09", "H03", "V04",
)


@pytest.fixture(scope="module")
def fixture_cartas() -> dict:
    return json.loads(
        (_FIXDIR / "cartas_parity.json").read_text(encoding="utf-8")
    )


def test_bloques_completos_en_catalogo():
    """Los 129 ids de NS/XC/XF/XR/XH/XV están en `CARTAS`."""
    bloques = {
        "NS": _IDS_NS,
        "XC": _IDS_Z,
        "XF": _IDS_Y,
        "XR": _IDS_X,
        "XH": _IDS_H,
        "XV": _IDS_V,
    }
    esperados = {"NS": 52, "XC": 32, "XF": 22, "XR": 12, "XH": 4, "XV": 7}
    for bloque, ids in bloques.items():
        assert len(ids) == esperados[bloque], bloque
        for identificador in ids:
            assert identificador in CARTAS, identificador
    total_bloques = sum(esperados.values())
    assert total_bloques == 129
    assert len(CARTAS) == 106 + total_bloques


def test_sectas_v47_iniciales_en_orden():
    """Las 4 sectas v47 reciben sus 5 primeras cartas de NS, en orden."""
    assert SECTAS["mon"].cartas_iniciales == (
        "M01", "M02", "M03", "M04", "M05",
    )
    assert SECTAS["pil"].cartas_iniciales == (
        "P01", "P02", "P03", "P04", "P05",
    )
    assert SECTAS["tru"].cartas_iniciales == (
        "T01", "T02", "T03", "T04", "T05",
    )
    assert SECTAS["bam"].cartas_iniciales == (
        "B01", "B02", "B03", "B04", "B05",
    )


def test_secta_de_carta_cubre_las_sectables(fixture_cartas):
    """`SC[id] = k` sólo cuando el JS trae secta (k no-null)."""
    assert len(_SECTABLES) == 114
    sc_js = fixture_cartas["sc"]
    assert {
        identificador: SECTA_DE_CARTA[identificador]
        for identificador in _SECTABLES
    } == {identificador: sc_js[identificador] for identificador in _SECTABLES}
    for identificador in _NEUTRAS_V47:
        assert identificador not in SECTA_DE_CARTA
        assert identificador not in sc_js


def test_secta_de_ns_es_la_de_su_prefijo():
    """NS: M→mon, P→pil, T→tru, B→bam (`SC[id] = k` de la línea 12)."""
    por_prefijo = {"M": "mon", "P": "pil", "T": "tru", "B": "bam"}
    for identificador in _IDS_NS:
        assert SECTA_DE_CARTA[identificador] == por_prefijo[
            identificador[0]
        ], identificador


def test_neutrales_v47(fixture_cartas):
    """`NEU.push` de js/06-contenido.js:28,30,42,45, en ese orden."""
    assert CARTAS_NEUTRALES[-7:] == (
        "Y21", "X01", "H01", "H02", "V01", "V02", "V03",
    )
    assert list(CARTAS_NEUTRALES) == fixture_cartas["neu"]
    assert len(CARTAS_NEUTRALES) == 16
    for identificador in CARTAS_NEUTRALES:
        assert identificador in CARTAS


def test_muestreo_nombre_coste_tipo(fixture_cartas):
    """Nombre, coste y tipo del muestreo frente a la fixture."""
    for identificador in _MUESTRA:
        carta = CARTAS[identificador]
        bruto = fixture_cartas["cartas"][identificador]
        assert carta.nombre == bruto["n"], identificador
        assert carta.coste_qi == bruto["c"], identificador
        assert carta.tipo.value == bruto["t"], identificador
        assert carta.a_js() == bruto, identificador


def test_muestreo_efectos_desde_js(fixture_cartas):
    """Todos los campos de efecto del muestreo, vía `desde_js`+fixture."""
    for identificador in _MUESTRA:
        if identificador == "Y05":
            # ts: 'x' no está en TipoEfecto; lo cubre el test de abajo.
            continue
        bruto = fixture_cartas["cartas"][identificador]
        assert CARTAS[identificador] == CartaData.desde_js(
            identificador, bruto
        ), identificador


def test_muestreo_efectos_compuestos():
    """Traducciones de efectos compuestos más propensas a error."""
    assert CARTAS["M13"].ultimo_aliento == UltimoAliento(
        tipo=TipoEfecto.ESCUDO, valor=6
    )
    assert CARTAS["T10"].habilidad_activa is not None
    assert CARTAS["T10"].habilidad_activa.tipo == TipoEfecto.DANO_HROE
    assert CARTAS["P12"].curar == 10 and CARTAS["P12"].ganar_qi == 2
    assert CARTAS["Z21"].escudo == 14 and CARTAS["Z21"].dano_area == 3
    assert CARTAS["H03"].curar_porcentaje == 32
    assert CARTAS["V04"].abismo_traer == 1
    assert CARTAS["V04"].abismo_elegir is True
    assert CARTAS["Y07"].mejora_vida_al_trazar == 2
    assert CARTAS["Y17"].duracion_turnos == 3
    assert CARTAS["X09"].renovar == 3


def test_y05_conserva_el_ts_x(fixture_cartas):
    """`ts: ['x', 1]` de Y05, con el código crudo pendiente de enum."""
    carta = CARTAS["Y05"]
    bruto = fixture_cartas["cartas"]["Y05"]
    assert carta.mejora_ataque_al_trazar == bruto["pa"] == 2
    tipo, valor = carta.efecto_inicio_turno
    assert tipo.value == bruto["ts"][0] == "x"
    assert valor == bruto["ts"][1] == 1


def test_cartas_con_efecto_inicio_turno(fixture_cartas):
    """Cobertura exacta de `ts` en todo el catálogo (19 cartas)."""
    obtenidos = {}
    for identificador, carta in CARTAS.items():
        if carta.efecto_inicio_turno is not None:
            tipo, valor = carta.efecto_inicio_turno
            obtenidos[identificador] = (tipo.value, valor)
    assert obtenidos == _TS_ESPERADO
    for identificador, (codigo, valor) in _TS_ESPERADO.items():
        assert CARTAS[identificador].a_js()["ts"] == [codigo, valor]
        assert fixture_cartas["cartas"][identificador]["ts"] == [
            codigo,
            valor,
        ]


def test_reliquias_v47_no_se_venden():
    """`lk` de XC: 20 reliquias (Z02-Z03, Z05-Z06, …), rareza 4/5."""
    reliquias = {i for i, c in CARTAS.items() if c.reliquia}
    assert reliquias == {
        "Z02", "Z03", "Z05", "Z06", "Z08", "Z09", "Z11", "Z12",
        "Z14", "Z15", "Z17", "Z18", "Z20", "Z21", "Z23", "Z24",
        "Z26", "Z27", "Z29", "Z30",
    }
    assert all(
        CARTAS[identificador].rareza_fija in (4, 5)
        for identificador in reliquias
    )
