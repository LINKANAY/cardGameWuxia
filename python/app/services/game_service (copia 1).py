"""Casos de uso de partida — crear, leer snapshot, mutar con auto-save.

La lógica de negocio (compras, mazos, victorias…) se irá añadiendo aquí
en fases posteriores; por ahora: crear/reiniciar, leer el snapshot,
listar slots y borrar partidas.
"""

from __future__ import annotations

from app.core.errors import NotFoundError, ValidationError
from app.data.sectas import SECTAS
from app.engine.state import Partida
from app.repositories import save_repo
from app.schemas.game import SlotResumen
from app.state.session_store import SessionStore


class GameService:
    """Casos de uso de la capa de juego (orquesta `SessionStore`)."""

    def __init__(self, store: SessionStore):
        self._store = store

    def new_game(self, slot: str) -> dict:
        """Crea (o reinicia) la partida del slot y devuelve su snapshot."""
        partida = self._store.create(slot)
        return partida.a_dict()

    def confirmar_secta(self, slot: str, clave: str) -> dict:
        """Fija la secta elegida en la puerta (`confirmS` del JS).

        Réplica de `js/06-contenido.js:72`: `schosen = sect = selS`
        y regalo de un Talismán de Escape (`pil.tes += 1`).

        Args:
            slot: partida a mutar (auto-guardado incluido).
            clave: identificador de la secta del catálogo.

        Returns:
            Snapshot actualizado (`data` xcg3).

        Raises:
            NotFoundError: si la partida no existe.
            ValidationError: si la clave no está en el catálogo.
        """
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")
        if clave not in SECTAS:
            raise ValidationError(
                f"Secta desconocida: '{clave}'", code="secta_invalida"
            )

        def mutador(partida: Partida) -> dict:
            partida.secta = clave
            partida.secta_elegida_confirmada = clave
            partida.pildoras["tes"] = partida.pildoras.get("tes", 0) + 1
            return partida.a_dict()

        return self._store.mutate(slot, mutador)

    def snapshot(self, slot: str) -> dict:
        """Snapshot `data` de la partida; 404 si no existe en memoria ni disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")
        return self._store.snapshot(slot)

    def partida(self, slot: str) -> Partida:
        """Objeto `Partida` (para servicios que muten estado)."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")
        return self._store.get_or_create(slot)

    def exists(self, slot: str) -> bool:
        return self._store.exists(slot)

    def list_slots(self) -> list[SlotResumen]:
        """Resúmenes de los slots con guardado en disco (orden alfabético).

        Los saves corruptos o ilegibles se omiten: no hay nada que
        mostrar para ellos (el usuario podrá recrearlos desde la UI).
        """
        resumenes: list[SlotResumen] = []
        for slot in save_repo.list_slots():
            datos = save_repo.load(slot)
            if datos is None:
                continue
            resumenes.append(
                SlotResumen(
                    slot=slot,
                    nivel_reino=int(datos.get("realm") or 0),
                    secta=str(datos.get("sect") or "esp"),
                    victorias=len(datos.get("wins") or []),
                )
            )
        return resumenes

    def delete_game(self, slot: str) -> None:
        """Borra la partida: saca la copia en memoria y borra el archivo.

        Raises:
            NotFoundError: si el slot no existía ni en memoria ni en disco.
        """
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")
        self._store.drop(slot)
        save_repo.delete(slot)
