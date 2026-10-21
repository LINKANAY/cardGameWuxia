"""Casos de uso de alquimia — recetario, forja, fusión y desmantelado.

Puerto del tab `alq` del monolito (`alq()`/`brew`/`forge`/`fuse`/`dis`
en `js/01-datos.js`). Toda mutación pasa por `SessionStore.mutate` para
que el auto-guardado sea infalible (decisión de la Fase 0).

El JS no da feedback de error (simplemente no hace nada); aquí cada
precondición violada lanza `ValidationError` con un código propio para
que la UI pueda explicar el fallo.
"""

from __future__ import annotations

import time

from app.core.errors import NotFoundError, ValidationError
from app.engine import rules
from app.engine.rng import GeneradorAleatorio
from app.engine.state import Partida
from app.state.session_store import SessionStore


class AlchemyService:
    """Orquesta las acciones de alquimia sobre la partida de un slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    def _asegurar_partida(self, slot: str) -> None:
        """404 si el slot no existe ni en memoria ni en disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    @staticmethod
    def _aleatorio():
        """Callback float aleatorio con semilla de tiempo.

        El JS usa `Math.random()` (no determinista); aquí el RNG del
        motor con semilla de nanosegundos cumple el mismo contrato y
        mantiene el algoritmo del monolito (mulberry32).
        """
        return GeneradorAleatorio(f"alq-{time.time_ns()}").random

    def elaborar(self, slot: str, pildora: str) -> dict:
        """Elabora una píldora (`brew(k)` del JS).

        Args:
            slot: slot de la partida.
            pildora: id en `PILDORAS`; debe tener receta aprendida.

        Returns:
            Dict con `mensaje` (texto del monolito) y `snapshot`.

        Raises:
            ValidationError: píldora desconocida, receta no aprendida o
                materiales insuficientes.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            if pildora not in rules.PILDORAS:
                raise ValidationError(
                    f"Píldora desconocida: '{pildora}'",
                    code="pildora_desconocida",
                )
            if not partida.recetas.get(pildora):
                raise ValidationError(
                    f"No conoces la receta de {pildora}",
                    code="receta_no_aprendida",
                )
            if not rules.puede_pagar(
                rules.PILDORAS[pildora].coste, partida.materiales
            ):
                raise ValidationError(
                    "Materiales insuficientes para elaborarla",
                    code="materiales_insuficientes",
                )
            rules.elaborar_pildora(
                partida.pildoras,
                partida.recetas,
                partida.materiales,
                pildora,
            )
            partida.misiones["br"] = partida.misiones.get("br", 0) + 1
            return f"Elaboraste: {rules.PILDORAS[pildora].nombre}"

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def forjar(self, slot: str, rareza: int) -> dict:
        """Forja una carta aleatoria de la rareza dada (`forge(r)`).

        Args:
            slot: slot de la partida.
            rareza: índice 0–5.

        Returns:
            Dict con `mensaje`, `carta` (id obtenida) y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> tuple[str, str]:
            if not rules.puede_forjar(rareza, partida.materiales):
                raise ValidationError(
                    "Materiales insuficientes para forjar",
                    code="materiales_insuficientes",
                )
            resultado = rules.forjar_carta(
                partida.coleccion,
                partida.materiales,
                rareza,
                self._aleatorio(),
                partida.misiones,
            )
            mensaje = (
                f"Forjaste: {resultado.nombre} ({rules.RAREZAS[rareza]})"
            )
            return mensaje, resultado.identificador

        mensaje, carta = self._store.mutate(slot, mutador)
        return {
            "mensaje": mensaje,
            "carta": carta,
            "snapshot": self._store.snapshot(slot),
        }

    def fusionar(self, slot: str, carta: str) -> dict:
        """Fusiona 3 copias en una carta de rareza superior (`fuse`).

        Args:
            slot: slot de la partida.
            carta: id de la carta a fusionar (≥3 copias, rareza < 5).

        Returns:
            Dict con `mensaje`, `carta` (id obtenida) y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> tuple[str, str]:
            if carta not in rules.CARTAS:
                raise ValidationError(
                    f"Carta desconocida: '{carta}'", code="carta_desconocida"
                )
            if partida.coleccion.get(carta, 0) < 3:
                raise ValidationError(
                    "Necesitas al menos 3 copias para fusionar",
                    code="coleccion_insuficiente",
                )
            if rules.rareza_de(rules.CARTAS[carta]) >= 5:
                raise ValidationError(
                    "Las cartas Celestiales no se fusionan",
                    code="rareza_maxima",
                )
            resultado = rules.fusionar_coleccion(
                partida.coleccion,
                partida.materiales,
                carta,
                self._aleatorio(),
                partida.misiones,
            )
            nueva_rareza = rules.rareza_de(rules.CARTAS[carta]) + 1
            mensaje = (
                f"Fusión: obtuviste {resultado.nombre} "
                f"({rules.RAREZAS[nueva_rareza]})"
            )
            return mensaje, resultado.identificador

        mensaje, obtenida = self._store.mutate(slot, mutador)
        return {
            "mensaje": mensaje,
            "carta": obtenida,
            "snapshot": self._store.snapshot(slot),
        }

    def desmantelar(self, slot: str, carta: str) -> dict:
        """Desmantela una copia en polvo de jade (`dis(id)`).

        Args:
            slot: slot de la partida.
            carta: id de la carta a desmantelar.

        Returns:
            Dict con `mensaje`, `polvo` (ganado) y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> tuple[str, int]:
            if carta not in rules.CARTAS:
                raise ValidationError(
                    f"Carta desconocida: '{carta}'", code="carta_desconocida"
                )
            if not partida.coleccion.get(carta):
                raise ValidationError(
                    "No tienes copias para desmantelar",
                    code="coleccion_insuficiente",
                )
            polvo = rules.desmantelar_coleccion(
                partida.coleccion, partida.materiales, carta
            )
            nombre = rules.CARTAS[carta].nombre
            mensaje = f"Desmantelaste {nombre}: +{polvo} polvo de jade"
            return mensaje, polvo

        mensaje, polvo = self._store.mutate(slot, mutador)
        return {
            "mensaje": mensaje,
            "polvo": polvo,
            "snapshot": self._store.snapshot(slot),
        }
