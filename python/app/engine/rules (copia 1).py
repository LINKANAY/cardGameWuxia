"""Reglas puras del motor — sin estado global, sin I/O.

Funciones deterministas (o con RNG inyectado) que implementan las
reglas del monolito. Cada función cita la referencia JS. El resto de
reglas de combate llegan en la Fase 2 (`app.engine.combat`).

Convención: si una regla necesita azar, el manejador se pasa como
argumento (`rng`), nunca se importa un módulo global. Así los tests
pueden inyectar un RNG fijo y verificar la secuencia exacta.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from app.data.cartas import (
    CARTAS,
    CARTAS_NEUTRALES,
    PRECIO_RAREZA,
    RAREZAS,
    cartas_de_rareza,
    crear_carta,
    rareza_de,
)
from app.data.equipo import PIEZAS, PiezaData, pieza
from app.data.gacha import (
    CANTIDAD_POLVO,
    POOLS,
    PROBABILIDAD_CARTA,
    RAREZA_OBJETIVO,
    RAREZAS_GACHA,
    TICKETS,
)
from app.data.mercado import (
    PILDORAS_BASICAS_MERCADO,
    PRECIO_VENTA_MATERIAL,
    PUESTOS_MERCADO,
)
from app.data.narrativa import DIFICULTADES, redondear_js
from app.data.niveles import ENEMIGOS
from app.data.pildoras import COSTE_FORJA, NOMBRE_MATERIAL, PILDORAS
from app.data.sectas import SECTA_DE_CARTA, SECTAS
from app.data.tipos import Material, TipoCarta, TipoEfecto
from app.data.trajes import (
    traje,
)

# Re-exportados para que la capa de servicios no tenga que importar de data.
__all__ = [
    "CARTAS",
    "CARTAS_NEUTRALES",
    "MAX_MAZOS",
    "PILDORAS",
    "POOLS",
    "PRECIO_RAREZA",
    "PRECIO_VENTA_MATERIAL",
    "PUESTOS_MERCADO",
    "RAREZAS",
    "RAREZAS_GACHA",
    "SECTAS",
    "TAMANO_MAZO",
    "TICKETS",
    "RecompensaGacha",
    "ResultadoCarta",
    "agregar_carta_coleccion",
    "anadir_carta_a_mazo",
    "autocompletar_mazo",
    "candidatas_gacha",
    "carta_abismo_disponible",
    "cartas_de_rareza",
    "cartas_en_venta",
    "construir_mazo",
    "copias_usables",
    "coste_forja",
    "crear_carta",
    "crear_mazo",
    "descripcion_carta",
    "desequipar_del_activo",
    "desmantelar_coleccion",
    "duplicar_mazo",
    "elaborar_pildora",
    "eliminar_mazo",
    "es_carta_abismo",
    "estadisticas_carta",
    "forjar_carta",
    "forjar_pieza",
    "fusionar_coleccion",
    "gear_stat",
    "generar_rareza_recompensa",
    "generar_recompensa_gacha",
    "mazo_activo_plano",
    "mazo_valido",
    "obtencion_carta",
    "pagar",
    "pieza_desbloqueada",
    "pildoras_en_venta",
    "precio_compra",
    "precio_pildora_mercado",
    "puede_comprar_carta",
    "puede_elaborar",
    "puede_forjar",
    "puede_forjar_pieza",
    "puede_pagar",
    "puede_vestir_traje",
    "quitar_carta_de_mazo",
    "rareza_de",
    "registrar_abismo",
    "renombrar_mazo",
    "sortear_rareza_gacha",
    "subir_acumulacion",
    "tabla_acumulacion",
    "tamano_mazo",
    "texto_coste",
    "tipo_pildora_mercado",
    "vaciar_mazo",
    "vestir_traje",
]


def generar_rareza_recompensa(
    aleatorio: Callable[[], float], rareza_meritada: int
) -> list[str]:
    """Genera 3 ids de carta como recompensa de combate (`genRw` del JS).

    Semántica exacta del monolito:

    1. La primera carta sale con la rareza exacta que merece el enemigo.
    2. Las dos siguientes salen con ``max(0, m - floor(random()*3))``,
       es decir, rareza igual o menor (hasta 3 puntos por debajo).
    3. Se reintenta (máx. 60 intentos por carta) hasta encontrar una
       carta no repetida de esa rareza. Si una rareza no tiene cartas
       disponibles, se baja la rareza solicitada en el siguiente intento.

    Args:
        aleatorio: callback float en ``[0, 1)`` (se inyecta el RNG).
        rareza_meritada: rareza base 0–5 del enemigo vencido (`ch.rw`).

    Returns:
        Lista de 3 ids de carta (puede repetir ids si no hay más opciones;
        el JS no lo evita explícitamente, sólo filtra `o.includes`).
    """
    salida: list[str] = []
    intentos = 0
    while len(salida) < 3 and intentos < 60:
        intentos += 1
        if salida:
            rareza_objetivo = max(
                0, rareza_meritada - math.floor(aleatorio() * 3)
            )
        else:
            rareza_objetivo = rareza_meritada
        candidatos = [
            identificador
            for identificador in cartas_de_rareza(rareza_objetivo)
            if identificador not in salida
        ]
        if candidatos:
            indice_elegido = math.floor(aleatorio() * len(candidatos))
            salida.append(candidatos[indice_elegido])
    return salida


def puede_comprar_carta(
    identificador: str, secta_elegida: str | None
) -> bool:
    """`okBuy(id)` del JS: ¿se puede comprar esta carta en el mercado?

    Reglas:
    - Rareza < 5 (las Celestiales no se venden).
    - Si la carta pertenece a una secta (`SECTA_DE_CARTA`), su secta
      debe coincidir con `secta_elegida` (la del jugador, `schosen`).
    """
    carta = CARTAS[identificador]
    if rareza_de(carta) >= 5:
        return False
    secta_carta = SECTA_DE_CARTA.get(identificador)
    return not (secta_carta and secta_carta != secta_elegida)


def precio_compra(identificador: str) -> int:
    """Precio de compra en piedras espirituales (`PR(id)` del JS)."""
    return PRECIO_RAREZA[rareza_de(CARTAS[identificador])]


def puede_pagar(
    coste: dict[Material, int], materiales: dict[str, int]
) -> bool:
    """¿Hay materiales suficientes? (`canPay` del JS).

    Args:
        coste: dict Material → cantidad requerida.
        materiales: inventario actual, con claves `'h'/'n'/'p'`.
    """
    return all(
        materiales.get(material.value, 0) >= cantidad
        for material, cantidad in coste.items()
    )


def pagar(coste: dict[Material, int], materiales: dict[str, int]) -> None:
    """Descuenta materiales in situ (`pay` del JS; muta `materiales`).

    Lanza `ValueError` si no hay suficiente (el JS simplemente no hace
    nada; aquí preferimos fallar ruidosamente para atrapar bugs).
    """
    if not puede_pagar(coste, materiales):
        raise ValueError(f"materiales insuficientes para pagar {coste}")
    for material, cantidad in coste.items():
        materiales[material.value] = (
            materiales.get(material.value, 0) - cantidad
        )


def texto_coste(coste: dict[Material, int]) -> str:
    """Texto legible de un coste (`cs` del JS): "3 hierbas, 1 polvo de jade"."""
    return ", ".join(
        f"{cantidad} {NOMBRE_MATERIAL[material]}"
        for material, cantidad in coste.items()
    )


def coste_forja(rareza: int) -> dict[Material, int]:
    """Coste de forjar una carta de la rareza dada (`FC[r]` del JS)."""
    return COSTE_FORJA[rareza]


def puede_forjar(rareza: int, materiales: dict[str, int]) -> bool:
    """¿Se puede pagar la forja de una carta de esa rareza?"""
    return puede_pagar(COSTE_FORJA[rareza], materiales)


# --- Cartas del Abismo (v47: una sola vez por partida) ---------------------
#
# `js/12-v47-init.js:39-44`: las cartas con `vb`/`vs` (Agujero Negro)
# solo pueden obtenerse una vez por partida; las copias posteriores se
# convierten en polvo. El estado vive en `qs.vz` (mapa id → 1).


def es_carta_abismo(carta) -> bool:
    """¿Es una carta del Abismo? (`VREC(id)`: tiene `vb` o `vs`)."""
    return bool(carta.abismo_traer or carta.samsara)


def carta_abismo_disponible(
    coleccion: dict[str, int], misiones: dict, identificador: str
) -> bool:
    """¿Se puede seguir obteniendo esta carta del Abismo? (`vzOk`).

    Args:
        coleccion: inventario de cartas (`col`).
        misiones: contadores de misión (`qs`); el registro del Abismo
            vive en la subclave `vz`.
        identificador: id de la carta.
    """
    carta = CARTAS[identificador]
    if not es_carta_abismo(carta):
        return True
    registro = misiones.get("vz") or {}
    return not (registro.get(identificador) or coleccion.get(identificador, 0) > 0)


def registrar_abismo(misiones: dict, identificador: str) -> None:
    """Marca una carta del Abismo como obtenida (`vzTake`).

    Args:
        misiones: contadores de misión (`qs`; mutado con la subclave
            `vz`).
        identificador: id de la carta.
    """
    if not es_carta_abismo(CARTAS[identificador]):
        return
    registro = misiones.setdefault("vz", {})
    registro[identificador] = 1


# --- Alquimia (tab `alq` del monolito: brew/forge/fuse/dis/addCard) ------


@dataclass(frozen=True, slots=True)
class ResultadoCarta:
    """Carta obtenida por forja o fusión.

    Atributos:
        identificador: id de la carta elegida del catálogo.
        nombre: nombre visible con el sufijo de conversión si la
            colección ya tenía 3 copias (devuelto por `addCard`).
    """

    identificador: str
    nombre: str


def agregar_carta_coleccion(
    coleccion: dict[str, int],
    materiales: dict[str, int],
    identificador: str,
    misiones: dict | None = None,
) -> ResultadoCarta:
    """Añade una copia a la colección (`addCard` del JS, `js/01-datos.js:190`).

    Aplica también el wrapper v47 (`js/12-v47-init.js:44`): si la carta
    es del Abismo (`vb`/`vs`) y ya se obtuvo en la partida, la copia se
    convierte directamente en ``1 + rareza`` polvo de jade y se marca
    el registro `qs.vz`.

    Si ya se tienen 3 copias (caso normal), la copia extra se convierte
    en polvo de jade: ``1 + rareza`` unidades, y el nombre devuelto lo
    indica.

    Args:
        coleccion: inventario de cartas, id → nº de copias (mutado).
        materiales: inventario de materiales con claves `'h'/'n'/'p'`
            (mutado sólo en los casos de conversión a polvo).
        identificador: id de carta del catálogo.
        misiones: contadores `qs` (opcional; si se pasa, se registra el
            Abismo en la subclave `vz`).

    Returns:
        El id aportado y su nombre visible (con sufijo de conversión
        si corresponde).
    """
    carta = CARTAS[identificador]
    if misiones is not None and es_carta_abismo(carta):
        if not carta_abismo_disponible(coleccion, misiones, identificador):
            polvo = 1 + rareza_de(carta)
            materiales["p"] = materiales.get("p", 0) + polvo
            return ResultadoCarta(
                identificador,
                f"{carta.nombre} (carta del Abismo ya obtenida esta "
                "partida: se convierte en polvo de jade)",
            )
        registrar_abismo(misiones, identificador)
    if coleccion.get(identificador, 0) >= 3:
        polvo = 1 + rareza_de(carta)
        materiales["p"] = materiales.get("p", 0) + polvo
        return ResultadoCarta(
            identificador,
            f"{carta.nombre} (ya tenías 3 copias: se convierte en "
            "polvo de jade)",
        )
    coleccion[identificador] = coleccion.get(identificador, 0) + 1
    return ResultadoCarta(identificador, carta.nombre)


def puede_elaborar(
    identificador: str,
    recetas: dict[str, int],
    materiales: dict[str, int],
) -> bool:
    """¿Se puede elaborar esta píldora? (precondiciones de `brew`).

    Reglas del JS (`js/01-datos.js:191`): la receta debe estar
    aprendida (`rec[k]`) y haber materiales suficientes para su coste.
    """
    if not recetas.get(identificador):
        return False
    pildora = PILDORAS.get(identificador)
    if pildora is None:
        return False
    return puede_pagar(pildora.coste, materiales)


def elaborar_pildora(
    pildoras: dict[str, int],
    recetas: dict[str, int],
    materiales: dict[str, int],
    identificador: str,
) -> None:
    """Elabora una píldora (`brew` del JS; muta `pildoras` y `materiales`).

    Precondiciones: `puede_elaborar(...)`. El incremento del contador
    de misiones `qs.br` lo orquesta la capa de servicios.
    """
    if not puede_elaborar(identificador, recetas, materiales):
        raise ValueError(f"no se puede elaborar la píldora '{identificador}'")
    pildora = PILDORAS[identificador]
    pagar(pildora.coste, materiales)
    pildoras[identificador] = pildoras.get(identificador, 0) + 1


def forjar_carta(
    coleccion: dict[str, int],
    materiales: dict[str, int],
    rareza: int,
    aleatorio: Callable[[], float],
    misiones: dict | None = None,
) -> ResultadoCarta:
    """Forja una carta aleatoria de la rareza dada (`forge` del JS).

    Referencia: `js/01-datos.js:192`. Paga ``FC[rareza]`` y añade una
    carta al azar entre las de esa rareza (excluyendo reliquias, igual
    que `byR`). El azar se inyecta (`aleatorio` = `Math.random` en el JS).

    Args:
        coleccion: inventario de cartas (mutado).
        materiales: inventario de materiales (mutado).
        rareza: índice 0–5.
        aleatorio: callback float en ``[0, 1)``.
        misiones: contadores `qs` (opcional; paridad del wrapper del
            Abismo en `addCard`).

    Returns:
        La carta obtenida (id + nombre visible con sufijo si ya se
        tenían 3 copias).
    """
    pagar(COSTE_FORJA[rareza], materiales)
    candidatos = cartas_de_rareza(rareza)
    elegida = candidatos[math.floor(aleatorio() * len(candidatos))]
    return agregar_carta_coleccion(
        coleccion, materiales, elegida, misiones
    )


def fusionar_coleccion(
    coleccion: dict[str, int],
    materiales: dict[str, int],
    identificador: str,
    aleatorio: Callable[[], float],
    misiones: dict | None = None,
) -> ResultadoCarta:
    """Fusiona 3 copias en una carta de rareza superior (`fuse` del JS).

    Referencia: `js/01-datos.js:193`. Condiciones: al menos 3 copias y
    rareza < 5 (las Celestiales no se fusionan). Se consumen 3 copias y
    se añade una carta aleatoria de rareza ``rareza + 1``.

    Args:
        coleccion: inventario de cartas (mutado).
        materiales: inventario de materiales (mutado sólo si la carta
            resultante llena las 3 copias).
        identificador: id de la carta a fusionar.
        aleatorio: callback float en ``[0, 1)``.
        misiones: contadores `qs` (opcional; paridad del wrapper del
            Abismo en `addCard`).

    Returns:
        La carta obtenida (id + nombre visible).
    """
    carta = CARTAS[identificador]
    if coleccion.get(identificador, 0) < 3:
        raise ValueError(f"no hay 3 copias de '{identificador}' para fusionar")
    if rareza_de(carta) >= 5:
        raise ValueError(f"la carta '{identificador}' es Celestial")
    coleccion[identificador] -= 3
    if not coleccion[identificador]:
        del coleccion[identificador]
    nueva_rareza = rareza_de(carta) + 1
    candidatos = cartas_de_rareza(nueva_rareza)
    elegida = candidatos[math.floor(aleatorio() * len(candidatos))]
    return agregar_carta_coleccion(
        coleccion, materiales, elegida, misiones
    )


def desmantelar_coleccion(
    coleccion: dict[str, int],
    materiales: dict[str, int],
    identificador: str,
) -> int:
    """Desmantela una copia en polvo de jade (`dis` del JS).

    Referencia: `js/01-datos.js:194`. Consume 1 copia y devuelve
    ``1 + rareza`` de polvo de jade (ya sumado a `materiales['p']`).

    Args:
        coleccion: inventario de cartas (mutado).
        materiales: inventario de materiales (mutado).
        identificador: id de la carta a desmantelar.

    Returns:
        Cantidad de polvo de jade ganada.
    """
    carta = CARTAS[identificador]
    if not coleccion.get(identificador):
        raise ValueError(f"no hay copias de '{identificador}' para desmantelar")
    coleccion[identificador] -= 1
    if not coleccion[identificador]:
        del coleccion[identificador]
    polvo = 1 + rareza_de(carta)
    materiales["p"] = materiales.get("p", 0) + polvo
    return polvo


def construir_mazo(
    secta: str,
    *,
    con_coleccion: bool = False,
    coleccion: dict[str, int] | None = None,
    extras: int = 0,
    aleatorio: Callable[[], float] | None = None,
) -> list[str]:
    """Construye un mazo de hasta 40 cartas (`deck()` del JS).

    Semántica del monolito:

    1. Las 5 cartas base de la secta, hasta 3 copias de cada una.
    2. `extras` cartas aleatorias de la misma secta (no base, no reliquia).
    3. Si `con_coleccion`, se añaden todas las copias de la colección.
    4. Se rellena con cartas neutrales (hasta 40) en orden barajado.
    5. El resultado final se baraja y se recorta a 40.

    Nota: el JS usa `Math.random` para los extras y `RNG.shuffle` para
    el orden; aquí se inyecta un único `aleatorio` para ambas cosas
    (el backend usará el `GeneradorAleatorio` de la partida). Si no se
    pasa, se usa `random.random` de la stdlib (sólo para tests/manuales).

    Args:
        secta: clave de la secta (`'esp'`, …).
        con_coleccion: incluir las cartas de la colección del jugador.
        coleccion: dict id → nº copias (si `con_coleccion`).
        extras: nº de cartas extra de la secta.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Lista de ids (máx. 40) barajada.
    """
    import random as _random

    azar = aleatorio or _random.random

    def barajar(lista: list[str]) -> list[str]:
        valores = list(lista)
        for posicion in range(len(valores) - 1, 0, -1):
            otra = math.floor(azar() * (posicion + 1))
            valores[posicion], valores[otra] = valores[otra], valores[posicion]
        return valores

    def elegir(lista: list[str]) -> str:
        return lista[math.floor(azar() * len(lista))]

    base = SECTAS[secta].cartas_iniciales
    conteo: dict[str, int] = {}

    def agregar(identificador: str) -> bool:
        if conteo.get(identificador, 0) >= 3:
            return False
        conteo[identificador] = conteo.get(identificador, 0) + 1
        return True

    for identificador_base in base:
        agregar(identificador_base)
        agregar(identificador_base)
        agregar(identificador_base)

    if extras:
        misma_secta = [
            identificador
            for identificador, carta in CARTAS.items()
            if SECTA_DE_CARTA.get(identificador) == secta
            and identificador not in base
            and not carta.reliquia
        ]
        for _ in range(extras):
            if misma_secta:
                agregar(elegir(misma_secta))

    if con_coleccion:
        for identificador, cantidad in (coleccion or {}).items():
            for _ in range(cantidad):
                agregar(identificador)

    total = sum(conteo.values())
    neutrales_barajadas = barajar(
        [
            identificador
            for identificador in CARTAS_NEUTRALES
            for _ in (0, 1, 2)
        ]
    )
    for identificador in neutrales_barajadas:
        if total >= 40:
            break
        if agregar(identificador):
            total += 1

    plana: list[str] = []
    for identificador, cantidad in conteo.items():
        plana.extend([identificador] * cantidad)
    return barajar(plana)[:40]


# ---------- Mazos (tab `dk` del monolito) ----------

#: Máximo de mazos guardados (`mzs.length >= 8` en `dNew`/`dDup`).
MAX_MAZOS = 8

#: Tamaño exacto de un mazo válido (`DM` en `js/03-cartas-mercado.js:35`).
TAMANO_MAZO = 40

#: Copias máximas de una carta en un mazo o usables en combate (`MAXSK`).
MAX_COPIAS = 3


def copias_usables(
    identificador: str, secta: str, coleccion: dict[str, int]
) -> int:
    """Máximo de copias de una carta en un mazo (`own3` del JS).

    Referencia: `js/03-cartas-mercado.js:35`. Las 5 cartas base de la
    secta del jugador y las neutrales son usables hasta en 3 copias
    aunque no estén en la colección; el resto se limita a lo poseído.

    Args:
        identificador: id de la carta.
        secta: secta del jugador (`sect` global en el JS).
        coleccion: cartas poseídas, id → nº copias (`col`).

    Returns:
        Copias usables (0–3).
    """
    base = SECTAS[secta].cartas_iniciales if secta in SECTAS else ()
    gratis = identificador in base or identificador in CARTAS_NEUTRALES
    return min(MAX_COPIAS, max(3 if gratis else 0, coleccion.get(identificador, 0)))


def tamano_mazo(mazo: dict) -> int:
    """Número de cartas de un mazo (`dsz` del JS).

    Args:
        mazo: mazo guardado ``{"n": nombre, "c": {id: copias}}``.

    Returns:
        Suma de copias de todas las cartas.
    """
    return sum(mazo.get("c", {}).values())


def mazo_valido(mazo: dict | None, secta: str, coleccion: dict[str, int]) -> bool:
    """True si el mazo es jugable (`dok` del JS).

    Referencia: `js/03-cartas-mercado.js:35`. Un mazo es válido si
    tiene exactamente `TAMANO_MAZO` cartas y cada carta existe en el
    catálogo con copias ≤ `copias_usables`.

    Args:
        mazo: mazo guardado o None.
        secta: secta del jugador.
        coleccion: cartas poseídas.

    Returns:
        True si es jugable.
    """
    if not mazo:
        return False
    if tamano_mazo(mazo) != TAMANO_MAZO:
        return False
    return all(
        identificador in CARTAS
        and cantidad <= copias_usables(identificador, secta, coleccion)
        for identificador, cantidad in mazo.get("c", {}).items()
    )


def mazo_activo_plano(
    mazo: dict | None, secta: str, coleccion: dict[str, int]
) -> list[str] | None:
    """Mazo activo como lista de ids (`actDeck` del JS).

    Referencia: `js/03-cartas-mercado.js:36`. Devuelve None si el mazo
    no es válido (en combate se usa el automático).

    Args:
        mazo: mazo activo o None.
        secta: secta del jugador.
        coleccion: cartas poseídas.

    Returns:
        Lista de 40 ids o None.
    """
    if not mazo_valido(mazo, secta, coleccion):
        return None
    return [
        identificador
        for identificador, cantidad in mazo["c"].items()
        for _ in range(cantidad)
    ]


def crear_mazo(
    mazos: list[dict],
    *,
    desde_automatico: bool,
    secta: str,
    coleccion: dict[str, int],
    aleatorio: Callable[[], float] | None = None,
) -> dict:
    """Crea y añade un mazo nuevo (`dNew` del JS).

    Referencia: `js/04-mazos-formaciones.js:9`. Con `desde_automatico`
    el contenido son las cuentas del mazo automático (`deck(sect, true)`:
    base ×3 + colección + neutrales, hasta 40).

    Args:
        mazos: lista de mazos guardados (mutada).
        desde_automatico: copiar el mazo automático en vez de vacío.
        secta: secta del jugador.
        coleccion: cartas poseídas.
        aleatorio: callback float para el barajado del automático.

    Returns:
        El mazo creado (mismo objeto añadido a la lista).

    Raises:
        ValueError: ya hay `MAX_MAZOS` mazos.
    """
    if len(mazos) >= MAX_MAZOS:
        raise ValueError(f"Máximo {MAX_MAZOS} mazos")
    conteo: dict[str, int] = {}
    if desde_automatico:
        for identificador in construir_mazo(
            secta,
            con_coleccion=True,
            coleccion=coleccion,
            aleatorio=aleatorio,
        ):
            conteo[identificador] = conteo.get(identificador, 0) + 1
    mazo = {"n": f"Mazo {len(mazos) + 1}", "c": conteo}
    mazos.append(mazo)
    return mazo


def renombrar_mazo(mazo: dict, nombre: str) -> str:
    """Renombra un mazo (`dRen` del JS).

    Referencia: `js/04-mazos-formaciones.js:13`. Se recorta a 22
    caracteres y se ignoran nombres vacíos tras recortar.

    Args:
        mazo: mazo guardado (mutado).
        nombre: nombre nuevo.

    Returns:
        El nombre aplicado, o '' si se ignoró (vacío tras recortar).
    """
    aplicado = nombre.strip()[:22]
    if not aplicado:
        return ""
    mazo["n"] = aplicado
    return aplicado


def anadir_carta_a_mazo(
    mazo: dict, identificador: str, secta: str, coleccion: dict[str, int]
) -> bool:
    """Añade 1 copia de una carta al mazo (`dAdd` del JS).

    Referencia: `js/04-mazos-formaciones.js:11`. Se niega si el mazo
    está lleno o ya se alcanzaron las copias usables.

    Args:
        mazo: mazo guardado (mutado).
        identificador: id de la carta.
        secta: secta del jugador.
        coleccion: cartas poseídas.

    Returns:
        True si se añadió.
    """
    conteo = mazo.setdefault("c", {})
    if conteo.get(identificador, 0) >= copias_usables(
        identificador, secta, coleccion
    ):
        return False
    if tamano_mazo(mazo) >= TAMANO_MAZO:
        return False
    conteo[identificador] = conteo.get(identificador, 0) + 1
    return True


def quitar_carta_de_mazo(mazo: dict, identificador: str) -> bool:
    """Quita 1 copia de una carta del mazo (`dRm` del JS).

    Referencia: `js/04-mazos-formaciones.js:12`. Si llega a 0 se
    borra la clave (como el JS).

    Args:
        mazo: mazo guardado (mutado).
        identificador: id de la carta.

    Returns:
        True si había copias que quitar.
    """
    conteo = mazo.get("c", {})
    if not conteo.get(identificador):
        return False
    conteo[identificador] -= 1
    if not conteo[identificador]:
        del conteo[identificador]
    return True


def vaciar_mazo(mazo: dict) -> None:
    """Vacía un mazo (`dClr` del JS).

    Referencia: `js/04-mazos-formaciones.js:14`.

    Args:
        mazo: mazo guardado (mutado).
    """
    mazo["c"] = {}


def autocompletar_mazo(
    mazo: dict,
    secta: str,
    coleccion: dict[str, int],
    aleatorio: Callable[[], float] | None = None,
) -> None:
    """Rellena el mazo con las mejores cartas poseídas (`dFill` del JS).

    Referencia: `js/04-mazos-formaciones.js:15`. Orden: cartas de la
    secta del jugador primero, después por coste de qi ascendente y
    por rareza ascendente. Reparte copias en rondas (1, luego 2, luego
    3) hasta `TAMANO_MAZO` o hasta las copias usables de cada carta.

    Args:
        mazo: mazo guardado (mutado).
        secta: secta del jugador.
        coleccion: cartas poseídas.
        aleatorio: aceptado por simetría con las demás reglas de mazo;
            el orden del JS no usa azar, así que se ignora.
    """
    del aleatorio  # dFill no aleatoriza: el orden es determinista
    conteo = mazo.setdefault("c", {})
    identificables = [
        identificador
        for identificador in CARTAS
        if copias_usables(identificador, secta, coleccion) > 0
    ]
    identificables.sort(
        key=lambda identificador: (
            0 if SECTA_DE_CARTA.get(identificador) == secta else 1,
            CARTAS[identificador].coste_qi,
            rareza_de(CARTAS[identificador]),
        )
    )
    for ronda in range(1, MAX_COPIAS + 1):
        for identificador in identificables:
            if tamano_mazo(mazo) >= TAMANO_MAZO:
                return
            limite = min(ronda, copias_usables(identificador, secta, coleccion))
            if conteo.get(identificador, 0) < limite:
                conteo[identificador] = conteo.get(identificador, 0) + 1


def duplicar_mazo(mazos: list[dict], indice: int) -> dict:
    """Duplica un mazo (`dDup` del JS).

    Referencia: `js/04-mazos-formaciones.js:17`. El nombre se copia
    con el sufijo « (copia)» y se recorta a 22 caracteres.

    Args:
        mazos: lista de mazos guardados (mutada).
        indice: índice del mazo a copiar.

    Returns:
        El mazo nuevo (mismo objeto añadido a la lista).

    Raises:
        ValueError: índice inválido o `MAX_MAZOS` mazos.
    """
    if len(mazos) >= MAX_MAZOS:
        raise ValueError(f"Máximo {MAX_MAZOS} mazos")
    origen = mazos[indice]
    copia = {"n": (origen["n"] + " (copia)")[:22], "c": dict(origen.get("c", {}))}
    mazos.append(copia)
    return copia


def eliminar_mazo(mazos: list[dict], indice: int, mazo_activo: int) -> int:
    """Elimina un mazo y reajusta el índice activo (`dDel` del JS).

    Referencia: `js/04-mazos-formaciones.js:18`. Si se borra el mazo
    activo, el activo pasa a -1 (automático); si era anterior, se
    decrementa.

    Args:
        mazos: lista de mazos guardados (mutada).
        indice: índice del mazo a eliminar.
        mazo_activo: índice del mazo en uso (`mza`).

    Returns:
        El nuevo índice del mazo activo.
    """
    del mazos[indice]
    if mazo_activo == indice:
        return -1
    if mazo_activo > indice:
        return mazo_activo - 1
    return mazo_activo


def desequipar_del_activo(
    mazos: list[dict], mazo_activo: int, identificador: str
) -> bool:
    """Quita 1 copia del mazo en uso desde la colección (`dUneq`).

    Referencia: `js/12-v47-init.js:25`. Opera sobre el mazo activo
    (`mzs[mza]`), no sobre un índice cualquiera.

    Args:
        mazos: lista de mazos guardados.
        mazo_activo: índice del mazo en uso (`mza`).
        identificador: id de la carta.

    Returns:
        True si se quitó una copia.
    """
    if mazo_activo < 0 or mazo_activo >= len(mazos):
        return False
    return quitar_carta_de_mazo(mazos[mazo_activo], identificador)


# --- Mercado (tab `mkt` del monolito) ---------------------------------------
#
# Fuente: `buy`/`buyM`/`sellM`/`mkt`/`mkDet` de
# `js/03-cartas-mercado.js` + el override v47 de `js/12-v47-init.js:131-167`
# (píldoras, confirmaciones y filtro `vzOk`).

#: Límite de mano que menciona la descripción del Abismo (`HM` del JS).
LIMITE_MANO = 5

#: Claves de habilidad que escalan «a 1 al máximo de pila» (`SKU`).
CLAVES_SKILL_FIJO = frozenset("rqe")

#: Efectos por tipo de último aliento (`ULT` de `js/01-datos.js:184`).
EFECTOS_ULTIMO_ALIENTO: dict[str, str] = {
    "d": "daña {n} al héroe rival",
    "h": "cura {n}",
    "r": "roba {n}",
    "s": "escudo {n}",
    "e": "el rival pierde {n} Qi",
    "q": "+{n} Qi",
}

#: Palabras clave de cartas (`KI` de `js/04-mazos-formaciones.js:68`;
#: aquí solo el texto, sin los iconos SVG).
PALABRAS_CLAVE: dict[str, str] = {
    "rf": (
        "Renovar: devuelve tu mano al mazo y roba cartas nuevas al azar"
    ),
    "tk": "Provocar: hay que atacarla primero",
    "rs": "Ímpetu: ataca el turno en que entra",
    "vm": "Roba vida: cura lo que daña",
    "gr": "Crece: gana ataque al atacar",
    "ul": "Último aliento: efecto al morir",
    "bc": "Al entrar: efecto inmediato",
    "ab": "Activa: habilidad que cuesta Qi",
    "fz": "Congela: pierde su próximo ataque",
    "k": "Espada: cada 3ª técnica de espada da +3 de daño a la siguiente",
    "dsp": "Disipa formaciones y runas rivales",
    "eq": "Drena Qi: el rival pierde Qi en su turno",
    "dr": "Roba cartas",
    "sac": "Pagas vida al jugarla",
}

#: Clave corta `KI` → atributo del `CartaData` equivalente (el JS
#: filtra `Object.keys(KI).filter(k => c[k])` sobre sus propias claves).
ATRIBUTO_PALABRA_CLAVE: dict[str, str] = {
    "rf": "renovar",
    "tk": "provocar",
    "rs": "impetu",
    "vm": "robar_vida",
    "gr": "crece",
    "ul": "ultimo_aliento",
    "bc": "al_entrar",
    "ab": "habilidad_activa",
    "fz": "congelar",
    "k": "es_espada",
    "dsp": "disipa",
    "eq": "drenar_qi_rival",
    "dr": "robar",
    "sac": "sacrificar_vida",
}


def precio_pildora_mercado(identificador: str) -> int:
    """Precio de compra de una píldora (`mkcPrice` del JS).

    Referencia: `js/12-v47-init.js:133`.
    ``max(8, round((h*6 + n*14 + p*8) * 1.7))`` con el `Math.round`
    del monolito (`redondear_js`).

    Args:
        identificador: clave en `PILDORAS`.

    Returns:
        Precio en piedras espirituales.
    """
    pildora = PILDORAS[identificador]
    hierbas = pildora.coste.get(Material.HIERBAS, 0)
    nucleos = pildora.coste.get(Material.NUCLEOS, 0)
    polvo = pildora.coste.get(Material.POLVO_JADE, 0)
    bruto = (hierbas * 6 + nucleos * 14 + polvo * 8) * 1.7
    return max(8, redondear_js(bruto))


def pildoras_en_venta(recetas: dict[str, int]) -> list[str]:
    """Píldoras/talismanes a la venta en el puesto General (`mkcList`).

    Referencia: `js/12-v47-init.js:132`. Se excluyen `inm` y `rar`;
    el resto se vende si se conoce su receta (`rec`) o es de las
    básicas (`MKC_BASIC`). El orden es el del catálogo `PILDORAS`.

    Args:
        recetas: recetas aprendidas (`rec`).

    Returns:
        Lista de identificadores en orden de catálogo.
    """
    return [
        identificador
        for identificador in PILDORAS
        if identificador not in {"inm", "rar"}
        and (recetas.get(identificador) or identificador in PILDORAS_BASICAS_MERCADO)
    ]


def tipo_pildora_mercado(identificador: str) -> str:
    """Etiqueta de tipo para el detalle de compra (`pillKind` del JS).

    Referencia: `js/12-v47-init.js:134`.
    """
    if identificador == "tes":
        return "Talismán"
    pildora = PILDORAS[identificador]
    if pildora.es_recuperacion:
        return "Píldora de recuperación (Cueva)"
    if pildora.es_combate:
        return "Píldora de combate ⚡"
    return "Píldora de inicio"


def _secta_visible(identificador: str) -> str | None:
    """`SX(id)` del JS: `SC[id] == 'neu'` cuenta como sin secta."""
    secta = SECTA_DE_CARTA.get(identificador)
    return None if secta == "neu" else secta


def cartas_en_venta(
    secta_puesto: str,
    secta_elegida: str,
    coleccion: dict[str, int],
    misiones: dict,
) -> list[str]:
    """Cartas que lista el puesto dado (`ids` de `mkt()`, v47).

    Referencia: `js/12-v47-init.js:157`. Filtros: sin reliquia
    (`lk`), rareza < 5, disponible en el Abismo (`vzOk`) y secta:
    en el puesto General sólo cartas sin secta visible (incluye las
    coleccionables `'neu'`); en un puesto de secta, las de esa secta
    que no sean de las 5 iniciales (`S[ks].l`). Orden: rareza asc,
    coste de Qi asc.

    Args:
        secta_puesto: clave del puesto (`ks`; `'neu'` = General).
        secta_elegida: secta del jugador (`schosen`).
        coleccion: inventario de cartas (`col`).
        misiones: contadores `qs` (registro del Abismo en `vz`).

    Returns:
        Identificadores de carta ordenados.
    """

    def lista(carta) -> bool:
        if carta.reliquia:
            return False
        if rareza_de(carta) >= 5:
            return False
        if not carta_abismo_disponible(
            coleccion, misiones, carta.identificador
        ):
            return False
        visible = _secta_visible(carta.identificador)
        if secta_puesto == "neu":
            return visible is None
        starters = SECTAS[secta_puesto].cartas_iniciales
        return visible == secta_puesto and carta.identificador not in starters

    candidatas = [carta for carta in CARTAS.values() if lista(carta)]
    candidatas.sort(
        key=lambda carta: (rareza_de(carta), carta.coste_qi)
    )
    return [carta.identificador for carta in candidatas]


def _texto_ultimo_aliento(tipo: str, valor: int) -> str:
    return EFECTOS_ULTIMO_ALIENTO[tipo].format(n=valor)


def _efecto_turno_texto(ts: tuple) -> str:
    """Texto de un efecto por turno de Formación/Runa (`TSD`).

    Referencia: `js/04-mazos-formaciones.js:33`.
    """
    tipo, valor = ts
    textos = {
        TipoEfecto.DANO_HROE: f"daña {valor} al héroe rival",
        TipoEfecto.CURAR: f"cura {valor}",
        TipoEfecto.ESCUDO: f"escudo {valor}",
        TipoEfecto.ROBAR: f"roba {valor}",
        TipoEfecto.GANAR_QI: f"+{valor} Qi",
        TipoEfecto.DANO_CRIATURA_AL_AZAR: (
            f"daña {valor} a una criatura rival al azar"
        ),
        TipoEfecto.AUTO_DANO: f"pierdes {valor} de vida",
    }
    return textos.get(tipo, str(tipo))


def descripcion_fr(carta) -> list[str]:
    """Descripción de Formación/Runa (`FRd` del JS).

    Referencia: `js/04-mazos-formaciones.js:34`. Líneas de texto plano
    (el HTML `<strong>`/`kwH` lo reconstruye la UI).

    Args:
        carta: `CartaData` de tipo F o R.

    Returns:
        Lista de líneas: tipo, mejora de ATK/vida, efecto por turno y
        pago de vida.
    """
    etiqueta = (
        "Formación"
        if carta.tipo == TipoCarta.FORMACION
        else f"Runa · {carta.duracion_turnos} turnos"
    )
    lineas = [etiqueta]
    if carta.mejora_ataque_al_trazar:
        lineas.append(
            f"Tus criaturas: +{carta.mejora_ataque_al_trazar} ATK"
        )
    if carta.mejora_vida_al_trazar:
        lineas.append(
            f"Criaturas aliadas: +{carta.mejora_vida_al_trazar} vida"
        )
    if carta.efecto_inicio_turno:
        prefijo = (
            "Cada turno: "
            if carta.tipo == TipoCarta.FORMACION
            else "Al inicio de tu turno: "
        )
        lineas.append(prefijo + _efecto_turno_texto(carta.efecto_inicio_turno))
    if carta.sacrificar_vida:
        lineas.append(f"Pagas {carta.sacrificar_vida} de vida")
    return lineas


def descripcion_carta(carta) -> list[str]:
    """Descripción de efectos de una carta (`descH` del JS).

    Referencia: `js/02-motor.js:80-92`. Devuelve una lista de líneas
    de texto plano (el HTML con `<strong>`/`<u class="kw">` del
    monolito lo reconstruye la UI). Para cartas Formación/Runa usa
    `descripcion_fr` (port de `FRd`, js/04-mazos-formaciones.js:34).

    Args:
        carta: `CartaData` del catálogo.

    Returns:
        Lista de líneas (vacía si la carta no tiene efectos).
    """
    if carta.tipo in {TipoCarta.FORMACION, TipoCarta.RUNA}:
        return descripcion_fr(carta)
    lineas: list[str] = []
    if carta.provocar:
        lineas.append("Provocar")
    if carta.impetu:
        lineas.append("Ímpetu")
    if carta.robar_vida:
        lineas.append("Roba vida")
    if carta.al_entrar:
        lineas.append(
            f"Al entrar: {carta.al_entrar.valor} daño a una criatura "
            "rival al azar (o al héroe si no hay)"
        )
    if carta.dano_hroe:
        lineas.append(f"Daña {carta.dano_hroe} al héroe rival")
    if carta.dano_criatura:
        congelacion = " y la congela" if carta.congelar else ""
        lineas.append(
            f"Daña {carta.dano_criatura} a una criatura rival"
            f"{congelacion} (si no hay, al héroe)"
        )
    elif carta.congelar:
        lineas.append("Congela")
    if carta.dano_area:
        lineas.append(
            f"Daña {carta.dano_area} a todas las criaturas rivales"
        )
    if carta.tribulacion:
        lineas.append("Daña 3 a ambos héroes y 4 a todas las criaturas")
    if carta.renovar:
        lineas.append(
            "Renovar: devuelve tu mano al mazo y roba " f"{carta.renovar}"
        )
    if carta.vacio_descarte:
        cartas_txt = "s" if carta.vacio_descarte > 1 else ""
        lineas.append(
            "Vacío: el rival descarta "
            f"{carta.vacio_descarte} carta{cartas_txt} al azar"
        )
    if carta.ciclo:
        lineas.append("Ciclo: descarta tu mano y roba la misma cantidad")
    if carta.abismo_traer:
        eleccion = "elige " if carta.abismo_elegir else "trae al azar "
        cartas_txt = "s" if carta.abismo_traer > 1 else ""
        ponlas = "ponlas" if carta.abismo_traer > 1 else "ponla"
        lineas.append(
            "Abismo: "
            f"{eleccion}{carta.abismo_traer} carta{cartas_txt} del "
            f"Agujero Negro y {ponlas} en tu mano (puede superar el "
            f"límite de {LIMITE_MANO} hasta el fin del turno)"
        )
    if carta.samsara:
        cartas_txt = "s" if carta.samsara > 1 else ""
        lineas.append(
            "Samsara: baraja "
            f"{carta.samsara} carta{cartas_txt} al azar del "
            "Agujero Negro en tu mazo"
        )
    if carta.disipa:
        lineas.append(
            "Disipa: destruye las formaciones y runas rivales"
        )
    if carta.curar:
        if carta.curar_porcentaje:
            lineas.append(
                f"Cura {carta.curar_porcentaje}% de tu vida máx. "
                f"(mín. {carta.curar})"
            )
        else:
            lineas.append(f"Cura {carta.curar}")
    if carta.escudo:
        lineas.append(f"Escudo {carta.escudo}")
    if carta.robar:
        lineas.append(f"Roba {carta.robar}")
    if carta.ganar_qi:
        lineas.append(f"+{carta.ganar_qi} Qi")
    if carta.drenar_qi_rival:
        lineas.append(
            f"El rival pierde {carta.drenar_qi_rival} Qi en su turno"
        )
    if carta.mejorar_aliada:
        mejora = carta.mejorar_aliada
        lineas.append(
            f"Aliada: +{mejora.ataque} ATK / +{mejora.vida} vida "
            "(sin aliadas: escudo 3)"
        )
    if carta.sacrificar_vida:
        lineas.append(f"Pagas {carta.sacrificar_vida} de vida")
    if carta.crece:
        lineas.append(f"Crece +{carta.crece} al atacar")
    if carta.ultimo_aliento:
        aliento = carta.ultimo_aliento
        lineas.append(
            "Último aliento: "
            + _texto_ultimo_aliento(aliento.tipo.value, aliento.valor)
        )
    if carta.habilidad_activa:
        habilidad = carta.habilidad_activa
        lineas.append(
            f"Activa ({habilidad.coste_qi} Qi): {habilidad.descripcion}"
        )
    if carta.es_espada:
        lineas.append("⚔ Espada")
    return lineas


def estadisticas_carta(carta) -> list[tuple[str, str]]:
    """Filas «Estadísticas» del detalle (`st` de `mkDet`).

    Referencia: `js/03-cartas-mercado.js:17-23` (mapeo `PROP` de
    `js/03-cartas-mercado.js:13` más las filas de `bf`/`ul`/`ab`/`bc`).

    Args:
        carta: `CartaData` del catálogo.

    Returns:
        Lista de pares (etiqueta, valor como texto).
    """
    filas: list[tuple[str, str]] = []

    def simple(etiqueta: str, valor) -> None:
        if valor is not None:
            filas.append((etiqueta, str(valor)))

    simple("Ataque", carta.ataque)
    simple("Vida", carta.vida)
    simple("Daño directo al héroe rival", carta.dano_hroe)
    simple("Daño a una criatura rival", carta.dano_criatura)
    simple("Daño a todas las criaturas rivales", carta.dano_area)
    if carta.curar is not None:
        if carta.curar_porcentaje:
            filas.append(
                (
                    "Curación",
                    f"{carta.curar_porcentaje}% de vida máx. "
                    f"(mín. {carta.curar})",
                )
            )
        else:
            filas.append(("Curación", str(carta.curar)))
    simple("Escudo", carta.escudo)
    simple("Cartas que robas", carta.robar)
    simple("Qi que ganas", carta.ganar_qi)
    simple("Qi que pierde el rival en su turno", carta.drenar_qi_rival)
    simple("Vida que pagas al jugarla", carta.sacrificar_vida)
    if carta.mejorar_aliada:
        mejora = carta.mejorar_aliada
        filas.append(
            (
                "Mejora a una aliada",
                f"+{mejora.ataque} ATK / +{mejora.vida} vida",
            )
        )
    if carta.ultimo_aliento:
        aliento = carta.ultimo_aliento
        filas.append(
            (
                "Último aliento",
                _texto_ultimo_aliento(aliento.tipo.value, aliento.valor),
            )
        )
    if carta.habilidad_activa:
        habilidad = carta.habilidad_activa
        filas.append(
            (
                f"Habilidad activa ({habilidad.coste_qi} Qi)",
                habilidad.descripcion,
            )
        )
    if carta.al_entrar:
        filas.append(
            (
                "Al entrar",
                f"{carta.al_entrar.valor} de daño a una criatura "
                "rival al azar",
            )
        )
    return filas


def _bonus_skill(clave: str, valor: int, pila: int) -> int:
    """`skFx(k, v, n)` de `js/02-motor.js:2`."""
    if clave in CLAVES_SKILL_FIJO:
        return 1 if pila >= MAX_COPIAS else 0
    return (pila - 1) * math.ceil(valor / 2)


def subir_acumulacion(carta, estado: dict) -> dict:
    """Aplica una pila más sobre el estado de acumulación (`stkUp`).

    Referencia: `js/02-motor.js:4-8`. El estado (`T` del JS) lleva
    `sk`, `A`, `H` y opcionalmente `ul`/`ab`/`gr` ya ajustados; aquí
    se devuelve siempre un dict mutado.

    Args:
        carta: `CartaData` de la criatura apilada.
        estado: dict con `sk`, `A`, `H` y claves opcionales `ul_valor`,
            `ab_valor`, `ab_texto`, `gr`.

    Returns:
        El mismo dict, con la pila incrementada.
    """
    pila = estado["sk"] + 1
    estado["sk"] = pila
    estado["A"] += math.ceil(carta.ataque / 2)
    estado["H"] += math.ceil(carta.vida / 2)
    if carta.ultimo_aliento:
        aliento = carta.ultimo_aliento
        estado["ul_valor"] = aliento.valor + _bonus_skill(
            aliento.tipo.value, aliento.valor, pila
        )
    if carta.habilidad_activa:
        habilidad = carta.habilidad_activa
        nuevo = habilidad.valor + _bonus_skill(
            habilidad.tipo.value, habilidad.valor, pila
        )
        estado["ab_valor"] = nuevo
        estado["ab_texto"] = habilidad.descripcion.replace(
            str(habilidad.valor), str(nuevo), 1
        )
    if carta.crece:
        estado["gr"] = carta.crece + (1 if pila >= MAX_COPIAS else 0)
    return estado


def _efectos_acumulacion(carta, estado: dict) -> str:
    """Texto de efectos de una fila de la tabla (`stEff` del JS)."""
    partes: list[str] = []
    if carta.ultimo_aliento:
        valor = estado.get("ul_valor", carta.ultimo_aliento.valor)
        partes.append(
            "Último aliento: "
            + _texto_ultimo_aliento(carta.ultimo_aliento.tipo.value, valor)
        )
    if carta.habilidad_activa:
        partes.append(
            "Activa: "
            + estado.get(
                "ab_texto", carta.habilidad_activa.descripcion
            )
        )
    if estado.get("gr"):
        partes.append(f"Crece +{estado['gr']}")
    if carta.al_entrar:
        partes.append(f"Al entrar: {carta.al_entrar.valor} de daño")
    return " · ".join(partes)


def tabla_acumulacion(carta) -> list[dict] | None:
    """Tabla de acumulación del detalle (`ac` de `mkDet`).

    Referencia: `js/03-cartas-mercado.js:17-23` + `stkUp` de
    `js/02-motor.js:4`. Sólo las criaturas que se acumulan (no
    bestias) tienen tabla.

    Args:
        carta: `CartaData` del catálogo.

    Returns:
        Fila por nivel de pila (``pila``, ``ataque``, ``vida``,
        ``efectos``); None si no se acumula.
    """
    if carta.tipo != TipoCarta.CRIATURA or carta.bestia:
        return None
    estado: dict = {
        "sk": 1,
        "A": carta.ataque,
        "H": carta.vida,
    }
    if carta.crece:
        estado["gr"] = carta.crece
    filas = [
        {
            "pila": 1,
            "ataque": estado["A"],
            "vida": estado["H"],
            "efectos": _efectos_acumulacion(carta, estado),
        }
    ]
    for nivel in range(2, MAX_COPIAS + 1):
        subir_acumulacion(carta, estado)
        filas.append(
            {
                "pila": nivel,
                "ataque": estado["A"],
                "vida": estado["H"],
                "efectos": _efectos_acumulacion(carta, estado),
            }
        )
    return filas


def obtencion_carta(identificador: str, secta_elegida: str) -> list[str]:
    """Sección «Obtención» del detalle (`howGet` del JS).

    Referencia: `js/04-mazos-formaciones.js:51-56`. El primer enemigo
    con recompensa de rareza ``r … r+2`` viene del catálogo aplanado
    `CH` (= `ENEMIGOS`).

    Args:
        identificador: id de la carta.
        secta_elegida: secta del jugador (`schosen`).

    Returns:
        Lista de líneas (cada una un párrafo del monolito).
    """
    carta = CARTAS[identificador]
    rareza = rareza_de(carta)
    enemigo = next(
        (
            enemigo
            for enemigo in ENEMIGOS
            if rareza <= enemigo.rareza_recompensa <= rareza + 2
        ),
        None,
    )
    lineas: list[str] = []
    if identificador in CARTAS_NEUTRALES:
        lineas.append(
            "🎁 Gratis: carta neutral, ya la tienes (×3)."
        )
        return lineas
    secta = _secta_visible(identificador)
    if rareza >= 5:
        lineas.append(
            "🏆 No se vende: es de las cartas más poderosas y solo "
            "cae de jefes."
        )
    else:
        puesto = f"de {SECTAS[secta].nombre}" if secta else "General"
        bloqueo = (
            ""
            if not secta or secta == secta_elegida
            else " · 🔒 solo discípulos de esa secta"
        )
        lineas.append(
            f"💎 Mercado: puesto {puesto} · {precio_compra(identificador)}"
            f"{bloqueo}"
        )
    if enemigo:
        rango = (
            f"a {RAREZAS[min(5, rareza + 2)]}" if rareza < 5 else ""
        )
        lineas.append(
            f"⚔ Premio de combate: enemigos con recompensa "
            f"{RAREZAS[rareza]} {rango}. El primero: nivel "
            f"{enemigo.indice_nivel + 1}, {enemigo.nombre_enemigo} "
            f"({DIFICULTADES[enemigo.dificultad]})."
        )
    return lineas


# --- Gacha (Ceremonia de Adivinación Ancestral) -----------------------------
#
# Fuente: `js/14-gacha.js` (`draw`/`generateReward`). El backend
# separa el sorteo puro (reglas) de la orquestación (servicio): aquí
# sólo viven la distribución de rarezas, la piedad y la generación de
# recompensas, con el azar inyectado como en todo el motor.


@dataclass(frozen=True, slots=True)
class RecompensaGacha:
    """Recompensa de una tirada del gacha (carta o polvo).

    Atributos:
        tipo: `'carta'` o `'recurso'` (`type` del JS).
        identificador: id de la carta obtenida, o None si es recurso.
        nombre: nombre visible de la recompensa.
        rareza: rareza de gacha sorteada (`common`…`legendary`).
        descripcion: texto de ayuda (lore o 'Esencia condensada…').
    """

    tipo: str
    identificador: str | None
    nombre: str
    rareza: str
    descripcion: str


def sortear_rareza_gacha(
    pool,
    indice: int,
    count: int,
    piedad: int,
    aleatorio: Callable[[], float],
) -> tuple[str, int]:
    """Sortea la rareza de una tirada del gacha (`draw` del JS).

    Referencia: `js/14-gacha.js:94-118`. Orden de prioridad:
    1. Si la piedad llegó a `guaranteedEpicAfter` → Épico y piedad a 0.
    2. Si es el décimo tiro de una tirada de 10 → al menos Raro
       (azar entre Legendario/Épico/Raro según las probabilidades).
    3. Azar normal acumulando las probabilidades del pool.

    Args:
        pool: `PoolGacha` del catálogo.
        indice: posición dentro de la tirada (0-based).
        count: nº total de tiradas (1 o 10).
        piedad: contador de piedad actual del pool.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Tupla (rareza de gacha, nueva piedad tras esta tirada).
    """
    probabilidades = pool.probabilidades
    if piedad >= pool.piedad.garantizado_epico_tras:
        return "epic", 0
    if count == 10 and indice == 9:
        r = aleatorio() * 100
        if r < probabilidades.legendary:
            rareza = "legendary"
        elif r < probabilidades.legendary + probabilidades.epic:
            rareza = "epic"
        else:
            rareza = "rare"
    else:
        rand = aleatorio() * 100
        acc = 0.0
        rareza = "common"
        for nombre, probabilidad in (
            ("common", probabilidades.common),
            ("rare", probabilidades.rare),
            ("epic", probabilidades.epic),
            ("legendary", probabilidades.legendary),
        ):
            acc += probabilidad
            if rand <= acc:
                rareza = nombre
                break
    if rareza in {"epic", "legendary"}:
        return rareza, 0
    return rareza, piedad + 1


def candidatas_gacha(rareza_gacha: str) -> list[str]:
    """Ids de carta sorteadas para una rareza de gacha.

    Referencia: `js/14-gacha.js:139`. El filtro usa la rareza fija
    de la carta (`C[id].r`), con el ``|| 1`` del JS para las que no
    la tienen; la rareza 0 del mapa se traduce a umbral 1 (todas).
    """
    objetivo = RAREZA_OBJETIVO.get(rareza_gacha, 0)
    umbral = 1 if objetivo == 0 else objetivo
    return [
        identificador
        for identificador, carta in CARTAS.items()
        if (carta.rareza_fija or 1) >= umbral
    ]


def generar_recompensa_gacha(
    rareza_gacha: str,
    coleccion: dict[str, int],
    materiales: dict[str, int],
    aleatorio: Callable[[], float],
    misiones: dict | None = None,
) -> RecompensaGacha:
    """Genera la recompensa de una tirada (`generateReward` del JS).

    Referencia: `js/14-gacha.js:134-163`. Con probabilidad 0.7 entrega
    una carta al azar de las candidatas de su rareza (pasando por
    `addCard`, con el wrapper del Abismo si se aporta `misiones`);
    si no, otorga polvo de jade (5/20/50 según rareza).

    Args:
        rareza_gacha: rareza sorteada (`common`…`legendary`).
        coleccion: inventario de cartas (mutado si sale carta).
        materiales: inventario de materiales (mutado en el caso de
            polvo o si la carta llena las 3 copias).
        aleatorio: callback float en ``[0, 1)``.
        misiones: contadores `qs` (opcional; paridad del wrapper del
            Abismo en `addCard`).

    Returns:
        La recompensa obtenida.
    """
    candidatas = candidatas_gacha(rareza_gacha)
    if candidatas and aleatorio() < PROBABILIDAD_CARTA:
        elegida = candidatas[
            math.floor(aleatorio() * len(candidatas))
        ]
        resultado = agregar_carta_coleccion(
            coleccion, materiales, elegida, misiones
        )
        return RecompensaGacha(
            "carta",
            elegida,
            resultado.nombre,
            rareza_gacha,
            "Técnica o Artefacto del Sendero",
        )
    cantidad = CANTIDAD_POLVO.get(rareza_gacha, 5)
    materiales["p"] = materiales.get("p", 0) + cantidad
    return RecompensaGacha(
        "recurso",
        None,
        f"{cantidad}x Polvo de Jade / Esencia",
        rareza_gacha,
        "Esencia condensada del Sendero",
    )


# --- Equipo (Herrería) y trajes (js/06-contenido.js:66-71) ---------------

TOPE_BONO_EQUIPO = 4
"""Tope del bono de equipo en Ataque y Qi (`Math.min(4, ...)` de `gearStat`)."""


def pieza_desbloqueada(pieza: PiezaData, victorias: list[int]) -> bool:
    """¿El plano está desbloqueado? (`g.u == null || wins.includes(g.u)`)."""
    return pieza.desbloqueo is None or pieza.desbloqueo in victorias


def puede_forjar_pieza(
    pieza: PiezaData,
    materiales: dict[str, int],
    equipo_guardado: dict,
    victorias: list[int],
) -> bool:
    """Precondiciones de `forgeG(id)`: sin poseer, desbloqueada y con pago."""
    return (
        not equipo_guardado.get(pieza.identificador)
        and pieza_desbloqueada(pieza, victorias)
        and puede_pagar(pieza.coste, materiales)
    )


def forjar_pieza(
    equipo_guardado: dict,
    equipado: dict,
    usos_equipo: dict,
    materiales: dict[str, int],
    victorias: list[int],
    identificador: str,
) -> None:
    """Forja una pieza (`forgeG(id)`; muta `gr`, `du`, `eq` y `mat`).

    Precondiciones: `puede_forjar_pieza(...)`. Si su hueco está vacío,
    la pieza se equipa sola.
    """
    objetivo = pieza(identificador)
    if objetivo is None:
        raise ValueError(f"pieza de equipo desconocida '{identificador}'")
    if not puede_forjar_pieza(objetivo, materiales, equipo_guardado, victorias):
        raise ValueError(f"no se puede forjar la pieza '{identificador}'")
    pagar(objetivo.coste, materiales)
    equipo_guardado[identificador] = 1
    if objetivo.usos:
        usos_equipo[identificador] = objetivo.usos
    if not equipado.get(objetivo.slot):
        equipado[objetivo.slot] = identificador


def equipar_pieza(equipado: dict, identificador: str) -> None:
    """Alterna equipar/retirar en el hueco de la pieza (`wearG(id)`)."""
    objetivo = pieza(identificador)
    if objetivo is None:
        raise ValueError(f"pieza de equipo desconocida '{identificador}'")
    if equipado.get(objetivo.slot) == identificador:
        equipado[objetivo.slot] = None
    else:
        equipado[objetivo.slot] = identificador


def gear_stat(equipado: dict, equipo_guardado: dict) -> dict[str, int]:
    """Bonos del equipo equipado y poseído (`gearStat()` del JS).

    Returns:
        Dict con `a`/`q` (con tope +4 cada uno, lo que se aplica en
        combate) y `ra`/`rq` (sin topear, para avisar del exceso).

    Nota: solo cuentan las piezas que se poseen (`gear[id]`), igual
    que en el monolito.
    """
    ataque = 0
    qi = 0
    for identificador in equipado.values():
        if not identificador:
            continue
        objetivo = PIEZAS.get(identificador)
        if objetivo and equipo_guardado.get(identificador):
            ataque += objetivo.ataque
            qi += objetivo.qi
    return {
        "a": min(TOPE_BONO_EQUIPO, ataque),
        "q": min(TOPE_BONO_EQUIPO, qi),
        "ra": ataque,
        "rq": qi,
    }


def puede_vestir_traje(
    secta: str, indice: int, victorias: list[int]
) -> bool:
    """¿El traje está desbloqueado? (`W >= TU[i]` de `trj()`)."""
    objetivo = traje(secta, indice)
    return objetivo is not None and len(victorias) >= objetivo.umbral


def vestir_traje(
    atuendo: dict[str, int],
    victorias: list[int],
    secta: str,
    indice: int,
) -> None:
    """Viste un traje de la secta (`wear(k, i)`; muta `of`).

    Precondiciones: `puede_vestir_traje(...)`.
    """
    if not puede_vestir_traje(secta, indice, victorias):
        raise ValueError(f"el traje {secta}[{indice}] no está desbloqueado")
    atuendo[secta] = indice


def bestia_desbloqueada(bestia, victorias: list[int]) -> bool:
    """¿Venciste al jefe que doma esta bestia? (`wins.includes(i*6+5)`).

    Args:
        bestia: `BestiaDomable` del catálogo (`BEAST[i]`).
        victorias: índices de enemigos vencidos (`wins`).
    """
    return bestia.indice_nivel * 6 + 5 in victorias
