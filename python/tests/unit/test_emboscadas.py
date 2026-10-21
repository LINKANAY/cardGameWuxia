"""Tests puros del núcleo de emboscadas (`ambRoll`/`mkAmb`/`mkBot`)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.data.niveles import ENEMIGOS, TEXTO_HABILIDAD_ENEMIGO
from app.data.pildoras import PILDORAS
from app.data.sectas import SECTAS
from app.engine import emboscadas
from app.engine.emboscadas import (
    NOMBRES_ALQUIMISTA,
    NOMBRES_BOTICARIO,
    RECETAS_RECUPERACION,
    Sorteo,
)
from app.engine.state import Partida


class _Secuencia:
    """RNG de guion: devuelve valores fijos y cuenta los rolls."""

    def __init__(self, *valores: float):
        self.valores = list(valores)
        self.rolls = 0

    def __call__(self) -> float:
        self.rolls += 1
        if not self.valores:
            raise AssertionError("rolls agotados: sobra un Math.random()")
        return self.valores.pop(0)

    @property
    def agotada(self) -> bool:
        return not self.valores


def _recetas_todas_menos(*excluidas: str) -> dict[str, int]:
    """`rec` con todas las píldoras aprendidas salvo las excluidas."""
    return {
        ident: 1 for ident in PILDORAS if ident not in excluidas
    }


class TestSortearAmboscada:
    def _sortear(self, rol: _Secuencia, **kwargs):
        opciones = {
            "recetas": {"vit": 1},
            "dificultad": 0,
            "es_mazmorra": False,
            "es_amboscada": False,
        }
        opciones.update(kwargs)
        return emboscadas.sortear_amboscada(rol, **opciones)

    @pytest.mark.parametrize(
        "puerta",
        [
            {"es_mazmorra": True},
            {"es_amboscada": True},
            {"es_tribulacion": True},
        ],
    )
    def test_puertas_sin_tirada(self, puerta):
        """Mazmorra, emboscada encadenada y tribulación ni tiran."""
        rol = _Secuencia()
        assert self._sortear(rol, **puerta) is None
        assert rol.rolls == 0

    def test_tirada_en_el_umbral_no_embosca(self):
        # `Math.random() >= .22` → fuera; por debajo sí embosca.
        assert self._sortear(_Secuencia(0.22)) is None
        sorteo = self._sortear(_Secuencia(0.2199, 0.9, 0.0))
        assert sorteo is not None

    def test_umbral_crece_con_la_dificultad(self):
        # d=5 → umbral .47: cabe por debajo, no por encima.
        sorteo = self._sortear(
            _Secuencia(0.4699, 0.9, 0.0), dificultad=5
        )
        assert sorteo is not None
        assert self._sortear(_Secuencia(0.47), dificultad=5) is None

    def test_alquimista_cuota_fallida_elige_legacy(self):
        # Sólo queda `qi2` sin aprender → el índice cae siempre en ella.
        rol = _Secuencia(0.0, 0.9, 0.99)  # puerta, cuota (≥.5), índice
        sorteo = self._sortear(
            rol, recetas=_recetas_todas_menos("qi2")
        )
        assert sorteo == Sorteo(tipo="alquimista", receta="qi2")
        assert sorteo.boticario is False
        assert rol.rolls == 3 and rol.agotada

    def test_boticario_sin_legacy_omite_la_cuota(self):
        # legacy vacío → sin tirada de `BOT.share` (cortocircuito JS).
        rol = _Secuencia(0.0, 0.5)  # puerta, índice (pozo completo)
        sorteo = self._sortear(rol, recetas=_recetas_todas_menos())
        assert sorteo.tipo == "boticario"
        assert sorteo.receta in RECETAS_RECUPERACION
        assert rol.rolls == 2 and rol.agotada

    def test_boticario_pozo_de_recuperaciones_sin_aprender(self):
        # Aprendidas las no-recuperación y rcA → pozo (rcB, rcC).
        recetas = _recetas_todas_menos("rcB", "rcC")
        rol = _Secuencia(0.0, 0.1, 0.6)  # puerta, pozo (<.8), índice
        sorteo = self._sortear(rol, recetas=recetas)
        assert sorteo == Sorteo(tipo="boticario", receta="rcC")
        assert rol.rolls == 3 and rol.agotada

    def test_boticario_pozo_completo_si_estan_todas(self):
        # Sin recuperaciones libres no hay tirada de pozo (`.8` corto).
        recetas = _recetas_todas_menos()
        rol = _Secuencia(0.0, 0.99)  # puerta, índice
        sorteo = self._sortear(rol, recetas=recetas)
        assert sorteo == Sorteo(
            tipo="boticario",
            receta=RECETAS_RECUPERACION[
                int(0.99 * len(RECETAS_RECUPERACION))
            ],
        )
        assert rol.rolls == 2 and rol.agotada

    def test_boticario_por_cuota_con_legacy(self):
        # Legacy = qi2 (las recuperaciones ya están aprendidas → no
        # hay pozo libre), cuota baja → boticario con el índice final.
        recetas = _recetas_todas_menos("qi2")
        rol = _Secuencia(0.0, 0.1, 0.9)  # puerta, cuota (<.5), índice
        sorteo = self._sortear(rol, recetas=recetas)
        assert sorteo == Sorteo(
            tipo="boticario",
            receta=RECETAS_RECUPERACION[
                int(0.9 * len(RECETAS_RECUPERACION))
            ],
        )
        assert rol.rolls == 3 and rol.agotada


class TestConstruirEnemigo:
    def _previo(self, indice: int):
        return ENEMIGOS[indice]

    def test_formulas_de_la_ficha(self):
        previo = self._previo(5)  # li 0, d 5, rw 3
        rol = _Secuencia(0.0, 0.0, 0.0, 0.0)
        enemigo = emboscadas.construir_enemigo(
            previo, receta="rcB", boticario=False, aleatorio=rol
        )
        assert enemigo.dificultad == 5  # min(5, 5 + 1)
        # redondear_js(16 * 1.7 * 1.05) = redondear_js(28.56…)
        assert enemigo.vida == 29
        assert enemigo.capacidad == 10  # min(10, 5 + 5)
        assert enemigo.rareza_recompensa == 4  # min(5, 3 + 1)
        assert enemigo.receta == "rcB"
        assert enemigo.es_emboscada is True
        assert enemigo.es_boticario is False
        assert enemigo.indice_mazmorra is None
        assert enemigo.indice_mision is None
        assert enemigo.historia is None
        assert enemigo.nombre_nivel == "Emboscada de un alquimista"

    def test_rolls_en_orden_y_deduplicacion(self):
        # d→1 (<3): una sola habilidad; rolls = hab, nombre, secta.
        rol = _Secuencia(0.0, 0.0, 0.0)
        enemigo = emboscadas.construir_enemigo(
            self._previo(0), receta="qi2", boticario=False, aleatorio=rol
        )
        assert rol.rolls == 3 and rol.agotada
        assert enemigo.habilidades == ("heal",)
        assert enemigo.nombre_enemigo == NOMBRES_ALQUIMISTA[0]
        assert enemigo.secta == "esp"

    def test_dificultad_alta_tira_dos_habilidades(self):
        # d→3 (≥3): dos rolls de habilidad aunque repitan (dedup después).
        rol = _Secuencia(0.0, 0.0, 0.0, 0.0)
        enemigo = emboscadas.construir_enemigo(
            self._previo(2), receta="qi2", boticario=False, aleatorio=rol
        )
        assert rol.rolls == 4 and rol.agotada
        assert enemigo.habilidades == ("heal",)  # Set([heal, heal])
        assert enemigo.dificultad == 3

    def test_boticario_tira_su_nombre_al_final(self):
        # d→1 (<3): hab, nombre de alquimista, secta y nombre final.
        rol = _Secuencia(0.0, 0.0, 0.0, 0.0)
        enemigo = emboscadas.construir_enemigo(
            self._previo(0), receta="rcA", boticario=True, aleatorio=rol
        )
        assert rol.rolls == 4 and rol.agotada
        assert enemigo.nombre_enemigo == NOMBRES_BOTICARIO[0]
        assert enemigo.nombre_nivel == "Encuentro con un boticario"
        assert enemigo.frase_inicio == (
            "Hierbas, humo y un precio. ¿Qué ofreces?"
        )
        assert enemigo.es_boticario is True

    def test_texto_de_habilidades_y_secta_valida(self):
        rol = _Secuencia(0.5, 0.5, 0.5)
        enemigo = emboscadas.construir_enemigo(
            self._previo(0), receta="rcB", boticario=False, aleatorio=rol
        )
        assert enemigo.secta in SECTAS
        assert enemigo.texto_habilidades.endswith(".")
        assert (
            TEXTO_HABILIDAD_ENEMIGO[enemigo.habilidades[0]]
            in enemigo.texto_habilidades
        )

    def test_las_fichas_originales_no_se_mutan(self):
        previo = self._previo(0)
        emboscadas.construir_enemigo(
            previo, receta="rcB", boticario=False, aleatorio=_Secuencia(
                0.0, 0.0, 0.0
            )
        )
        assert previo.es_emboscada is False
        assert previo.dificultad == 0


class TestAplicarBoticario:
    def test_sin_boticario_no_hace_nada(self):
        partida = Partida()
        rol = _Secuencia(0.0)  # no debe tirar
        resumen = emboscadas.aplicar_boticario(
            partida,
            replace(ENEMIGOS[0]),
            receta_aprendida=None,
            aleatorio=rol,
        )
        assert resumen is None
        assert "bt" not in partida.misiones
        assert rol.rolls == 0

    def test_receta_nueva_sin_tirada_ni_pildora(self):
        partida = Partida()
        enemigo = replace(
            ENEMIGOS[0], es_boticario=True, es_emboscada=True, receta="rcB"
        )
        rol = _Secuencia()  # no debe tirar: `!found` corta
        resumen = emboscadas.aplicar_boticario(
            partida, enemigo, receta_aprendida="rcB", aleatorio=rol
        )
        assert resumen == {"pildora": None}
        assert partida.misiones["bt"] == 1
        assert rol.rolls == 0
        assert "rcB" not in partida.pildoras

    def test_pildora_de_regalo_si_la_receta_ya_se_conocia(self):
        partida = Partida()
        enemigo = replace(
            ENEMIGOS[0], es_boticario=True, es_emboscada=True, receta="rcC"
        )
        resumen = emboscadas.aplicar_boticario(
            partida, enemigo, receta_aprendida=None, aleatorio=_Secuencia(0.3)
        )
        assert resumen == {"pildora": "rcC"}
        assert partida.pildoras["rcC"] == 1
        assert partida.misiones["bt"] == 1

    def test_sin_suerte_no_regala_pildora(self):
        partida = Partida()
        enemigo = replace(
            ENEMIGOS[0], es_boticario=True, es_emboscada=True, receta="rcA"
        )
        resumen = emboscadas.aplicar_boticario(
            partida, enemigo, receta_aprendida=None, aleatorio=_Secuencia(0.35)
        )
        assert resumen == {"pildora": None}
        assert "rcA" not in partida.pildoras
