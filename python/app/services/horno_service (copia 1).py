"""Casos de uso del Horno de Alquimia — inventario, refinado y botín.

Puerto del módulo `HornoAlq` de `js/11-horno.js` (secciones 4 · PUENTE,
5 · ESTADO y la parte accionable de 6 · INTERFAZ). Toda mutación pasa
por `SessionStore.mutate` para que el auto-guardado sea infalible
(decisión de la Fase 0).

El núcleo matemático es puro y vive en `app.engine.horno`; las
constantes en `app.data.hierbas`. Este servicio sólo orquesta: valida
precondiciones, consume/produce inventario y aplica vida.

Diferencias deliberadas respecto al monolito (el JS calla y no hace
nada ante un error de UI; aquí cada violación lanza `ValidationError`
con código propio):

- El estado del horno vive en `Partida.horno` (clave `xn`) en vez del
  `localStorage` aparte `xcg_horno`.
- El JS nunca deja refinar en combate porque la UI lo bloquea; este
  servicio sólo recibe el `SessionStore`, así que ese guardia queda en
  la capa de API/UI y no aquí.
- Si `vida_hroe` es None (vida "llena"/sin partida en curso) el fallo
  **no** toca la vida: el monolito restaría de la vida máxima y fijaría
  `hpNow`, pero aquí `None` significa "sin vida registrada" y se
  conserva ese significado (decisión documentada en el informe).
"""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence

from app.core.errors import NotFoundError, ValidationError
from app.data.hierbas import (
    CALIDADES,
    CFG,
    HIERBA,
    TIPOS,
    clave_pildora,
    nuevo_horno,
    parsear_pildora,
)
from app.data.narrativa import redondear_js
from app.engine import horno as nucleo
from app.engine.combat import vida_heroe_max
from app.engine.rng import GeneradorAleatorio
from app.engine.state import Partida
from app.state.session_store import SessionStore

#: Callback aleatorio inyectable (contrato de `Math.random`).
Rng = Callable[[], float]


