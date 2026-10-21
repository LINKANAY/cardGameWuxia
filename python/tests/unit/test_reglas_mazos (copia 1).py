"""Reglas de mazos — paridad con dkUI/dNew/dAdd/… del JS.

Fuente: `js/04-mazos-formaciones.js` (acciones),
`js/03-cartas-mercado.js:35-36` (DM/own3/dsz/dok/actDeck) y
`js/12-v47-init.js:25` (dUneq). Cada test cita la referencia.
"""

from __future__ import annotations

import pytest

from app.data.cartas import CARTAS, CARTAS_NEUTRALES
from app.data.sectas import SECTAS
from app.engine.rules import (
    MAX_COPIAS,
    MAX_MAZOS,
    TAMANO_MAZO,
    anadir_carta_a_mazo,
    autocompletar_mazo,
    construir_mazo,
    copias_usables,
    crear_mazo,
    desequipar_del_activo,
    duplicar_mazo,
    eliminar_mazo,
    mazo_activo_plano,
    mazo_valido,
    quitar_carta_de_mazo,
    renombrar_mazo,
    tamano_mazo,
    vaciar_mazo,
)

SECTA = "esp"
BASE_ESP = SECTAS[SECTA].cartas_iniciales  # cf, ev, ld, ma, te


def _mazo(conteo=None, nombre="Mazo 1"):
    return {"n": nombre, "c": dict(conteo or {})}


def _mazo_lleno_de_base():
    """Mazo válido: 5 base ×3 + neutrales completando hasta 40."""
    conteo = {}
    for carta in BASE_ESP:
        conteo[carta] = MAX_COPIAS
    restantes = TAMANO_MAZO - sum(conteo.values())
    for carta in CARTAS_NEUTRALES:  # 16 neutrales: 8×3 + 1 = 25
        if restantes <= 0:
            break
        cantidad = min(MAX_COPIAS, restantes)
        conteo[carta] = cantidad
        restantes -= cantidad
    assert restantes == 0
    return _mazo(conteo)


class TestCopiasUsables:
    """`own3(id)`: min(3, max(3 si base/neutral, col[id]))."""

    def test_carta_base_de_la_secta_es_usable_a_3_sin_coleccion(self):
        assert copias_usables("cf", SECTA, {}) == 3

    def test_carta_neutral_es_usable_a_3_sin_coleccion(self):
        assert copias_usables("pq", SECTA, {}) == 3

    def test_carta_ajena_solo_lo_poseido(self):
        assert copias_usables("lc", SECTA, {"lc": 2}) == 2

    def test_carta_ajena_sin_coleccion_es_0(self):
        assert copias_usables("lc", SECTA, {}) == 0

    def test_tope_de_3(self):
        assert copias_usables("lc", SECTA, {"lc": 5}) == 3


class TestTamanoYValidez:
    """`dsz`/`dok`: 40 cartas exactas y copias ≤ own3."""

    def test_tamano_suma_copias(self):
        assert tamano_mazo(_mazo({"cf": 3, "ev": 2})) == 5

    def test_vacio_no_es_valido(self):
        assert mazo_valido(_mazo(), SECTA, {}) is False

    def test_tamano_incorrecto_no_es_valido(self):
        mazo = _mazo_lleno_de_base()
        mazo["c"]["cf"] = 2  # 39 cartas
        assert mazo_valido(mazo, SECTA, {}) is False

    def test_carta_inexistente_no_es_valida(self):
        mazo = _mazo_lleno_de_base()
        mazo["c"]["zzz"] = 1
        mazo["c"]["cf"] = 2  # sigue en 40
        assert mazo_valido(mazo, SECTA, {}) is False

    def test_copias_de_mas_no_son_validas(self):
        mazo = _mazo_lleno_de_base()
        # 'lc' (Loto) no es base de esp ni neutral: 1 copia sin coleccionar
        mazo["c"]["pq"] = 2
        mazo["c"]["lc"] = 1
        assert mazo_valido(mazo, SECTA, {}) is False

    def test_mazo_lleno_de_base_es_valido(self):
        assert mazo_valido(_mazo_lleno_de_base(), SECTA, {}) is True

    def test_none_no_es_valido(self):
        assert mazo_valido(None, SECTA, {}) is False


