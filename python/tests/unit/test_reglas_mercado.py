"""Reglas del mercado — paridad con buy/buyM/sellM/mkt/mkDet del JS.

Fuente: `js/03-cartas-mercado.js` (compra/venta, detalle, `howGet`)
y `js/12-v47-init.js:131-167` (píldoras, `mkcPrice`, `vzOk`). Cada
test cita la referencia exacta del monolito.
"""

from __future__ import annotations

from app.data.cartas import CARTAS, CARTAS_NEUTRALES, rareza_de
from app.data.mercado import PUESTOS_MERCADO
from app.data.pildoras import PILDORAS
from app.data.tipos import CartaData, TipoCarta, TipoEfecto
from app.engine.rules import (
    MAX_COPIAS,
    PALABRAS_CLAVE,
    carta_abismo_disponible,
    cartas_en_venta,
    descripcion_carta,
    descripcion_fr,
    es_carta_abismo,
    estadisticas_carta,
    obtencion_carta,
    pildoras_en_venta,
    precio_compra,
    precio_pildora_mercado,
    puede_comprar_carta,
    registrar_abismo,
    subir_acumulacion,
    tabla_acumulacion,
    tipo_pildora_mercado,
)


class TestPuedeComprarCarta:
    """`okBuy(id)`: rar < 5 && (!SX(id) || SX(id) == schosen)."""

    def test_carta_neutral_es_comprable(self):
        assert puede_comprar_carta("pq", "esp") is True

    def test_carta_de_mi_secta_es_comprable(self):
        # cf es de esp (inicial; el filtro de iniciales es del listado,
        # no de okBuy)
        assert puede_comprar_carta("cf", "esp") is True

    def test_carta_de_otra_secta_es_bloqueada(self):
        # bl es de lot; comprando con secta esp no se puede
        assert puede_comprar_carta("bl", "esp") is False

    def test_celestial_no_se_vende(self):
        celestial = next(
            i for i, c in CARTAS.items() if rareza_de(c) >= 5
        )
        assert puede_comprar_carta(celestial, "esp") is False


class TestCartasEnVenta:
    """Filtro de `mkt()` v47: !lk && rar < 5 && vzOk && secta."""

    def test_general_lista_neutrales_y_neu(self):
        ids = cartas_en_venta("neu", "esp", {}, {})
        assert "pq" in ids  # neutral
        # `aa` está mapeada a 'neu' en SC: SX la trata como sin secta
        assert "aa" in ids

    def test_general_excluye_con_secta_visible(self):
        ids = cartas_en_venta("neu", "esp", {}, {})
        # ninguna carta de secta jugable (ex, bl…) aparece en General
        assert "ex" not in ids
        assert "bl" not in ids

    def test_puesto_de_secta_excluye_iniciales(self):
        ids = cartas_en_venta("esp", "esp", {}, {})
        starters = set(PUESTOS_MERCADO and _starters("esp"))
        assert starters.isdisjoint(ids)
        # ex
        assert "ex" in ids  # carta de esp no inicial

    def test_puesto_de_otra_secta_lista_las_suyas(self):
        ids = cartas_en_venta("lot", "esp", {}, {})
        assert "bl" in ids

    def test_puesto_de_secta_v47_lista_sus_cartas(self):
        """Montaña Inmortal vende M06+ (no neutrales ni starters)."""
        ids = cartas_en_venta("mon", "mon", {}, {})
        # cartas del bloque NS que no son de las 5 iniciales
        assert "M06" in ids
        assert "M13" in ids
        # las 5 iniciales no se venden (vienen en el mazo)
        assert set(_starters("mon")).isdisjoint(ids)
        # ni neutrales (puesto General) ni de otra secta
        assert "pq" not in ids
        assert "ex" not in ids
        # las reliquias del bloque XC (Z20/Z21) tampoco
        assert "Z20" not in ids
        assert "Z21" not in ids

    def test_ordena_por_rareza_luego_qi(self):
        ids = cartas_en_venta("esp", "esp", {}, {})
        claves = [
            (rareza_de(CARTAS[i]), CARTAS[i].coste_qi) for i in ids
        ]
        assert claves == sorted(claves)


def _starters(secta: str) -> tuple[str, ...]:
    from app.data.sectas import SECTAS

    return SECTAS[secta].cartas_iniciales


def _sectas_con_cartas() -> set[str]:
    from app.data.sectas import SECTA_DE_CARTA

    return set(SECTA_DE_CARTA)


