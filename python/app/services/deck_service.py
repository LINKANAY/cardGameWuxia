"""Casos de uso de mazos — crear, editar, activar y desequipar.

Puerto del tab `dk` del monolito (`dkUI`/`dNew`/`dAdd`/`dRm`/`dRen`/
`dClr`/`dFill`/`dUse`/`dDup`/`dDel`/`dUneq` en
`js/04-mazos-formaciones.js` y `js/12-v47-init.js`). Toda mutación
pasa por `SessionStore.mutate` para que el auto-guardado sea infalible
(decisión de la Fase 0).

El JS no da feedback de error (los botones vienen deshabilitados y
algunas acciones son no-ops silenciosas); aquí cada precondición
violada lanza `ValidationError` con un código propio para que la UI
pueda explicar el fallo.
"""

from __future__ import annotations

import time

from app.core.errors import NotFoundError, ValidationError
from app.engine import rules
from app.engine.rng import GeneradorAleatorio
from app.engine.state import Partida
from app.state.session_store import SessionStore


class DeckService:
    """Orquesta las acciones de mazos sobre la partida de un slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    def _asegurar_partida(self, slot: str) -> None:
        """404 si el slot no existe ni en memoria ni en disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    @staticmethod
    def _aleatorio():
        """Callback float aleatorio con semilla de tiempo (paridad JS).

        El monolito usa `Math.random()` para el barajado del mazo
        automático; aquí el RNG mulberry32 con semilla de nanosegundos
        cumple el mismo contrato.
        """
        return GeneradorAleatorio(f"dk-{time.time_ns()}").random

    @staticmethod
    def _mazo(partida: Partida, indice: int) -> dict:
        """El mazo en `indice` o error si no existe (índice del JS)."""
        if indice < 0 or indice >= len(partida.mazos):
            raise ValidationError(
                f"No hay ningún mazo en la posición {indice}",
                code="indice_invalido",
            )
        return partida.mazos[indice]

    @staticmethod
    def _carta(id_carta: str) -> None:
        if id_carta not in rules.CARTAS:
            raise ValidationError(
                f"Carta desconocida: '{id_carta}'", code="carta_desconocida"
            )

    def crear(self, slot: str, desde_automatico: bool) -> dict:
        """Crea un mazo (`dNew(a)` del JS).

        Args:
            slot: slot de la partida.
            desde_automatico: copiar el mazo automático o empezar vacío.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            try:
                rules.crear_mazo(
                    partida.mazos,
                    desde_automatico=desde_automatico,
                    secta=partida.secta,
                    coleccion=partida.coleccion,
                    aleatorio=self._aleatorio(),
                )
            except ValueError as error:
                raise ValidationError(
                    str(error), code="maximo_mazos"
                ) from error
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def usar(self, slot: str, indice: int) -> dict:
        """Marca un mazo como activo, o el automático (`dUse(i)`).

        Paridad: el JS activa el mazo incluso si aún no es válido; la
        diferencia está en el mensaje (y en que el combate usará el
        automático hasta que se complete).

        Args:
            slot: slot de la partida.
            indice: índice del mazo o -1 para el automático.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            if indice == -1:
                partida.mazo_activo = -1
                return "Usarás el mazo automático."
            mazo = self._mazo(partida, indice)
            partida.mazo_activo = indice
            if rules.mazo_valido(mazo, partida.secta, partida.coleccion):
                return f"Mazo en uso: {mazo['n']}."
            return (
                "Ese mazo aún no tiene 40 cartas válidas; mientras tanto "
                "se usará el automático."
            )

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def renombrar(self, slot: str, indice: int, nombre: str) -> dict:
        """Renombra un mazo (`dRen(v)` del JS).

        Args:
            slot: slot de la partida.
            indice: índice del mazo.
            nombre: nombre nuevo (se recorta a 22 caracteres).

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            mazo = self._mazo(partida, indice)
            if not rules.renombrar_mazo(mazo, nombre):
                raise ValidationError(
                    "El nombre del mazo no puede quedar vacío",
                    code="nombre_vacio",
                )
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def anadir(self, slot: str, indice: int, id_carta: str) -> dict:
        """Añade 1 copia de una carta a un mazo (`dAdd(id)`).

        Args:
            slot: slot de la partida.
            indice: índice del mazo.
            id_carta: id de la carta.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)
        self._carta(id_carta)

        def mutador(partida: Partida) -> str:
            mazo = self._mazo(partida, indice)
            if rules.tamano_mazo(mazo) >= rules.TAMANO_MAZO:
                raise ValidationError(
                    "El mazo ya tiene 40 cartas", code="mazo_lleno"
                )
            if not rules.anadir_carta_a_mazo(
                mazo, id_carta, partida.secta, partida.coleccion
            ):
                raise ValidationError(
                    "No puedes llevar más copias de esa carta",
                    code="copias_maximas",
                )
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def quitar(self, slot: str, indice: int, id_carta: str) -> dict:
        """Quita 1 copia de una carta de un mazo (`dRm(id)`).

        Args:
            slot: slot de la partida.
            indice: índice del mazo.
            id_carta: id de la carta.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)
        self._carta(id_carta)

        def mutador(partida: Partida) -> str:
            mazo = self._mazo(partida, indice)
            if not rules.quitar_carta_de_mazo(mazo, id_carta):
                raise ValidationError(
                    "Esa carta no está en el mazo", code="carta_no_en_mazo"
                )
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def vaciar(self, slot: str, indice: int) -> dict:
        """Vacía un mazo (`dClr` del JS).

        Args:
            slot: slot de la partida.
            indice: índice del mazo.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            rules.vaciar_mazo(self._mazo(partida, indice))
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def autocompletar(self, slot: str, indice: int) -> dict:
        """Rellena un mazo con las mejores cartas poseídas (`dFill`).

        Args:
            slot: slot de la partida.
            indice: índice del mazo.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            rules.autocompletar_mazo(
                self._mazo(partida, indice),
                partida.secta,
                partida.coleccion,
            )
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def duplicar(self, slot: str, indice: int) -> dict:
        """Duplica un mazo (`dDup(i)` del JS).

        Args:
            slot: slot de la partida.
            indice: índice del mazo a copiar.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            self._mazo(partida, indice)  # valida el índice antes
            try:
                rules.duplicar_mazo(partida.mazos, indice)
            except ValueError as error:
                raise ValidationError(
                    str(error), code="maximo_mazos"
                ) from error
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def eliminar(self, slot: str, indice: int) -> dict:
        """Elimina un mazo y reajusta el activo (`dDel(i)` del JS).

        Args:
            slot: slot de la partida.
            indice: índice del mazo.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            self._mazo(partida, indice)  # valida el índice antes
            partida.mazo_activo = rules.eliminar_mazo(
                partida.mazos, indice, partida.mazo_activo
            )
            return ""

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def desequipar(self, slot: str, id_carta: str) -> dict:
        """Quita 1 copia del mazo en uso (`dUneq(id)` del JS).

        Args:
            slot: slot de la partida.
            id_carta: id de la carta.

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)
        self._carta(id_carta)

        def mutador(partida: Partida) -> str:
            if not rules.desequipar_del_activo(
                partida.mazos, partida.mazo_activo, id_carta
            ):
                raise ValidationError(
                    "Esa carta no está en tu mazo en uso",
                    code="carta_no_en_mazo",
                )
            mazo = partida.mazos[partida.mazo_activo]
            nombre = rules.CARTAS[id_carta].nombre
            if rules.mazo_valido(mazo, partida.secta, partida.coleccion):
                return f"Carta desequipada: {nombre}."
            return (
                f"Carta desequipada: {nombre}. El mazo quedó incompleto: "
                "se usará el automático hasta completarlo."
            )

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}