class TestMazoActivoPlano:
    """`actDeck`: lista plana solo si el mazo es válido."""

    def test_invalido_devuelve_none(self):
        assert mazo_activo_plano(_mazo({"cf": 1}), SECTA, {}) is None

    def test_valido_aplana_por_orden(self):
        mazo = _mazo_lleno_de_base()
        plano = mazo_activo_plano(mazo, SECTA, {})
        assert plano is not None
        assert len(plano) == TAMANO_MAZO
        assert plano.count("cf") == 3


class TestCrearMazo:
    """`dNew(a)`: nombre incremental; con `a` copia el automático."""

    def test_crea_vacio_con_nombre_incremental(self):
        mazos: list[dict] = []
        mazo = crear_mazo(
            mazos, desde_automatico=False, secta=SECTA, coleccion={}
        )
        assert mazos == [mazo]
        assert mazo["n"] == "Mazo 1"
        assert mazo["c"] == {}

    def test_desde_automatico_tiene_40_cartas(self):
        mazos: list[dict] = []
        mazo = crear_mazo(
            mazos,
            desde_automatico=True,
            secta=SECTA,
            coleccion={"aa": 2},
            aleatorio=_aleatorio_fijo(),
        )
        assert tamano_mazo(mazo) == TAMANO_MAZO
        # la base de la secta entra a 3 copias, como deck(sect, true)
        assert all(mazo["c"].get(carta, 0) == 3 for carta in BASE_ESP)
        assert mazo["c"].get("aa") == 2

    def test_maximo_8_mazos(self):
        mazos = [_mazo() for _ in range(MAX_MAZOS)]
        with pytest.raises(ValueError):
            crear_mazo(
                mazos, desde_automatico=False, secta=SECTA, coleccion={}
            )


class TestRenombrarMazo:
    """`dRen(v)`: trim, tope 22, vacío ignorado."""

    def test_aplica_trim_y_tope(self):
        mazo = _mazo()
        assert renombrar_mazo(mazo, "  Mazo guerrero  ") == "Mazo guerrero"
        assert mazo["n"] == "Mazo guerrero"
        assert renombrar_mazo(mazo, "x" * 30) == "x" * 22

    def test_vacio_devuelve_vacio_sin_cambiar(self):
        mazo = _mazo({"cf": 1}, nombre="Original")
        assert renombrar_mazo(mazo, "   ") == ""
        assert mazo["n"] == "Original"


class TestAnadirYQuitar:
    """`dAdd`/`dRm`: tope own3 y DM; delete al llegar a 0."""

    def test_anade_y_quita(self):
        mazo = _mazo()
        assert anadir_carta_a_mazo(mazo, "cf", SECTA, {}) is True
        assert mazo["c"] == {"cf": 1}
        assert quitar_carta_de_mazo(mazo, "cf") is True
        assert mazo["c"] == {}

    def test_anade_hasta_las_copias_usables(self):
        mazo = _mazo({"cf": 3})
        assert anadir_carta_a_mazo(mazo, "cf", SECTA, {}) is False
        mazo_ajena = _mazo({"lc": 1})
        assert anadir_carta_a_mazo(mazo_ajena, "lc", SECTA, {"lc": 1}) is False

    def test_no_anade_si_el_mazo_esta_lleno(self):
        mazo = _mazo_lleno_de_base()
        assert tamano_mazo(mazo) == TAMANO_MAZO
        assert anadir_carta_a_mazo(mazo, "cf", SECTA, {}) is False

    def test_quitar_inexistente_es_false(self):
        assert quitar_carta_de_mazo(_mazo(), "cf") is False


class TestVaciar:
    def test_vacia_por_completo(self):
        mazo = _mazo({"cf": 3, "ev": 1})
        vaciar_mazo(mazo)
        assert mazo["c"] == {}


