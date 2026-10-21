"""Casos de uso del mercado — compra/venta de cartas, materiales y píldoras.

Puerto del tab `mkt` del monolito (`buy`/`buyM`/`sellM`/`buyC` en
`js/03-cartas-mercado.js` y el override v47 de `js/12-v47-init.js:145-157`).
Toda mutación pasa por `SessionStore.mutate` para que el auto-guardado
sea infalible (decisión de la Fase 0).

El JS cancela silenciosamente las acciones inválidas; aquí cada
precondición violada lanza `ValidationError` con un código propio para
que la UI pueda explicar el fallo.
"""

from __future__ import annotations

from app.core.errors import NotFoundError, ValidationError
from app.data.mercado import PUESTOS_MERCADO
from app.data.pildoras import NOMBRE_MATERIAL
from app.data.tipos import Material
from app.engine import rules
from app.engine.state import Partida
from app.state.session_store import SessionStore


class MarketService:
    """Orquesta las acciones del mercado sobre la partida de un slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    def _asegurar_partida(self, slot: str) -> None:
        """404 si el slot no existe ni en memoria ni en disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    def comprar_carta(self, slot: str, carta: str) -> dict:
        """Compra una carta del puesto (`buy(id)` + `vzTake` del v47).

        Args:
            slot: slot de la partida.
            carta: id de la carta del catálogo.

        Returns:
            Dict con `mensaje` y `snapshot`.

        Raises:
            ValidationError: carta desconocida, Celestial/relíquia,
                bloqueada para la secta del jugador, ya 3 copias,
                cartas del Abismo ya obtenidas o piedras insuficientes.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            if carta not in rules.CARTAS:
                raise ValidationError(
                    f"Carta desconocida: '{carta}'", code="carta_desconocida"
                )
            if not rules.puede_comprar_carta(
                carta, partida.secta_elegida_confirmada
            ):
                raise ValidationError(
                    "Carta no disponible en el mercado para tu secta",
                    code="no_disponible",
                )
            if not rules.carta_abismo_disponible(
                partida.coleccion, partida.misiones, carta
            ):
                raise ValidationError(
                    "Carta del Abismo ya obtenida esta partida",
                    code="abismo_agotado",
                )
            if partida.coleccion.get(carta, 0) >= rules.MAX_COPIAS:
                raise ValidationError(
                    "Ya tienes las 3 copias máximas",
                    code="coleccion_llena",
                )
            precio = rules.precio_compra(carta)
            if partida.piedras_espirituales < precio:
                raise ValidationError(
                    "Piedras espirituales insuficientes",
                    code="piedras_insuficientes",
                )
            partida.piedras_espirituales -= precio
            partida.misiones["bu"] = partida.misiones.get("bu", 0) + 1
            partida.misiones["ss"] = partida.misiones.get("ss", 0) + precio
            if (
                partida.secta_elegida_confirmada
                and rules.SECTA_DE_CARTA.get(carta)
                == partida.secta_elegida_confirmada
            ):
                partida.misiones["bsc"] = (
                    partida.misiones.get("bsc", 0) + 1
                )
            rules.agregar_carta_coleccion(
                partida.coleccion, partida.materiales, carta
            )
            rules.registrar_abismo(partida.misiones, carta)
            nombre = rules.CARTAS[carta].nombre
            return (
                f"Compraste «{nombre}» por {precio} piedras espirituales."
            )

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}

    def comprar_material(
        self, slot: str, puesto: str, confirmado: bool
    ) -> dict:
        """Compra el lote de material del puesto (`buyM(k)`).

        El monolito pide confirmación antes de ejecutar la compra
        (`cfOpen` en `js/12-v47-init.js:152`); aquí el flag
        `confirmado` reproduce ese paso (False devuelve los datos del
        lote sin comprar; True ejecuta `buyM`).

        Args:
            slot: slot de la partida.
            puesto: clave del puesto de mercado (`MK[k]`; la clave
                `'neu'` no tiene lote).
            confirmado: True = ejecutar la compra.

        Returns:
            Dict con `mensaje`, `confirmar` (bool) y, si falta
            confirmar, `lote` (nombre, material, cantidad, precio);
            siempre con `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> tuple[str, dict | None]:
            if puesto not in PUESTOS_MERCADO:
                raise ValidationError(
                    "Puesto de mercado desconocido",
                    code="puesto_invalido",
                )
            lote = PUESTOS_MERCADO[puesto].lote
            if lote is None:
                raise ValidationError(
                    "Ese puesto no vende materiales",
                    code="puesto_invalido",
                )
            if not confirmado:
                return (
                    f"Comprar {lote.nombre}: recibirás {lote.cantidad} "
                    f"{NOMBRE_MATERIAL[lote.material]} por {lote.costo} "
                    "piedras espirituales.",
                    {
                        "nombre": lote.nombre,
                        "material": lote.material,
                        "cantidad": lote.cantidad,
                        "costo": lote.costo,
                    },
                )
            if partida.piedras_espirituales < lote.costo:
                raise ValidationError(
                    "Piedras espirituales insuficientes",
                    code="piedras_insuficientes",
                )
            partida.piedras_espirituales -= lote.costo
            partida.misiones["bm"] = partida.misiones.get("bm", 0) + 1
            partida.misiones["ss"] = partida.misiones.get("ss", 0) + lote.costo
            partida.materiales[lote.material] = (
                partida.materiales.get(lote.material, 0) + lote.cantidad
            )
            mensaje = (
                f"Compraste {lote.cantidad} "
                f"{NOMBRE_MATERIAL[lote.material]} ({lote.nombre})."
            )
            return mensaje, None

        mensaje, lote = self._store.mutate(slot, mutador)
        resultado = {
            "mensaje": mensaje,
            "snapshot": self._store.snapshot(slot),
        }
        if lote is not None:
            resultado["confirmar"] = True
            resultado["lote"] = lote
        return resultado

    def vender_material(self, slot: str, material: str) -> dict:
        """Vende 1 unidad de material (`sellM(m)`).

        Referencia: `js/03-cartas-mercado.js:10`. El monolito vende
        una unidad por clic al precio fijo `SELL[m]`.

        Args:
            slot: slot de la partida.
            material: `'h'`, `'p'` o `'n'`.

        Returns:
            Dict con `mensaje`, `piedras` (ganadas) y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> tuple[str, int]:
            if material not in {m.value for m in Material}:
                raise ValidationError(
                    f"Material desconocido: '{material}'",
                    code="material_desconocido",
                )
            if not partida.materiales.get(material):
                raise ValidationError(
                    "No tienes ese material para vender",
                    code="material_insuficiente",
                )
            precio = rules.PRECIO_VENTA_MATERIAL[material]
            partida.materiales[material] -= 1
            partida.misiones["sv"] = partida.misiones.get("sv", 0) + 1
            partida.piedras_espirituales += precio
            nombre = NOMBRE_MATERIAL[Material(material)]
            mensaje = (
                f"Vendiste 1 de {nombre} por {precio} "
                "piedras espirituales."
            )
            return mensaje, precio

        mensaje, piedras = self._store.mutate(slot, mutador)
        return {
            "mensaje": mensaje,
            "piedras": piedras,
            "snapshot": self._store.snapshot(slot),
        }

    def comprar_pildora(self, slot: str, pildora: str) -> dict:
        """Compra una píldora/talismán del puesto General (`buyC(k)`).

        Referencia: `js/12-v47-init.js:146`. Precio por
        `mkcPrice(k)`; no exige receta aprendida (se vende en la
        vitrina).

        Args:
            slot: slot de la partida.
            pildora: id en `PILDORAS` (debe estar en `pildoras_en_venta`).

        Returns:
            Dict con `mensaje` y `snapshot`.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> str:
            if pildora not in rules.PILDORAS:
                raise ValidationError(
                    f"Píldora desconocida: '{pildora}'",
                    code="pildora_desconocida",
                )
            if pildora not in rules.pildoras_en_venta(partida.recetas):
                raise ValidationError(
                    "Esa píldora no está a la venta",
                    code="no_en_venta",
                )
            precio = rules.precio_pildora_mercado(pildora)
            if partida.piedras_espirituales < precio:
                raise ValidationError(
                    "Piedras espirituales insuficientes",
                    code="piedras_insuficientes",
                )
            partida.piedras_espirituales -= precio
            partida.pildoras[pildora] = partida.pildoras.get(pildora, 0) + 1
            partida.misiones["ss"] = partida.misiones.get("ss", 0) + precio
            nombre = rules.PILDORAS[pildora].nombre
            return (
                f"Compraste {nombre} por {precio} piedras espirituales."
            )

        mensaje = self._store.mutate(slot, mutador)
        return {"mensaje": mensaje, "snapshot": self._store.snapshot(slot)}