class HornoService:
    """Orquesta el Horno de Alquimia sobre la partida de un slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    def _asegurar_partida(self, slot: str) -> None:
        """404 si el slot no existe ni en memoria ni en disco."""
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    @staticmethod
    def _aleatorio() -> Rng:
        """Callback float aleatorio con semilla de tiempo.

        El JS usa `Math.random()`; el RNG del motor con semilla de
        nanosegundos cumple el mismo contrato (mulberry32).
        """
        return GeneradorAleatorio(f"horno-{time.time_ns()}").random

    @staticmethod
    def _estado_partida(partida: Partida) -> dict:
        """Estado del horno + vida del héroe, listo para la API.

        `vida`/`vida_max` acompañan al inventario para que la UI del
        monolito (`pintarHp`) pueda pintar la barra sin otra llamada.
        """
        horno = partida.horno
        return {
            "hierbas": dict(horno.get("hierbas") or {}),
            "pildoras": dict(horno.get("pildoras") or {}),
            "refinadas": int(horno.get("refinadas") or 0),
            "fallos": int(horno.get("fallos") or 0),
            "vida": partida.vida_hroe,
            "vida_max": vida_heroe_max(partida.nivel_reino),
        }

    def estado(self, slot: str) -> dict:
        """Inventario del horno (`HornoAlq.estado()` del JS:578).

        Returns:
            Dict con `hierbas`, `pildoras`, `refinadas`, `fallos`,
            `vida` (None = sin daño registrado) y `vida_max`.

        Raises:
            NotFoundError: la partida del slot no existe.
        """
        self._asegurar_partida(slot)
        return self._estado_partida(self._store.get_or_create(slot))

    def resumen(self, slot: str, ids: Sequence[str]) -> dict:
        """Vista previa de una combinación (`resumenCombinacion`, 139).

        No valida ids desconocidos ni existencia de material: es una
        consulta pura (el JS los filtra en silencio igualmente).

        Args:
            slot: partida cuyo reino se suma al éxito.
            ids: ids de hierbas de la combinación (se pueden repetir).

        Returns:
            `{prob, puntos, tipo, armonia, discordia, desglose}`.

        Raises:
            NotFoundError: la partida del slot no existe.
        """
        self._asegurar_partida(slot)
        partida = self._store.get_or_create(slot)
        return nucleo.resumen_combinacion(ids, partida.nivel_reino)

    def _validar_seleccion(
        self, inventario: Mapping[str, int], ids: Sequence[str]
    ) -> Counter:
        """Precondiciones del refinado (`refinarUI`, 376-382)."""
        if len(ids) < CFG["MIN_HIERBAS"]:
            raise ValidationError(
                f"Coloca al menos {CFG['MIN_HIERBAS']} hierbas en el horno",
                code="hierbas_minimas",
            )
        if len(ids) > CFG["MAX_HIERBAS"]:
            raise ValidationError(
                f"El horno admite hasta {CFG['MAX_HIERBAS']} hierbas",
                code="hierbas_maximas",
            )
        necesarias: Counter = Counter()
        for identificador in ids:
            if identificador not in HIERBA:
                raise ValidationError(
                    f"Hierba desconocida: '{identificador}'",
                    code="hierba_desconocida",
                )
            necesarias[identificador] += 1
        for identificador, cantidad in necesarias.items():
            if inventario.get(identificador, 0) < cantidad:
                raise ValidationError(
                    f"No tienes suficientes '{identificador}' en el horno",
                    code="hierbas_insuficientes",
                )
        return necesarias

    @staticmethod
    def _consumir(
        inventario: dict[str, int], necesarias: Mapping[str, int]
    ) -> None:
        """Descuenta materiales del horno (siempre, éxito o no).

        El click del JS consume del inventario del horno siempre
        (`estado.hierbas[id]--`), no de `partida.materiales`.
        """
        for identificador, cantidad in necesarias.items():
            restantes = inventario.get(identificador, 0) - cantidad
            if restantes <= 0:
                inventario.pop(identificador, None)
            else:
                inventario[identificador] = restantes

    def refinar(
        self, slot: str, ids: Sequence[str], rng: Rng | None = None
    ) -> dict:
        """Refina una combinación (`refinarUI`, 376-412).

        Consume los materiales, resuelve una tirada y aplica el
        resultado: en éxito suma `refinadas` y produce la píldora
        `tipo.calidad`; en fallo suma `fallos`, produce `waste.fallida`
        y resta daño a `vida_hroe` con suelo 1 (nunca mata). Si
        `vida_hroe` es None la vida no se toca.

        Args:
            slot: partida a mutar (auto-guardado incluido).
            ids: 2–4 ids de hierbas del inventario del horno.
            rng: callback float opcional (para tests).

        Returns:
            Estado del horno + `resultado` (dict de `nucleo.refinar`
            más `clave` de la píldora y, en fallo, `danio_real`).

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: selección inválida o material insuficiente.
        """
        self._asegurar_partida(slot)
        aleatorio = rng or self._aleatorio()

        def mutador(partida: Partida) -> dict:
            horno = partida.horno
            inventario = horno["hierbas"]
            necesarias = self._validar_seleccion(inventario, ids)
            self._consumir(inventario, necesarias)

            resultado = nucleo.refinar(
                list(ids),
                aleatorio,
                {
                    "reino": partida.nivel_reino,
                    "maxHp": vida_heroe_max(partida.nivel_reino),
                },
            )
            if resultado["exito"]:
                horno["refinadas"] = horno.get("refinadas", 0) + 1
            else:
                horno["fallos"] = horno.get("fallos", 0) + 1
                resultado["danio_real"] = self._aplicar_danio(
                    partida, resultado["danio"]
                )
            clave = clave_pildora(
                resultado["pildora"]["tipo"], resultado["pildora"]["calidad"]
            )
            horno["pildoras"][clave] = horno["pildoras"].get(clave, 0) + 1
            resultado["clave"] = clave
            return {
                **self._estado_partida(partida),
                "resultado": resultado,
            }

        return self._store.mutate(slot, mutador)

    @staticmethod
    def _aplicar_danio(partida: Partida, danio: int) -> int:
        """Resta daño de fallo con suelo 1 (`juego.setHp`, 245-250).

        Returns:
            Daño realmente aplicado (0 si `vida_hroe` es None o el
            suelo absorbió todo).
        """
        if partida.vida_hroe is None:
            return 0
        suelo = 0 if CFG["PUEDE_MATAR"] else 1
        maximo = vida_heroe_max(partida.nivel_reino)
        nueva = max(
            suelo,
            min(maximo, redondear_js(partida.vida_hroe - danio)),
        )
        aplicado = partida.vida_hroe - nueva
        partida.vida_hroe = nueva
        return aplicado

    def usar_pildora(self, slot: str, clave: str) -> dict:
        """Consume una píldora del horno fuera de combate (`usarPildora`, 415).

        Cura `cura_pct(p)` % de la vida máxima (mín. 1 punto), sin
        pasarse de la vida máxima. La píldora no se gasta si la vida
        ya está completa (igual que el JS).

        Args:
            slot: partida a mutar (auto-guardado incluido).
            clave: clave de inventario (`'heal.media'`, `'waste.fallida'`…).

        Returns:
            Estado del horno + `resultado` (`clave`, `cura`, `vida_antes`,
            `vida_despues`, `cura_pct`).

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: sin stock (`pildora_inexistente`), clave
                corrupta (`clave_invalida`) o vida completa
                (`vida_completa`).
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> dict:
            horno = partida.horno
            stock = horno["pildoras"].get(clave, 0)
            if stock <= 0:
                raise ValidationError(
                    f"No tienes la píldora '{clave}'",
                    code="pildora_inexistente",
                )
            parseada = parsear_pildora(clave)
            if (
                parseada is None
                or parseada[0] not in TIPOS
                or parseada[1] not in CALIDADES
            ):
                raise ValidationError(
                    f"Clave de píldora inválida: '{clave}'",
                    code="clave_invalida",
                )
            maximo = vida_heroe_max(partida.nivel_reino)
            if partida.vida_hroe is None or partida.vida_hroe >= maximo:
                raise ValidationError(
                    "Tu vida ya está completa; la píldora no se gasta",
                    code="vida_completa",
                )
            pildora = {"tipo": parseada[0], "calidad": parseada[1]}
            antes = min(partida.vida_hroe, maximo)
            cura = max(
                1, redondear_js(maximo * nucleo.cura_pct(pildora) / 100)
            )
            despues = min(antes + cura, maximo)
            partida.vida_hroe = despues

            restantes = stock - 1
            if restantes <= 0:
                del horno["pildoras"][clave]
            else:
                horno["pildoras"][clave] = restantes

            return {
                **self._estado_partida(partida),
                "resultado": {
                    "clave": clave,
                    "cura": despues - antes,
                    "vida_antes": antes,
                    "vida_despues": despues,
                    "cura_pct": nucleo.cura_pct(pildora),
                },
            }

        return self._store.mutate(slot, mutador)

    def agregar_hierbas(
        self,
        slot: str,
        cantidad: int | Mapping[str, int],
        *,
        dificultad: int = 0,
        rng: Rng | None = None,
    ) -> dict:
        """Añade hierbas al inventario (`dar`/`botin`, 283-300).

        Args:
            slot: partida a mutar (auto-guardado incluido).
            cantidad: nº de hierbas aleatorias ponderadas por peso, o
                dict id → cantidad para añadir explícitas.
            dificultad: 0–5; sólo con int, sube el peso de las raras.
            rng: callback float opcional (para tests).

        Returns:
            `anadidas` (id → cantidad) + estado del horno.

        Raises:
            NotFoundError: la partida no existe.
            ValidationError: cantidad fuera de rango o hierba
                desconocida.
        """
        self._asegurar_partida(slot)
        aleatorio = rng or self._aleatorio()
        if isinstance(cantidad, Mapping):
            anadidas: dict[str, int] = {}
            for identificador, n in cantidad.items():
                if identificador not in HIERBA:
                    raise ValidationError(
                        f"Hierba desconocida: '{identificador}'",
                        code="hierba_desconocida",
                    )
                if int(n) < 1:
                    raise ValidationError(
                        "La cantidad debe ser al menos 1",
                        code="cantidad_invalida",
                    )
                anadidas[identificador] = int(n)
        else:
            if cantidad < 1 or cantidad > 50:
                raise ValidationError(
                    "La cantidad debe estar entre 1 y 50",
                    code="cantidad_invalida",
                )
            anadidas = nucleo.botin(cantidad, aleatorio, dificultad)

        def mutador(partida: Partida) -> dict:
            inventario = partida.horno["hierbas"]
            for identificador, n in anadidas.items():
                inventario[identificador] = (
                    inventario.get(identificador, 0) + n
                )
            return self._estado_partida(partida)

        estado = self._store.mutate(slot, mutador)
        return {"anadidas": anadidas, **estado}

    def botin_victoria(
        self,
        slot: str,
        dificultad: int,
        es_jefe: bool = False,
        rng: Rng | None = None,
    ) -> dict:
        """Botín de hierbas al ganar un combate (`botinCombate`, 302-307).

        Nº aleatorio en `BOTIN_VICTORIA` (1–2) + `BOTIN_BONUS_JEFE` si
        `dificultad >= 4` o `es_jefe`; las hierbas se sortean por peso
        (las raras pesan más a mayor dificultad).

        Args:
            slot: partida a mutar (auto-guardado incluido).
            dificultad: dificultad del enemigo vencido (`ch.d`).
            es_jefe: jefe reconocido por el llamador (p. ej. jefe de
                mazmorra); equivale al umbral `dif >= 4` del JS.
            rng: callback float opcional (para tests).

        Returns:
            `hierbas` (id → cantidad), `dificultad` y `mensaje`
            (texto del aviso del JS).

        Raises:
            NotFoundError: la partida no existe.
        """
        self._asegurar_partida(slot)
        aleatorio = rng or self._aleatorio()
        conseguido = nucleo.botin_combate(dificultad, aleatorio, es_jefe)

        def mutador(partida: Partida) -> None:
            inventario = partida.horno["hierbas"]
            for identificador, n in conseguido.items():
                inventario[identificador] = (
                    inventario.get(identificador, 0) + n
                )

        self._store.mutate(slot, mutador)
        texto = ", ".join(
            f"{HIERBA[identificador].nombre} ×{n}"
            for identificador, n in conseguido.items()
        )
        return {
            "hierbas": conseguido,
            "dificultad": dificultad,
            "mensaje": texto,
        }

    def reiniciar(self, slot: str) -> dict:
        """Reinicia el horno al inventario inicial (`reiniciar`, 308).

        Returns:
            Estado del horno restaurado.

        Raises:
            NotFoundError: la partida no existe.
        """
        self._asegurar_partida(slot)

        def mutador(partida: Partida) -> dict:
            partida.horno = nuevo_horno()
            return self._estado_partida(partida)

        return self._store.mutate(slot, mutador)