class TestAutocompletar:
    """`dFill`: orden secta → coste → rareza; rondas 1..3 hasta 40."""

    def test_rellena_40_con_base_y_neutrales(self):
        mazo = _mazo()
        autocompletar_mazo(mazo, SECTA, {})
        assert tamano_mazo(mazo) == TAMANO_MAZO
        # con 16 neutrales la ronda 2 corta en 40 y la base se queda
        # en 2 copias: mismo corte que dFill (js/04-mazos-formaciones.js:15)
        assert all(mazo["c"].get(carta, 0) == 2 for carta in BASE_ESP)
        assert all(cantidad <= 3 for cantidad in mazo["c"].values())

    def test_incluye_lo_poseido_hasta_su_tope(self):
        mazo = _mazo()
        autocompletar_mazo(mazo, SECTA, {"aa": 2})
        assert mazo["c"].get("aa") == 2

    def test_respeta_el_tope_de_40(self):
        mazo = _mazo({"tf": 3})
        autocompletar_mazo(mazo, SECTA, {})
        assert tamano_mazo(mazo) == TAMANO_MAZO


class TestDuplicarMazo:
    """`dDup(i)`: sufijo « (copia)» y copia profunda de las cuentas."""

    def test_duplica_con_sufijo_y_contenido(self):
        mazos = [_mazo({"cf": 2}, nombre="Guerrero")]
        copia = duplicar_mazo(mazos, 0)
        assert copia["n"] == "Guerrero (copia)"
        assert copia["c"] == {"cf": 2}
        copia["c"]["cf"] = 1
        assert mazos[0]["c"]["cf"] == 2  # no comparten el dict

    def test_nombre_se_recorta_a_22(self):
        mazos = [_mazo(nombre="x" * 22)]
        assert duplicar_mazo(mazos, 0)["n"] == ("x" * 22 + " (copia)")[:22]

    def test_maximo_8_mazos(self):
        mazos = [_mazo() for _ in range(MAX_MAZOS)]
        with pytest.raises(ValueError):
            duplicar_mazo(mazos, 0)


class TestEliminarMazo:
    """`dDel(i)`: reajusta el mazo activo como el JS."""

    def test_eliminar_el_activo_pasa_a_automatico(self):
        mazos = [_mazo(), _mazo()]
        assert eliminar_mazo(mazos, 1, 1) == -1
        assert len(mazos) == 1

    def test_eliminar_anterior_decrementa_el_activo(self):
        mazos = [_mazo(), _mazo()]
        assert eliminar_mazo(mazos, 0, 1) == 0

    def test_eliminar_posterior_no_toca_el_activo(self):
        mazos = [_mazo(), _mazo()]
        assert eliminar_mazo(mazos, 1, 0) == 0


class TestDesequiparDelActivo:
    """`dUneq(id)`: quita del mazo en uso, no de uno cualquiera."""

    def test_quita_del_mazo_activo(self):
        mazos = [_mazo({"cf": 2}), _mazo({"ev": 1})]
        assert desequipar_del_activo(mazos, 0, "cf") is True
        assert mazos[0]["c"] == {"cf": 1}
        assert mazos[1]["c"] == {"ev": 1}

    def test_sin_mazo_activo_es_false(self):
        assert desequipar_del_activo([_mazo({"cf": 1})], -1, "cf") is False

    def test_carta_ausente_es_false(self):
        assert desequipar_del_activo([_mazo()], 0, "cf") is False


def _aleatorio_fijo(secuencia=None):
    """Callback float con valores predecibles (paridad de barajados)."""
    valores = iter(secuencia or [0.0, 0.5, 0.9, 0.1] * 40)

    def azar():
        try:
            return next(valores)
        except StopIteration:
            return 0.0

    return azar


# construir_mazo ya tiene tests en otro módulo; aquí solo verificamos
# que la integración con crear_mazo usa el mismo contrato. Cada llamada
# lleva su propia secuencia fija: con 16 neutrales sólo parte de ellos
# caben en 40 y el azar decidiría cuáles.
def test_crear_desde_automatico_es_un_construir_mazo():
    mazos: list[dict] = []
    mazo = crear_mazo(
        mazos,
        desde_automatico=True,
        secta=SECTA,
        coleccion={},
        aleatorio=_aleatorio_fijo(),
    )
    plano = construir_mazo(
        SECTA, con_coleccion=True, coleccion={}, aleatorio=_aleatorio_fijo()
    )
    assert sorted(mazo["c"]) == sorted(set(plano))
