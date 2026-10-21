"""Generador de números aleatorios con semilla — paridad bit a bit con el JS.

Puerto del módulo RNG del monolito (`js/00-rng.js`). La paridad es exacta:
misma semilla ⇒ misma secuencia de floats y mismos enteros derivados.

Diferencias respecto al original (además del lenguaje):
- La semilla se guarda como `str` (el JS usa `String(s)`), y el hash opera
  sobre unidades de código UTF-16, igual que `charCodeAt` del navegador.
- No hay semilla automática por URL/localStorage: el llamador decide la
  semilla. En el backend se fija en la sesión de partida (ver
  `app.engine.state.Partida`).

Uso típico::

    rng = GeneradorAleatorio("test-123")
    flujo = rng.random()      # float en [0, 1), igual que RNG.random()
    dado = rng.entero(6)      # 0..5, igual que RNG.int(6)
    carta = rng.elegir(["a", "b", "c"])
    baraja = rng.barajar([1, 2, 3])  # lista nueva, original intacta

Referencia JS: `js/00-rng.js` (hash, mulberry32, pick, shuffle, int).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import TypeVar

Elemento = TypeVar("Elemento")

# Constantes internas del mulberry32/hash del JS (parte del algoritmo: no tocar).
_PASO_SEMILLA = 0x6D2B79F5  # suma de estado por paso (mulberry32)
_SEMILLA_HASH = 1779033703  # valor inicial del hash (hash())
_FACTOR_HASH = 3432918353  # multiplicador del hash (Math.imul)
_MODULO_2_32 = 4294967296  # 2**32, divisor final de mulberry32


def _int32(valor: int) -> int:
    """Entero con signo de 32 bits.

    Equivalente a `valor | 0` en JavaScript (ToInt32). El mulberry32
    alterna sumas con desbordamiento de 32 bits y desplazamientos lógicos,
    por lo que cada operación debe pasar por aquí.
    """
    valor &= 0xFFFFFFFF
    return valor - 0x100000000 if valor >= 0x80000000 else valor


def _uint32(valor: int) -> int:
    """Entero sin signo de 32 bits (`valor >>> 0` en JS)."""
    return valor & 0xFFFFFFFF


def _imul(multiplicando: int, multiplicador: int) -> int:
    """Multiplicación entera de 32 bits con signo (`Math.imul` en JS).

    Devuelve la parte baja del producto interpretada como int32.
    """
    return _int32(multiplicando * multiplicador)


def _unidades_utf16(texto: str) -> list[int]:
    """Unidades de código UTF-16, idénticas a `charCodeAt(i)` en JS.

    Para caracteres fuera del BMP (emoji) el navegador devuelve los dos
    surrogados; aquí se reproduce ese comportamiento.
    """
    codificado = texto.encode("utf-16-le")
    return [
        codificado[indice_par] | (codificado[indice_par + 1] << 8)
        for indice_par in range(0, len(codificado), 2)
    ]


def hash_texto(texto: str) -> int:
    """Hash determinista de 32 bits sin signo de una cadena.

    Puerto exacto de `hash(str)` en `js/00-rng.js`::

        let h = 1779033703 ^ str.length;
        for (let i = 0; i < str.length; i++) {
           h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
           h = (h << 13) | (h >>> 19);
        }
        return h >>> 0;

    Devuelve un entero en ``[0, 2**32)``. No usar para seguridad/cryptografía.
    """
    unidades = _unidades_utf16(texto)
    acumulado = _int32(_SEMILLA_HASH ^ len(unidades))
    for unidad in unidades:
        acumulado = _imul(acumulado ^ unidad, _FACTOR_HASH)
        # `<< 13` es shift aritmético de 32 bits; `>>> 19` es lógico.
        acumulado = _int32(
            _int32(acumulado << 13) | (_uint32(acumulado) >> 19)
        )
    return _uint32(acumulado)


def generador_mulberry32(semilla: int) -> Callable[[], float]:
    """Fábrica del PRNG mulberry32 a partir de una semilla uint32.

    Puerto exacto de `mulberry32(a)` en `js/00-rng.js`. Devuelve una
    función con estado encapsulado en el closure (cada llamada avanza):

    >>> siguiente = generador_mulberry32(hash_texto("x"))
    >>> 0.0 <= siguiente() < 1.0
    True
    """
    estado = _int32(semilla)

    def siguiente() -> float:
        nonlocal estado
        estado = _int32(estado + _PASO_SEMILLA)
        mezcla = _imul(estado ^ (_uint32(estado) >> 15), 1 | estado)
        mezcla = _int32(
            _int32(mezcla + _imul(mezcla ^ (_uint32(mezcla) >> 7), 61 | mezcla))
            ^ mezcla
        )
        return _uint32(mezcla ^ (_uint32(mezcla) >> 14)) / _MODULO_2_32

    return siguiente


class GeneradorAleatorio:
    """RNG con semilla reutilizable (sustituye al objeto global `RNG`).

    Un generador por partida/módulo. No es thread-safe a propósito: cada
    sesión de combate usa su propio generador.

    Atributos:
        semilla: cadena de semilla actual (como `RNG.seed` del JS).
    """

    def __init__(self, semilla: str) -> None:
        """Crea el generador y lo reinicia con `semilla`.

        Args:
            semilla: cualquier texto; se hashea con `hash_texto` para
                obtener el estado uint32 inicial (igual que `reseed(s)`).
        """
        self.semilla: str = ""
        self._siguiente: Callable[[], float] | None = None
        self.reiniciar(semilla)

    def reiniciar(self, semilla: str) -> None:
        """Fija la semilla y reinicia la secuencia (`RNG.reseed`)."""
        self.semilla = str(semilla)
        self._siguiente = generador_mulberry32(hash_texto(self.semilla))

    def random(self) -> float:
        """Siguiente float en ``[0, 1)`` (`RNG.random`)."""
        assert self._siguiente is not None, "generador no inicializado"
        return self._siguiente()

    def entero(self, limite: int) -> int:
        """Entero aleatorio en ``[0, limite)`` (`RNG.int`).

        Implementado como ``floor(random() * limite)``, **no** como
        módulo, para conservar la distribución del original.
        """
        if limite <= 0:
            raise ValueError(
                f"entero(limite) requiere limite > 0, recibido {limite}"
            )
        return math.floor(self.random() * limite)

    def elegir(self, lista: Sequence[Elemento]) -> Elemento:
        """Elemento aleatorio de una secuencia no vacía (`RNG.pick`)."""
        if not lista:
            raise ValueError("elegir() requiere una lista no vacía")
        return lista[self.entero(len(lista))]

    def barajar(self, lista: Sequence[Elemento]) -> list[Elemento]:
        """Copia barajada con Fisher-Yates (`RNG.shuffle`).

        No muta la entrada. La semántica es exactamente la del JS:
        recorre de ``len-1`` a ``1`` y para cada posición elige ``j``
        con ``floor(random() * (i + 1))``.
        """
        return self.barajar_con(lista, self.random)

    def barajar_con(
        self, lista: Sequence[Elemento], fuente: Callable[[], float]
    ) -> list[Elemento]:
        """`barajar` con un generador de floats alternativo.

        Reproduce `RNG.shuffle(a, r)` del JS, que acepta un callback `r`
        distinto de `api.random` (lo usa el motor cuando el RNG local
        difiere del global).
        """
        valores = list(lista)
        for posicion in range(len(valores) - 1, 0, -1):
            otra = math.floor(fuente() * (posicion + 1))
            valores[posicion], valores[otra] = (
                valores[otra],
                valores[posicion],
            )
        return valores

    def __repr__(self) -> str:  # pragma: no cover - sólo diagnóstico
        return f"GeneradorAleatorio(semilla={self.semilla!r})"