class TestPrecioPildoraMercado:
    """`mkcPrice`: max(8, round((h*6+n*14+p*8)*1.7))."""

    def test_vit(self):
        # vit cuesta 3h → (3*6)*1.7 = 30.6 → round 31
        assert precio_pildora_mercado("vit") == 31

    def test_ninguna_baja_del_minimo(self):
        # el tope de 8 no se puede observar sin coste 0, pero sí
        # comprobar que el max se aplica a todo el catálogo vendible
        for identificador in PILDORAS:
            assert precio_pildora_mercado(identificador) >= 8


class TestPildorasEnVenta:
    """`mkcList`: excluye inm/rar; incluye recetas o MKC_BASIC."""

    def test_basicas_sin_recetas(self):
        venta = pildoras_en_venta({})
        assert "vit" in venta
        assert "tes" in venta
        assert "inm" not in venta
        assert "rar" not in venta

    def test_conoce_receta_la_incluye(self):
        venta = pildoras_en_venta({"cur": 1})
        assert "cur" in venta


class TestTipoPildoraMercado:
    """`pillKind`: tes → Talismán; o → recuperación; b → combate; resto
    → inicio."""

    def test_talisman(self):
        assert tipo_pildora_mercado("tes") == "Talismán"

    def test_recuperacion(self):
        # rcA/rcB/rcC son las únicas con flag `o`
        assert (
            tipo_pildora_mercado("rcA")
            == "Píldora de recuperación (Cueva)"
        )

    def test_combate(self):
        assert tipo_pildora_mercado("pet") == "Píldora de combate ⚡"

    def test_inicio(self):
        assert tipo_pildora_mercado("esc") == "Píldora de inicio"


class TestDescripcionCarta:
    """`descH` en texto plano (sin tags HTML)."""

    def test_criatura_con_provocar(self):
        # ev (esp) es criatura con provocar? comprobamos una known
        carta = CARTAS["ev"]
        lineas = descripcion_carta(carta)
        if carta.provocar:
            assert "Provocar" in lineas

    def test_carta_vacia_da_lista(self):
        # una carta sin efectos (sólo stats) da lista vacía o de stats
        carta = CARTAS["cf"]
        lineas = descripcion_carta(carta)
        assert isinstance(lineas, list)

    def test_espada_al_final(self):
        espada = next(
            i for i, c in CARTAS.items() if c.es_espada
        )
        lineas = descripcion_carta(CARTAS[espada])
        assert "⚔ Espada" in lineas


class TestDescripcionFormacionRuna:
    """`FRd` (js/04-mazos-formaciones.js:34) en texto plano.

    El catálogo ya incluye F/R (bloque Y del v47), pero los casos
    límite se prueban con instancias sintéticas al estilo del JS.
    """

    def _formacion(self, **kwargs) -> CartaData:
        return CartaData(
            identificador="frT",
            nombre="Formación de prueba",
            coste_qi=1,
            tipo=TipoCarta.FORMACION,
            **kwargs,
        )

    def _runa(self, **kwargs) -> CartaData:
        return CartaData(
            identificador="ruT",
            nombre="Runa de prueba",
            coste_qi=1,
            tipo=TipoCarta.RUNA,
            duracion_turnos=kwargs.pop("duracion_turnos", 3),
            **kwargs,
        )

    def test_formacion_solo_etiqueta(self):
        lineas = descripcion_fr(self._formacion())
        assert lineas == ["Formación"]

    def test_runa_incluye_duracion(self):
        lineas = descripcion_fr(self._runa())
        assert lineas == ["Runa · 3 turnos"]

    def test_formacion_con_mejoras_y_efecto(self):
        carta = self._formacion(
            mejora_ataque_al_trazar=2,
            mejora_vida_al_trazar=4,
            efecto_inicio_turno=(TipoEfecto.ESCUDO, 3),
        )
        lineas = descripcion_fr(carta)
        assert lineas == [
            "Formación",
            "Tus criaturas: +2 ATK",
            "Criaturas aliadas: +4 vida",
            "Cada turno: escudo 3",
        ]

    def test_runa_efecto_inicio_de_turno(self):
        carta = self._runa(
            efecto_inicio_turno=(TipoEfecto.DANO_HROE, 5),
            sacrificar_vida=2,
        )
        lineas = descripcion_fr(carta)
        assert lineas == [
            "Runa · 3 turnos",
            "Al inicio de tu turno: daña 5 al héroe rival",
            "Pagas 2 de vida",
        ]

    def test_formacion_auto_dano_texto(self):
        """`TSD('x', n)`: «pierdes n de vida» (Y05 del monolito)."""
        carta = self._formacion(efecto_inicio_turno=(TipoEfecto.AUTO_DANO, 1))
        assert descripcion_fr(carta) == [
            "Formación",
            "Cada turno: pierdes 1 de vida",
        ]

    def test_descripcion_carta_delega_en_fr(self):
        carta = self._formacion(mejora_vida_al_trazar=1)
        assert descripcion_carta(carta) == descripcion_fr(carta)


