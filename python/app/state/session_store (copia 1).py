"""Registro de partidas en memoria con auto-save.

- `get_or_create(slot)`: carga de disco (`SaveRepo`) o crea `Partida` nueva.
- `mutate(slot, mutador)`: aplica `mutador(partida)` y guarda
  automáticamente
  (patrón elegido en la Fase 0: la UI nunca muta estado sin pasar por aquí).
- `snapshot(slot)`: dict `data` listo para la API (formato `xcg3`).
- `save_all()`: vuelca todas las partidas en memoria (se llama en el
  `shutdown` del lifespan de FastAPI).

El `SaveRepo` envuelve en ``{v, t, data}`` (idéntico al `save()` del
monolito); aquí sólo manejamos el objeto `Partida` y su `a_dict()`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.logging import get_logger
from app.engine.state import Partida
from app.repositories import save_repo

logger = get_logger("session_store")


class SessionStore:
    """Caché en memoria de `Partida` por slot, con persistencia automática."""

    def __init__(self) -> None:
        self._partidas: dict[str, Partida] = {}

    def exists(self, slot: str) -> bool:
        """¿Hay partida en memoria o en disco para este slot?"""
        return slot in self._partidas or save_repo.load(slot) is not None

    def obtener(self, slot: str) -> Partida | None:
        """`Partida` en memoria; None si nunca se cargó/creó."""
        return self._partidas.get(slot)

    def get_or_create(self, slot: str) -> Partida:
        """Carga de disco o crea partida nueva con defaults de `Partida`."""
        if slot not in self._partidas:
            data = save_repo.load(slot)
            self._partidas[slot] = Partida.desde_dict(data)
            if data is None:
                logger.info("slot=%s partida nueva", slot)
        return self._partidas[slot]

    def create(self, slot: str) -> Partida:
        """Fuerza una partida nueva (descarta la previa en memoria y disco)."""
        partida = Partida()
        self._partidas[slot] = partida
        save_repo.save(slot, partida.a_dict())
        logger.info("slot=%s partida reiniciada", slot)
        return partida

    def mutate(
        self, slot: str, mutador: Callable[[Partida], Any]
    ) -> Any:
        """Aplica `mutador` a la partida y auto-guarda su resultado.

        Todas las escrituras de negocio deben pasar por aquí para que el
        auto-guardado sea infalible (decisión de la Fase 0).
        """
        partida = self.get_or_create(slot)
        resultado = mutador(partida)
        save_repo.save(slot, partida.a_dict())
        return resultado

    def snapshot(self, slot: str) -> dict:
        """Dict `data` de la partida (formato `xcg3`) sin tocar disco."""
        return self.get_or_create(slot).a_dict()

    def drop(self, slot: str) -> None:
        """Descarta la partida en memoria (no borra el archivo)."""
        self._partidas.pop(slot, None)

    def save_all(self) -> int:
        """Guarda todas las partidas en memoria. Devuelve cuántas se guardaron."""
        guardadas = 0
        for slot, partida in self._partidas.items():
            if save_repo.save(slot, partida.a_dict()):
                guardadas += 1
        return guardadas
