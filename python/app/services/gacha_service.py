"""Casos de uso del gacha — la Ceremonia de Adivinación Ancestral.

Puerto del modal `.gachab` del monolito (`GachaSystem.draw` en
`js/14-gacha.js`). Toda mutación pasa por `SessionStore.mutate` para
que el auto-guardado sea infalible (decisión de la Fase 0).

El JS avisa por toast si faltan tickets y no hace nada; aquí esa
precondición lanza `ValidationError` con código propio.
"""

from __future__ import annotations

import time

from app.core.errors import NotFoundError, ValidationError
from app.data.gacha import POOLS, TICKETS
from app.engine import rules
from app.engine.rng import GeneradorAleatorio
from app.engine.state import Partida
from app.state.session_store import SessionStore


class GachaService:
    """Orquesta las tiradas del gacha sobre la partida de un slot."""

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
        return GeneradorAleatorio(f"gch-{time.time_ns()}").random

    def tirar(self, slot: str, pool_clave: str, count: int) -> dict:
        """Ejecuta una tirada del gacha (`GachaSystem.draw`).

        Args:
            slot: slot de la partida.
            pool_clave: `'STANDARD'` o `'PREMIUM'`.
            count: nº de invocaciones (1 o 10).

        Returns:
            Dict con `mensaje` (texto del monolito), `resultados`
            (lista de recompensas), `tickets_restantes`,
            `piedad` y `snapshot`.

        Raises:
            ValidationError: pool desconocido, count inválido o
                tickets insuficientes.
        """
        self._asegurar_partida(slot)

        if pool_clave not in POOLS:
            raise ValidationError(
                f"Pool de gacha desconocida: '{pool_clave}'",
                code="pool_desconocida",
            )
        if count not in (1, 10):
            raise ValidationError(
                "Sólo se puede invocar 1 o 10 veces",
                code="cantidad_invalida",
            )

        pool = POOLS[pool_clave]
        coste = pool.coste_por_tirada * count

        def mutador(partida: Partida) -> dict:
            entradas = partida.entradas_gacha.get(pool.tipo_ticket, 0)
            if entradas < coste:
                nombre_ticket = TICKETS[pool.tipo_ticket].nombre
                raise ValidationError(
                    f"No tienes suficientes {nombre_ticket}",
                    code="tickets_insuficientes",
                )
            partida.entradas_gacha[pool.tipo_ticket] = entradas - coste

            clave_piedad = pool.piedad.clave
            piedad = partida.piedad_gacha.get(clave_piedad, 0)
            aleatorio = self._aleatorio()
            resultados: list[dict] = []
            for indice in range(count):
                rareza, piedad = rules.sortear_rareza_gacha(
                    pool, indice, count, piedad, aleatorio
                )
                recompensa = rules.generar_recompensa_gacha(
                    rareza,
                    partida.coleccion,
                    partida.materiales,
                    aleatorio,
                    partida.misiones,
                )
                resultados.append(
                    {
                        "tipo": recompensa.tipo,
                        "carta": recompensa.identificador,
                        "nombre": recompensa.nombre,
                        "rareza": recompensa.rareza,
                        "descripcion": recompensa.descripcion,
                    }
                )
            partida.piedad_gacha[clave_piedad] = piedad
            return {
                "resultados": resultados,
                "tickets_restantes": partida.entradas_gacha.get(
                    pool.tipo_ticket, 0
                ),
                "piedad": piedad,
            }

        datos = self._store.mutate(slot, mutador)
        mensaje = (
            f"✨ Ceremonia Completada — Has obtenido "
            f"{len(datos['resultados'])} Ecos del Sendero."
        )
        return {
            "mensaje": mensaje,
            **datos,
            "snapshot": self._store.snapshot(slot),
        }
