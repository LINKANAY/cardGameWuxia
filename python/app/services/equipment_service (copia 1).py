"""Casos de uso de equipo y trajes — Herrería, huecos y armario.

Puerto de las pestañas `eqp`/`trj` del monolito (`eqpUI`/`forgeG`/
`wearG`/`eqB`/`wear` en js/06-contenido.js). Toda mutación pasa por
`SessionStore.mutate` para que el auto-guardado sea infalible.

El JS no da feedback de error (simplemente no hace nada); aquí cada
precondición violada lanza `ValidationError` con código propio para
que la UI pueda explicar el fallo.
"""

from __future__ import annotations

from app.core.errors import NotFoundError, ValidationError
from app.data.bestias import BESTIAS_DOMADAS
from app.data.equipo import PiezaData, pieza
from app.data.trajes import TrajeData, traje
from app.engine import rules
from app.engine.state import Partida
from app.state.session_store import SessionStore


class EquipmentService:
    """Orquesta las acciones de equipo sobre la partida de un slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    def _asegurar_partida(self, slot: str) -> None:
        """404 si el slot no existe ni en memoria ni en disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    @staticmethod
    def _pieza(identificador: str) -> PiezaData:
        objetivo = pieza(identificador)
        if objetivo is None:
            raise ValidationError(
                f"Pieza de equipo desconocida: '{identificador}'",
                code="pieza_desconocida",
            )
        return objetivo

    def forjar(self, slot: str, identificador: str) -> dict:
        """Forja una pieza de la Herrería (`forgeG(id)`).

        Args:
            slot: slot de la partida.
            identificador: id de la pieza (`G1`…`G17`).

        Returns:
            Dict con `mensaje` y `snapshot`.

        Raises:
            ValidationError: pieza desconocida, ya poseída, plano
                bloqueado o materiales insuficientes.
        """
        self._asegurar_partida(slot)
        objetivo = self._pieza(identificador)

        def mutador(partida: Partida) -> str:
            if partida.equipo_guardado.get(identificador):
                raise ValidationError(
                    f"Ya has forjado {objetivo.nombre}",
                    code="pieza_ya_poseida",
                )
            if not rules.pieza_desbloqueada(objetivo, partida.victorias):
                nivel = objetivo.desbloqueo // 6 + 1
                raise ValidationError(
                    f"Plano bloqueado: vence al jefe del Nivel {nivel}",
                    code="pieza_bloqueada",
                )
            if not rules.puede_pagar(objetivo.coste, partida.materiales):
                raise ValidationError(
                    "Materiales insuficientes para forjarla",
                    code="materiales_insuficientes",
                )
            rules.forjar_pieza(
                partida.equipo_guardado,
                partida.equipado,
                partida.usos_equipo,
                partida.materiales,
                partida.victorias,
                identificador,
            )
            return f"Forjaste: {objetivo.nombre}"

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def equipar(self, slot: str, identificador: str) -> dict:
        """Equipa o retira una pieza poseída (`wearG(id)`; alterna).

        Args:
            slot: slot de la partida.
            identificador: id de la pieza; debe estar forjada.

        Returns:
            Dict con `mensaje` y `snapshot`.

        Raises:
            ValidationError: pieza desconocida o no forjada.
        """
        self._asegurar_partida(slot)
        objetivo = self._pieza(identificador)

        def mutador(partida: Partida) -> str:
            if not partida.equipo_guardado.get(identificador):
                raise ValidationError(
                    f"Todavía no has forjado {objetivo.nombre}",
                    code="pieza_no_poseida",
                )
            puesto = partida.equipado.get(objetivo.slot) == identificador
            rules.equipar_pieza(partida.equipado, identificador)
            if puesto:
                return f"Retiraste: {objetivo.nombre}"
            return f"Equipaste: {objetivo.nombre}"

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def equipar_bestia(self, slot: str, bestia: str | None) -> dict:
        """Equipa o retira la bestia de ayuda (`eqB(id)`; alterna).

        Args:
            slot: slot de la partida.
            bestia: id de la bestia (`BS1`…`BS8`) o `None` para
                retirar la equipada.

        Returns:
            Dict con `mensaje` y `snapshot`.

        Raises:
            ValidationError: bestia desconocida o no domada (su jefe).
        """
        self._asegurar_partida(slot)
        catalogo = {b.identificador: b for b in BESTIAS_DOMADAS}
        if bestia is not None and bestia not in catalogo:
            raise ValidationError(
                f"Bestia desconocida: '{bestia}'", code="bestia_desconocida"
            )

        def mutador(partida: Partida) -> str:
            if bestia is None:
                partida.bestia_equipada = None
                return "Retiraste tu bestia de ayuda"
            objetivo = catalogo[bestia]
            if not rules.bestia_desbloqueada(objetivo, partida.victorias):
                raise ValidationError(
                    f"Vence al jefe del Nivel {objetivo.indice_nivel + 1} "
                    "para domarla",
                    code="bestia_bloqueada",
                )
            if partida.bestia_equipada == bestia:
                partida.bestia_equipada = None
                return f"Retiraste: {objetivo.nombre}"
            partida.bestia_equipada = bestia
            return f"Equipaste: {objetivo.nombre}"

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def vestir(self, slot: str, secta: str, indice: int) -> dict:
        """Viste un traje del armario de la secta del jugador (`wear`).

        Args:
            slot: slot de la partida.
            secta: secta del traje; debe ser la del jugador (el
                armario solo muestra los trajes propios).
            indice: índice del traje (0–5).

        Returns:
            Dict con `mensaje` y `snapshot`.

        Raises:
            ValidationError: secta/traje desconocidos, de otra secta
                o bloqueado por victorias.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            if secta != partida.secta:
                raise ValidationError(
                    "Tu armario solo tiene trajes de tu secta",
                    code="secta_invalida",
                )
            objetivo: TrajeData | None = traje(secta, indice)
            if objetivo is None:
                raise ValidationError(
                    f"Traje desconocido: '{secta}[{indice}]'",
                    code="traje_desconocido",
                )
            if not rules.puede_vestir_traje(secta, indice, partida.victorias):
                raise ValidationError(
                    f"Se desbloquea con {objetivo.umbral} victorias "
                    f"({len(partida.victorias)}/{objetivo.umbral})",
                    code="traje_bloqueado",
                )
            rules.vestir_traje(
                partida.atuendo, partida.victorias, secta, indice
            )
            return f"Vestiste: {objetivo.nombre}"

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}
