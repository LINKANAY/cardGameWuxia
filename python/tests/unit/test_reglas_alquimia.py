"""Reglas de alquimia — paridad con brew/forge/fuse/dis/addCard del JS.

Fuente: `js/01-datos.js` (líneas 190–194) y `js/07-campamento.js` (PILK).
Cada test cita la referencia exacta del monolito.
"""

from __future__ import annotations

import pytest

from app.data.cartas import CARTAS
from app.data.pildoras import COSTE_FORJA, PILDORAS
from app.data.tipos import Material
from app.engine.rules import (
    agregar_carta_coleccion,
    cartas_de_rareza,
    coste_forja,
    desmantelar_coleccion,
    elaborar_pildora,
    forjar_carta,
    fusionar_coleccion,
    puede_elaborar,
    puede_pagar,
    rareza_de,
)


def _materiales(h=0, n=0, p=0):
    return {"h": h, "n": n, "p": p}


class TestPuedeElaborar:
    """`brew` precondiciones: rec[k] && canPay(PIL[k].c)."""

    def test_sin_receta_es_false(self):
        assert puede_elaborar("vit", {}, _materiales(h=10)) is False

    def test_receta_sin_materiales_es_false(self):
        assert puede_elaborar("vit", {"vit": 1}, _materiales()) is False

    def test_receta_con_materiales_es_true(self):
        assert puede_elaborar("vit", {"vit": 1}, _materiales(h=3)) is True

    def test_pildora_desconocida_es_false(self):
        assert puede_elaborar("noexiste", {"noexiste": 1}, _materiales(h=99)) is False


class TestElaborarPildora:
    """`brew(k)`: pay(PIL[k].c); pil[k]++."""

    def test_elabora_vit_y_descuenta_hierbas(self):
        materiales = _materiales(h=5)
        pildoras: dict[str, int] = {}
        recetas = {"vit": 1}
        elaborar_pildora(pildoras, recetas, materiales, "vit")
        assert pildoras == {"vit": 1}
        assert materiales == {"h": 2, "n": 0, "p": 0}  # 5 - coste 3h

    def test_acumula_copias(self):
        materiales = _materiales(h=6)
        pildoras = {"vit": 1}
        elaborar_pildora(pildoras, {"vit": 1}, materiales, "vit")
        assert pildoras == {"vit": 2}

    def test_lanza_si_no_puede_pagar(self):
        with pytest.raises(ValueError):
            elaborar_pildora({}, {"vit": 1}, _materiales(h=2), "vit")


class TestAgregarCartaColeccion:
    """`addCard(id)`: copia +1; a 3 copias → 1+rareza de polvo."""

    def test_copia_nueva(self):
        col: dict[str, int] = {}
        mat = _materiales()
        resultado = agregar_carta_coleccion(col, mat, "cf")
        assert col == {"cf": 1}
        assert mat == {"h": 0, "n": 0, "p": 0}  # intacto
        assert resultado.identificador == "cf"
        assert resultado.nombre == CARTAS["cf"].nombre

    def test_a_tres_copias_convierte_en_polvo(self):
        # cf es Común (rareza 0): polvo = 1 + 0 = 1 (addCard del JS).
        col = {"cf": 3}
        mat = _materiales()
        resultado = agregar_carta_coleccion(col, mat, "cf")
        assert col == {"cf": 3}  # no crece
        assert mat == {"h": 0, "n": 0, "p": 1}
        assert "ya tenías 3 copias" in resultado.nombre

    def test_polvo_escala_con_rareza(self):
        # Carta Épica (rareza 3): polvo = 1 + 3 = 4.
        epica = cartas_de_rareza(3)[0]
        col = {epica: 3}
        mat = _materiales()
        agregar_carta_coleccion(col, mat, epica)
        assert mat == {"h": 0, "n": 0, "p": 4}


class TestForjarCarta:
    """`forge(r)`: pay(FC[r]); byR(r)[random]; addCard."""

    def test_forja_comun_paga_dos_polvo(self):
        col: dict[str, int] = {}
        mat = _materiales(p=2)
        resultado = forjar_carta(col, mat, 0, aleatorio=lambda: 0.0)
        assert mat == {"h": 0, "n": 0, "p": 0}  # FC[0] = {p: 2} pagado
        assert col == {resultado.identificador: 1}
        assert rareza_de(CARTAS[resultado.identificador]) == 0

    def test_eligiendo_el_ultimo_candidato(self):
        candidatos = cartas_de_rareza(0)
        col: dict[str, int] = {}
        mat = _materiales(p=2)
        resultado = forjar_carta(
            col, mat, 0, aleatorio=lambda: 0.999999
        )
        assert resultado.identificador == candidatos[-1]

    def test_lanza_sin_materiales(self):
        with pytest.raises(ValueError):
            forjar_carta({}, _materiales(p=1), 0, aleatorio=lambda: 0.0)


class TestFusionarColeccion:
    """`fuse(id)`: col-=3; addCard de rareza+1."""

    def test_fusiona_comun_a_poco_comun(self):
        col = {"cf": 3}
        mat = _materiales()
        resultado = fusionar_coleccion(
            col, mat, "cf", aleatorio=lambda: 0.0
        )
        assert "cf" not in col  # 3 - 3 = 0 → se borra
        assert col[resultado.identificador] == 1
        assert rareza_de(CARTAS[resultado.identificador]) == 1

    def test_celestial_no_se_fusiona(self):
        celestial = cartas_de_rareza(5)[0]
        col = {celestial: 3}
        with pytest.raises(ValueError):
            fusionar_coleccion(col, _materiales(), celestial, lambda: 0.0)

    def test_sin_tres_copias_lanza(self):
        with pytest.raises(ValueError):
            fusionar_coleccion({"cf": 2}, _materiales(), "cf", lambda: 0.0)


class TestDesmantelarColeccion:
    """`dis(id)`: col--; mat.p += 1 + rar(C[id])."""

    def test_desmantela_comun_un_polvo(self):
        col = {"cf": 2}
        mat = _materiales()
        polvo = desmantelar_coleccion(col, mat, "cf")
        assert polvo == 1  # 1 + rareza 0
        assert col == {"cf": 1}
        assert mat == {"h": 0, "n": 0, "p": 1}

    def test_ultima_copia_se_borra(self):
        col = {"cf": 1}
        desmantelar_coleccion(col, _materiales(), "cf")
        assert col == {}

    def test_sin_copias_lanza(self):
        with pytest.raises(ValueError):
            desmantelar_coleccion({}, _materiales(), "cf")


class TestCostes:
    """Paridad de costes: FC del JS y puede_pagar."""

    def test_coste_forja_comun(self):
        # FC[0] = { p: 2 } en el JS.
        assert coste_forja(0) == COSTE_FORJA[0]
        assert coste_forja(0) == {Material.POLVO_JADE: 2}

    def test_puede_pagar_con_claves_cortas(self):
        coste_vit = PILDORAS["vit"].coste
        assert puede_pagar(coste_vit, {"h": 2}) is False
        assert puede_pagar(coste_vit, {"h": 3}) is True
        assert Material.HIERBAS.value == "h"
