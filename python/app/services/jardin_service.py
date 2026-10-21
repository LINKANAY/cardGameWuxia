"""Casos de uso del Jardín Medicinal — sembrar, acelerar, cosechar.

Módulo nuevo (no existe en el monolito). Toda mutación pasa por
`SessionStore.mutate` para que el auto-guardado sea infalible
(decisión de la Fase 0). El núcleo matemático (duraciones, piedras,
botines) es puro y vive en `app.engine.jardin`; las constantes en
`app.data.jardin`.

El reloj de las plantas es el del **servidor** (`_ahora`, epoch ms):
las casillas guardan el momento de siembra y el progreso se calcula al
leer, así que un cliente con el reloj atrasado no gana ni pierde
tiempo. En los tests se congela con `monkeypatch` igual que `_aleatorio`.

Diferencias deliberadas frente a lo que haría el JS (que calla ante un
error de UI): cada violación lanza `ValidationError` con código propio
(`casilla_ocupada`, `planta_bloqueada`, `piedras_invalidas`…).
"""

from __future__ import annotations

import time
from collections.abc import Callable

from app.core.errors import NotFoundError, ValidationError
from app.data.hierbas import HIERBA
from app.data.jardin import (
    FORMACION,
    MEJORAS,
)
from app.data.tipos import Material
from app.engine import jardin as nucleo
from app.engine.rng import GeneradorAleatorio
from app.engine.rules import pagar, puede_pagar
from app.engine.state import Partida
from app.state.session_store import SessionStore

#: Callback aleatorio inyectable (contrato de `Math.random`).
Rng = Callable[[], float]