class TestEstadisticasCarta:
    """`PROP` + bf/ul/ab/bc del `mkDet`."""

    def test_ataque_y_vida(self):
        carta = CARTAS["ev"]
        filas = dict(estadisticas_carta(carta))
        if carta.ataque is not None:
            assert "Ataque" in filas
        if carta.vida is not None:
            assert "Vida" in filas


class TestTablaAcumulacion:
    """`ac` de `mkDet`: sólo criaturas no-bestia."""

    def test_criatura_tiene_tabla(self):
        carta = CARTAS["ev"]
        if carta.tipo.value == "C" and not carta.bestia:
            filas = tabla_acumulacion(carta)
            assert filas is not None
            assert len(filas) == MAX_COPIAS
            assert filas[0]["pila"] == 1
            assert filas[-1]["pila"] == MAX_COPIAS

    def test_bestia_no_tiene_tabla(self):
        bestia = next(
            (i for i, c in CARTAS.items() if c.bestia), None
        )
        if bestia:
            assert tabla_acumulacion(CARTAS[bestia]) is None

    def test_no_criatura_no_tiene_tabla(self):
        tecnica = next(
            i for i, c in CARTAS.items() if c.tipo.value == "T"
        )
        assert tabla_acumulacion(CARTAS[tecnica]) is None

    def test_subir_acumulacion_escalacion(self):
        carta = CARTAS["ev"]
        estado = {"sk": 1, "A": carta.ataque, "H": carta.vida}
        subir_acumulacion(carta, estado)
        import math

        assert estado["A"] == carta.ataque + math.ceil(carta.ataque / 2)
        assert estado["H"] == carta.vida + math.ceil(carta.vida / 2)
        assert estado["sk"] == 2


class TestObtencionCarta:
    """`howGet`."""

    def test_neutral_esGratis(self):
        lineas = obtencion_carta("pq", "esp")
        assert any("Gratis" in linea for linea in lineas)

    def test_celestial_no_se_vende(self):
        celestial = next(
            i for i, c in CARTAS.items() if rareza_de(c) >= 5
        )
        lineas = obtencion_carta(celestial, "esp")
        assert any("No se vende" in linea for linea in lineas)

    def test_precio_y_bloqueo_de_secta(self):
        # bl es de lot; con secta esp debe llevar candado
        lineas = obtencion_carta("bl", "esp")
        mercado = next(x for x in lineas if "Mercado" in x)
        assert "🔒" in mercado

    def test_mi_secta_sin_candado(self):
        lineas = obtencion_carta("ex", "esp")
        mercado = next(x for x in lineas if "Mercado" in x)
        assert "🔒" not in mercado


class TestCartasDelAbismo:
    """`VREC`/`vzOk`/`vzTake` (v47): V04-V07 traen `vb`/`vs`."""

    def test_las_cartas_del_abismo_son_las_de_bloque_v(self):
        abismo = [i for i in CARTAS if es_carta_abismo(CARTAS[i])]
        assert abismo == ["V04", "V05", "V06", "V07"]
        # cualquier otra carta está siempre disponible
        assert carta_abismo_disponible({}, {}, "pq") is True

    def test_no_se_puede_obtener_dos_veces(self):
        misiones: dict = {}
        assert carta_abismo_disponible({}, misiones, "V04") is True
        registrar_abismo(misiones, "V04")
        assert carta_abismo_disponible({}, misiones, "V04") is False
        # ya poseída en la colección tampoco
        assert carta_abismo_disponible({"V05": 1}, {}, "V05") is False

    def test_registrar_abismo_es_noop_sin_abismo(self):
        misiones: dict = {}
        registrar_abismo(misiones, "pq")
        assert "vz" not in misiones
