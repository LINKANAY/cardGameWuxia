"""Tests de paridad del RNG con el monolito JS.

El fixture `tests/fixtures/rng_parity.json` se genera ejecutando el RNG
real de `js/00-rng.js` con `tools/gen_rng_fixture.mjs`. Si el fixture
queda desactualizado (cambió el JS), regenerar con:

    node tools/gen_rng_fixture.mjs
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engine.rng import GeneradorAleatorio, generador_mulberry32, hash_texto

_FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "rng_parity.json"
)


@pytest.fixture(scope="module")
def fixture_rng() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_hash_referencia(fixture_rng):
    """El hash de 'test-123' es el valor conocido (139701620)."""
    assert hash_texto("test-123") == 139701620
    for semilla, primer_valor in fixture_rng["hash_referencia"].items():
        generador = GeneradorAleatorio(semilla)
        assert int(generador.random() * 4294967296) == primer_valor


def test_secuencia_bit_a_bit(fixture_rng):
    """Cada float de la secuencia Python coincide con el uint32 del JS."""
    for semilla, datos in fixture_rng["semillas"].items():
        generador = GeneradorAleatorio(semilla)
        for indice, esperado in enumerate(datos["valores_uint32"]):
            obtenido = generador.random() * 4294967296
            assert int(obtenido) == esperado, (
                f"semilla={semilla!r} indice={indice}: "
                f"{obtenido} != {esperado}"
            )


def test_barajar_fisher_yates(fixture_rng):
    """`barajar` reproduce exactamente `RNG.shuffle` del JS."""
    for semilla, datos in fixture_rng["semillas"].items():
        generador = GeneradorAleatorio(semilla)
        entrada = list(range(10))
        for intento, esperado in enumerate(datos["barajados"]):
            obtenido = generador.barajar(entrada)
            assert (
                obtenido == esperado
            ), f"semilla={semilla!r} barajado={intento}"
            assert entrada == list(range(10)), "barajar no debe mutar la entrada"


def test_entero_y_elegir():
    """`entero(n)` = floor(random()*n); `elegir` usa `entero`."""
    generador = GeneradorAleatorio("secuencia")
    valores = [generador.entero(6) for _ in range(50)]
    assert all(0 <= valor < 6 for valor in valores)

    generador_2 = GeneradorAleatorio("secuencia")
    lista = ["a", "b", "c"]
    for _ in range(20):
        assert generador_2.elegir(lista) in lista


def test_reiniciar_repite_secuencia():
    """Reiniciar con la misma semilla reproduce la misma secuencia."""
    generador = GeneradorAleatorio("x")
    secuencia_1 = [generador.random() for _ in range(10)]
    generador.reiniciar("x")
    secuencia_2 = [generador.random() for _ in range(10)]
    assert secuencia_1 == secuencia_2


def test_semilla_distinta_cambia_secuencia():
    generador_uno = GeneradorAleatorio("x")
    generador_dos = GeneradorAleatorio("y")
    assert [generador_uno.random() for _ in range(5)] != [
        generador_dos.random() for _ in range(5)
    ]


def test_barajar_con_fuente_alternativa():
    """`barajar_con` usa el callback dado (paridad con `RNG.shuffle(a, r)`).

    Con una fuente que siempre devuelve 0, Fisher-Yates arrastra el
    primer elemento al final de cada paso:
    [1,2,3,4,5] → [5,2,3,4,1] → [4,2,3,5,1] → [3,2,4,5,1] → [2,3,4,5,1].
    """
    generador = GeneradorAleatorio("fija")

    def siempre_cero():  # elegiría siempre j=0
        return 0.0

    assert generador.barajar_con(
        [1, 2, 3, 4, 5], siempre_cero
    ) == [2, 3, 4, 5, 1]


def test_mulberry32_aislado():
    """El generador mulberry32 funciona sin pasar por la clase."""
    generador_uno = generador_mulberry32(hash_texto("a"))
    generador_dos = generador_mulberry32(hash_texto("a"))
    assert [generador_uno() for _ in range(5)] == [
        generador_dos() for _ in range(5)
    ]