class JardinService:
    """Orquesta el Jardín Medicinal sobre la partida de un slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    def _asegurar_partida(self, slot: str) -> None:
        """404 si el slot no existe ni en memoria ni en disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    @staticmethod
    def _aleatorio() -> Rng:
        """Callback float aleatorio con semilla de tiempo (mulberry32)."""
        return GeneradorAleatorio(f"jardin-{time.time_ns()}").random

    @staticmethod
    def _ahora() -> int:
        """epoch ms del servidor (reloj de crecimiento de las plantas)."""
        return int(time.time() * 1000)

    def _reloj(self, ahora: int | None) -> int:
        return self._ahora() if ahora is None else int(ahora)

    @staticmethod
    def _respuesta(
        partida: Partida, reloj: int, resultado: dict | None = None
    ) -> dict:
        """Estado del jardín + snapshot `xcg3` actualizado.

        El `snapshot` va en toda mutación (patrón de los demás
        servicios) para que la UI refresque materiales/piedras sin una
        segunda llamada.
        """
        datos = {
            **JardinService._estado_partida(partida, reloj),
            "snapshot": partida.a_dict(),
        }
        if resultado is not None:
            datos["resultado"] = resultado
        return datos

    @staticmethod
    def _estado_partida(partida: Partida, ahora_ms: int) -> dict:
        """Jardín + inventarios + mejoras, con tiempos ya calculados.

        Cada casilla sembrada sale enriquecida con `restante_ms`,
        `progreso`, `listo`, `coste_piedras` y `duracion_ms` (todo con
        la formación equipada aplicada), para que la UI no tenga que
        reproducir fórmulas.
        """
        jardin = partida.jardin
        formacion = jardin.get("formacion")
        casillas = []
        for casilla in jardin["casillas"]:
            if not casilla:
                casillas.append(None)
                continue
            casillas.append(
                {
                    **casilla,
                    "duracion_ms": nucleo.duracion_efectiva(
                        casilla["planta"], formacion
                    ),
                    "restante_ms": nucleo.restante_ms(
                        casilla, ahora_ms, formacion
                    ),
                    "progreso": nucleo.progreso(
                        casilla, ahora_ms, formacion
                    ),
                    "listo": nucleo.esta_listo(
                        casilla, ahora_ms, formacion
                    ),
                    "coste_piedras": nucleo.coste_max_piedras(
                        casilla, ahora_ms, formacion
                    ),
                }
            )
        return {
            "nivel": int(jardin.get("nivel", 0)),
            "casillas": casillas,
            "formacion": formacion,
            "semillas": dict(partida.semillas),
            "formaciones": dict(partida.formaciones_crecimiento),
            "reino": partida.nivel_reino,
            "materiales": dict(partida.materiales),
            "piedras": partida.piedras_espirituales,
            "siguiente_mejora": nucleo.siguiente_mejora(
                int(jardin.get("nivel", 0))
            ),
            "ahora": ahora_ms,
        }

    @staticmethod
    def _casilla_de(partida: Partida, indice: int) -> dict | None:
        """Casilla por índice con validación de rango (None si vacía)."""
        casillas = partida.jardin["casillas"]
        if not isinstance(indice, int) or isinstance(indice, bool):
            raise ValidationError(
                "Índice de casilla inválido", code="casilla_invalida"
            )
        if indice < 0 or indice >= len(casillas):
            raise ValidationError(
                "Esa casilla no existe en tu jardín",
                code="casilla_invalida",
            )
        return casillas[indice]

    def estado(self, slot: str, ahora: int | None = None) -> dict:
        """Estado completo del jardín para la UI.

        Args:
            slot: partida a leer.
            ahora: epoch ms opcional (para tests; por defecto el del
                servidor).

        Returns:
            `{nivel, casillas, formacion, semillas, formaciones, reino,
            materiales, piedras, siguiente_mejora, ahora}`.

        Raises:
            NotFoundError: la partida del slot no existe.
        """
        self._asegurar_partida(slot)
        reloj = self._reloj(ahora)
        return self._estado_partida(
            self._store.get_or_create(slot), reloj
        )

    def sembrar(
        self, slot: str, indice: int, planta: str, ahora: int | None = None
    ) -> dict:
        """Siembra una semilla en una casilla vacía.

        Args:
            slot: partida a mutar (auto-guardado incluido).
            indice: casilla destino (0 hasta `len(casillas) - 1`).
            planta: id de hierba sembrable.
            ahora: epoch ms opcional del momento de siembra.

        Returns:
            Estado del jardín con la casilla ocupada.

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: `casilla_invalida` (fuera de rango),
                `casilla_ocupada`, `planta_desconocida`,
                `planta_bloqueada` (reino insuficiente) o
                `semillas_insuficientes`.
        """
        self._asegurar_partida(slot)
        reloj = self._reloj(ahora)

        def mutador(partida: Partida) -> dict:
            casilla = self._casilla_de(partida, indice)
            if casilla is not None:
                raise ValidationError(
                    "Esa casilla ya está sembrada", code="casilla_ocupada"
                )
            hierba = HIERBA.get(planta)
            if hierba is None:
                raise ValidationError(
                    f"Semilla desconocida: '{planta}'",
                    code="planta_desconocida",
                )
            if not nucleo.desbloqueada(hierba.rareza, partida.nivel_reino):
                raise ValidationError(
                    f"Tu reino aún no puede sembrar {hierba.nombre}",
                    code="planta_bloqueada",
                )
            stock = partida.semillas.get(planta, 0)
            if stock <= 0:
                raise ValidationError(
                    f"No tienes semillas de {hierba.nombre}",
                    code="semillas_insuficientes",
                )
            restantes = stock - 1
            if restantes <= 0:
                partida.semillas.pop(planta, None)
            else:
                partida.semillas[planta] = restantes
            partida.jardin["casillas"][indice] = {
                "planta": planta,
                "siembra": reloj,
                "reducido": 0,
            }
            return self._respuesta(partida, reloj)

        return self._store.mutate(slot, mutador)

    def acelerar(
        self,
        slot: str,
        indice: int,
        piedras: int,
        ahora: int | None = None,
    ) -> dict:
        """Gasta piedras espirituales para adelantar una planta.

        Cada piedra quita 5 % del tiempo restante (mismo umbral de 1 s
        que `nucleo.aplicar_piedras`); se exige gastar **exactamente**
        lo necesario o menos, para que ninguna piedra se pierda.

        Args:
            slot: partida a mutar (auto-guardado incluido).
            indice: casilla sembrada.
            piedras: nº de piedras a gastar (≥ 1 y ≤ coste de esa
                casilla en este instante).
            ahora: epoch ms opcional.

        Returns:
            Estado del jardín + `resultado` (`indice`, `reducido`,
            `restante_ms`, `gastadas`).

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: `casilla_invalida`, `casilla_vacia`,
                `planta_lista`, `piedras_invalidas` o
                `piedras_insuficientes` (stn).
        """
        self._asegurar_partida(slot)
        reloj = self._reloj(ahora)

        def mutador(partida: Partida) -> dict:
            casilla = self._casilla_de(partida, indice)
            if not casilla:
                raise ValidationError(
                    "Esa casilla está vacía", code="casilla_vacia"
                )
            if not isinstance(piedras, int) or isinstance(piedras, bool):
                raise ValidationError(
                    "Cantidad de piedras inválida",
                    code="piedras_invalidas",
                )
            formacion = partida.jardin.get("formacion")
            maximo = nucleo.coste_max_piedras(casilla, reloj, formacion)
            if maximo <= 0:
                raise ValidationError(
                    "Esa planta ya está lista para cosechar",
                    code="planta_lista",
                )
            if piedras < 1 or piedras > maximo:
                raise ValidationError(
                    f"Con {maximo} piedra(s) basta para dejarla lista",
                    code="piedras_invalidas",
                )
            if partida.piedras_espirituales < piedras:
                raise ValidationError(
                    "Piedras espirituales insuficientes",
                    code="piedras_insuficientes",
                )
            partida.piedras_espirituales -= piedras
            resultado = nucleo.aplicar_piedras(
                casilla, piedras, reloj, formacion
            )
            casilla["reducido"] = resultado["reducido"]
            return self._respuesta(
                partida, reloj, {"indice": indice, **resultado}
            )

        return self._store.mutate(slot, mutador)

    def cosechar(
        self, slot: str, indice: int, ahora: int | None = None
    ) -> dict:
        """Cosecha una planta lista: hierbas al Horno y casilla libre.

        Args:
            slot: partida a mutar (auto-guardado incluido).
            indice: casilla sembrada y ya cumplida (≤ 1 s de margen).
            ahora: epoch ms opcional.

        Returns:
            Estado del jardín + `resultado` (`indice`, `planta`,
            `hierbas` cosechadas).

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: `casilla_invalida`, `casilla_vacia` o
                `planta_pendiente` (aún crece).
        """
        self._asegurar_partida(slot)
        reloj = self._reloj(ahora)

        def mutador(partida: Partida) -> dict:
            casilla = self._casilla_de(partida, indice)
            if not casilla:
                raise ValidationError(
                    "Esa casilla está vacía", code="casilla_vacia"
                )
            if not nucleo.esta_listo(
                casilla, reloj, partida.jardin.get("formacion")
            ):
                raise ValidationError(
                    "La planta aún está creciendo",
                    code="planta_pendiente",
                )
            planta = casilla["planta"]
            cantidad = nucleo.rendimiento(planta)
            inventario = partida.horno["hierbas"]
            inventario[planta] = inventario.get(planta, 0) + cantidad
            partida.jardin["casillas"][indice] = None
            return self._respuesta(
                partida,
                reloj,
                {
                    "indice": indice,
                    "planta": planta,
                    "hierbas": cantidad,
                },
            )

        return self._store.mutate(slot, mutador)

    def mejorar(self, slot: str, ahora: int | None = None) -> dict:
        """Amplía la cuadrícula al siguiente nivel (materiales + reino).

        Args:
            slot: partida a mutar (auto-guardado incluido).
            ahora: epoch ms opcional.

        Returns:
            Estado del jardín + `resultado` (`nivel`, `casillas`,
            `coste` pagado).

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: `mejora_no_disponible` (al tope),
                `reino_insuficiente` o `materiales_insuficientes`.
        """
        self._asegurar_partida(slot)
        reloj = self._reloj(ahora)

        def mutador(partida: Partida) -> dict:
            mejora = nucleo.siguiente_mejora(
                int(partida.jardin.get("nivel", 0))
            )
            if mejora is None:
                raise ValidationError(
                    "La cuadrícula ya está al máximo",
                    code="mejora_no_disponible",
                )
            if partida.nivel_reino < mejora["reino_min"]:
                raise ValidationError(
                    f"Reino {mejora['reino_min']} requerido "
                    f"(llevas {partida.nivel_reino})",
                    code="reino_insuficiente",
                )
            coste = {
                Material(clave): cantidad
                for clave, cantidad in mejora["coste"].items()
            }
            if not puede_pagar(coste, partida.materiales):
                raise ValidationError(
                    "Materiales insuficientes para la mejora",
                    code="materiales_insuficientes",
                )
            pagar(coste, partida.materiales)
            partida.jardin["nivel"] = mejora["nivel"]
            casillas = partida.jardin["casillas"]
            objetivo = MEJORAS[mejora["nivel"]].casillas
            if len(casillas) < objetivo:
                casillas.extend([None] * (objetivo - len(casillas)))
            return self._respuesta(
                partida,
                reloj,
                {
                    "nivel": mejora["nivel"],
                    "casillas": objetivo,
                    "coste": dict(mejora["coste"]),
                },
            )

        return self._store.mutate(slot, mutador)

    def equipar_formacion(
        self, slot: str, identificador: str | None, ahora: int | None = None
    ) -> dict:
        """Equipa (o quita) la formación de crecimiento del jardín.

        Args:
            slot: partida a mutar (auto-guardado incluido).
            identificador: id `fc*` a equipar; None o cadena vacía →
                desequipar (el inventario nunca se gasta aquí).
            ahora: epoch ms opcional.

        Returns:
            Estado del jardín (con la formación nueva aplicada ya a los
            `restante_ms` de las plantas en curso).

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: `formacion_desconocida` o
                `formacion_insuficiente` (no posees copias).
        """
        self._asegurar_partida(slot)
        reloj = self._reloj(ahora)

        def mutador(partida: Partida) -> dict:
            if not identificador:
                partida.jardin["formacion"] = None
                return self._respuesta(partida, reloj)
            if identificador not in FORMACION:
                raise ValidationError(
                    f"Formación desconocida: '{identificador}'",
                    code="formacion_desconocida",
                )
            if partida.formaciones_crecimiento.get(identificador, 0) < 1:
                raise ValidationError(
                    f"No posees {FORMACION[identificador].nombre}",
                    code="formacion_insuficiente",
                )
            partida.jardin["formacion"] = identificador
            return self._respuesta(partida, reloj)

        return self._store.mutate(slot, mutador)

    # --- entregas sin endpoint propio (las engancha el combate) -----------

    def botin_boticario(
        self, slot: str, dificultad: int, rng: Rng | None = None
    ) -> dict:
        """Entrega el botín de un boticario vencido (semillas, formación,
        materiales).

        Método de servicio **sin endpoint**: lo llama el hook de
        emboscadas de `CombatService` (Etapas posteriores), del mismo
        modo en que el botín de hierbas se engancha a `reclamar`.

        Args:
            slot: partida a mutar (auto-guardado incluido).
            dificultad: 0–5 del boticario (`ch.d`).
            rng: callback float opcional (para tests).

        Returns:
            Estado del jardín + `resultado` (el dict completo de
            `nucleo.botin_boticario`).

        Raises:
            NotFoundError: la partida no existe.
        """
        self._asegurar_partida(slot)
        aleatorio = rng or self._aleatorio()
        reloj = self._reloj(None)
        conseguido = nucleo.botin_boticario(dificultad, aleatorio)

        def mutador(partida: Partida) -> dict:
            for identificador, cantidad in conseguido["semillas"].items():
                partida.semillas[identificador] = (
                    partida.semillas.get(identificador, 0) + cantidad
                )
            formacion = conseguido.get("formacion")
            if formacion:
                partida.formaciones_crecimiento[formacion] = (
                    partida.formaciones_crecimiento.get(formacion, 0) + 1
                )
            for clave, cantidad in conseguido["materiales"].items():
                partida.materiales[clave] = (
                    partida.materiales.get(clave, 0) + cantidad
                )
            return self._respuesta(partida, reloj, conseguido)

        return self._store.mutate(slot, mutador)

    def regalo_ascenso(
        self, slot: str, rng: Rng | None = None
    ) -> dict:
        """Entrega el regalo al subir de reino (semilla + formación).

        Método de servicio **sin endpoint**: lo llama el hook de
        ascensión dentro de la resolución de victoria. Usa el reino
        **ya alcanzado** (`partida.nivel_reino` al entrar).

        Args:
            slot: partida a mutar (auto-guardado incluido).
            rng: callback float opcional (para tests).

        Returns:
            Estado del jardín + `resultado` (dict de
            `nucleo.regalo_ascenso`; `semilla` puede ser None si el
            reino no desbloquea especie nueva).

        Raises:
            NotFoundError: la partida no existe.
        """
        self._asegurar_partida(slot)
        aleatorio = rng or self._aleatorio()
        reloj = self._reloj(None)

        def mutador(partida: Partida) -> dict:
            regalo = nucleo.regalo_ascenso(partida.nivel_reino, aleatorio)
            semilla = regalo.get("semilla")
            if semilla:
                partida.semillas[semilla] = (
                    partida.semillas.get(semilla, 0) + 1
                )
            formacion = regalo.get("formacion")
            if formacion:
                partida.formaciones_crecimiento[formacion] = (
                    partida.formaciones_crecimiento.get(formacion, 0) + 1
                )
            return self._respuesta(partida, reloj, regalo)

        return self._store.mutate(slot, mutador)
