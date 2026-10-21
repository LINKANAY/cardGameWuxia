"""Efectos de campaña puros — victoria, muerte, recompensas.

Portes de `chk`/`genRw`/`grantSQ`/`qw`/`permaDeath`/`ascendRealm`/
`keepHp`/`relicDrop` del monolito. No toca disco ni API: muta un
`Partida` y devuelve un resumen para la UI. El orquestador es
`CombatService` (story-003).

Referencias: `js/02-motor.js:46-52`, `js/01-datos.js:42,164`,
`js/03-cartas-mercado.js:34`, `js/06-contenido.js:84-85,232-235`.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from app.data.cartas import CARTAS, cartas_de_rareza, rareza_de
from app.data.narrativa import REINOS
from app.data.niveles import MISIONES_SECUNDARIAS
from app.data.sectas import SECTA_DE_CARTA, SECTAS
from app.data.tipos import EnemigoCatalogo
from app.engine.combat import vida_heroe_max
from app.engine.rules import (
    agregar_carta_coleccion,
    construir_mazo,
    generar_rareza_recompensa,
    mazo_activo_plano,
)
from app.engine.state import Partida

#: Máx. reino con ascenso automático por jefe de nivel (`realm < 8`).
REINO_MAX_ASCENSO: int = 8

#: Umbral de `wins` donde empiezan las mazmorras en el catálogo (`k >= 48`).
OFFSET_MAZMORRAS: int = 48

_PATRON_BESTIA = re.compile(
    r"Lobo|Murciélago|Zorro|Garza|Pez|Lagarto|Serpiente|Cría|Dragón|"
    r"Bestia|Planta|Hongo|Caldero"
)

#: Sectas de bestias espirituales (`isBeast` en `js/06-contenido.js:82`).
_SECTAS_BESTIA = frozenset({"bam", "dra"})


def es_bestia_enemigo(enemigo: EnemigoCatalogo) -> bool:
    """¿El enemigo cuenta como bestia para misiones? (`isBeast`).

    Args:
        enemigo: ficha aplanada del catálogo.

    Returns:
        True si su secta es `bam`/`dra` o el nombre casa el patrón.
    """
    if enemigo.secta in _SECTAS_BESTIA:
        return True
    return bool(_PATRON_BESTIA.search(enemigo.nombre_enemigo))


def ascender_reino(partida: Partida) -> bool:
    """Sube un reino (`ascendRealm` de js/06-contenido.js:235).

    Args:
        partida: partida a mutar.

    Returns:
        True si se ascendió.
    """
    if partida.nivel_reino >= len(REINOS) - 1:
        return False
    vida_antes = vida_heroe_max(partida.nivel_reino)
    partida.nivel_reino += 1
    ganancia = vida_heroe_max(partida.nivel_reino) - vida_antes
    if partida.vida_hroe is not None:
        partida.vida_hroe = min(
            vida_heroe_max(partida.nivel_reino),
            partida.vida_hroe + ganancia,
        )
    return True


def mantener_vida(partida: Partida, vida_combate: int | None) -> None:
    """Conserva la vida entre combates (`keepHp`).

    Args:
        partida: partida a mutar (`hp`).
        vida_combate: vida final del héroe en combate, o None.
    """
    if vida_combate is None or vida_combate <= 0:
        return
    partida.vida_hroe = max(
        1, min(vida_combate, vida_heroe_max(partida.nivel_reino))
    )


def contadores_victoria(partida: Partida, enemigo: EnemigoCatalogo) -> None:
    """Actualiza `qs` al ganar (`qw` de js/06-contenido.js:84).

    Args:
        partida: partida a mutar (subclave `qs`).
        enemigo: ficha vencida.
    """
    qs = partida.misiones
    qs["w"] = qs.get("w", 0) + 1
    if es_bestia_enemigo(enemigo):
        qs["bk"] = qs.get("bk", 0) + 1
    if enemigo.dificultad == 5 and not enemigo.indice_mazmorra:
        qs["bs"] = qs.get("bs", 0) + 1
    ek = qs.setdefault("ek", {})
    ek[enemigo.secta] = ek.get(enemigo.secta, 0) + 1
    if enemigo.indice_mazmorra:
        qs["dg"] = qs.get("dg", 0) + 1


def materiales_victoria(
    enemigo: EnemigoCatalogo,
    aleatorio: Callable[[], float],
    *,
    primera: bool,
) -> dict[str, int]:
    """Materiales y piedras de una victoria (`m` en `chk`).

    Args:
        enemigo: ficha vencida.
        aleatorio: callback float en ``[0, 1)``.
        primera: si es la primera victoria sobre este enemigo.

    Returns:
        Dict con claves `'h'`, `'p'`, `'n'`, `'s'` (piedras).
    """
    d = enemigo.dificultad or 0
    li = enemigo.indice_nivel or 0
    hierbas = 1 + math.floor(aleatorio() * 2) + (d >> 1)
    polvo = 1 + d + (li >> 1)
    nucleos = 0
    if d >= 2:
        nucleos = (1 if aleatorio() < 0.5 else 0) + (1 if d >= 4 else 0) + (
            1 if d == 5 else 0
        )
    piedras = 2 + d * 2 + (li >> 1) + (5 * (d + 1) if primera else 0)
    return {"h": hierbas, "p": polvo, "n": nucleos, "s": piedras}


def gotear_reliquia(
    partida: Partida,
    enemigo: EnemigoCatalogo,
    aleatorio: Callable[[], float],
) -> str | None:
    """Suerte de reliquia al ganar (`relicDrop` de js/03-cartas-mercado.js:34).

    Args:
        partida: partida a mutar (`col`, `mat`, `qs.rp`).
        enemigo: ficha vencida.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Id de la carta reliquia obtenida, o None.
    """
    d = enemigo.dificultad or 0
    if d < 4:
        return None
    qs = partida.misiones
    rp = qs.get("rp") or 0
    p = (0.10 + (0.04 if enemigo.indice_mazmorra else 0.0)) if d == 5 else 0.02
    p += rp * 0.02
    if aleatorio() >= p:
        if d == 5:
            qs["rp"] = rp + 1
        return None
    clave_secta = enemigo.secta if enemigo.secta in SECTAS else partida.secta
    candidatos = [
        ident
        for ident, carta in CARTAS.items()
        if carta.reliquia and SECTA_DE_CARTA.get(ident) == clave_secta
    ]
    celestiales = [
        ident for ident in candidatos if rareza_de(CARTAS[ident]) == 5
    ]
    if d == 5 and celestiales and aleatorio() < 0.08:
        elegibles = celestiales
    else:
        elegibles = [
            ident for ident in candidatos if rareza_de(CARTAS[ident]) == 4
        ]
    if not elegibles:
        return None
    identificador = elegibles[math.floor(aleatorio() * len(elegibles))]
    qs["rp"] = 0
    if partida.coleccion.get(identificador, 0) >= 3:
        partida.materiales["p"] = (
            partida.materiales.get("p", 0) + 6
        )
    else:
        partida.coleccion[identificador] = (
            partida.coleccion.get(identificador, 0) + 1
        )
    return identificador


def otorgar_mision_secundaria(
    partida: Partida,
    enemigo: EnemigoCatalogo,
    aleatorio: Callable[[], float],
) -> str | None:
    """Recompensa al completar la misión secundaria (`grantSQ`).

    Args:
        partida: partida a mutar.
        enemigo: ficha de la fase final (``sqf == 2``).
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Texto legible de lo otorgado, o None si no aplica.
    """
    if not enemigo.indice_mision or enemigo.fase_mision != 2:
        return None
    mision = MISIONES_SECUNDARIAS[enemigo.indice_mision - 1]
    recompensa = mision.recompensa
    partes: list[str] = []
    if recompensa.piedras:
        partida.piedras_espirituales += recompensa.piedras
        partes.append(f"{recompensa.piedras} piedras espirituales")
    nombres = {"h": "hierbas", "n": "núcleos", "p": "polvo de jade"}
    for clave, cantidad in (
        ("h", recompensa.hierbas),
        ("n", recompensa.nucleos),
        ("p", recompensa.polvo),
    ):
        if cantidad:
            partida.materiales[clave] = (
                partida.materiales.get(clave, 0) + cantidad
            )
            partes.append(f"{cantidad} {nombres[clave]}")
    if recompensa.talisman_escape:
        partida.pildoras["tes"] = partida.pildoras.get("tes", 0) + 1
        partes.append("Talismán de Escape")
    if recompensa.cartas is not None:
        candidatos = [
            ident
            for ident in cartas_de_rareza(recompensa.cartas)
            if not CARTAS[ident].reliquia
        ]
        if candidatos:
            elegida = candidatos[
                math.floor(aleatorio() * len(candidatos))
            ]
            resultado = agregar_carta_coleccion(
                partida.coleccion,
                partida.materiales,
                elegida,
                partida.misiones,
            )
            partes.append(resultado.nombre)
    return ", ".join(partes) if partes else None


def es_jefe_final_mazmorra(indice: int) -> bool:
    """¿Es el tercer jefe de una mazmorra? (`k >= 48 && (k-48)%3==2`).

    Args:
        indice: índice global en `ENEMIGOS`.

    Returns:
        True si es jefe final de mazmorra.
    """
    return (
        indice >= OFFSET_MAZMORRAS
        and (indice - OFFSET_MAZMORRAS) % 3 == 2
    )


def muerte_permanente(
    partida: Partida, enemigo: EnemigoCatalogo | None
) -> dict[str, Any]:
    """Reinicio por muerte (`permaDeath` de js/06-contenido.js:85).

    Args:
        partida: partida a mutar (reset total salvo gacha).
        enemigo: quien mató al héroe.

    Returns:
        Resumen para la UI (``by``/``w``/``r``).
    """
    partida.muertes += 1
    partida.mejor_racha = max(partida.mejor_racha, partida.nivel_reino)
    resumen = {
        "by": enemigo.nombre_enemigo if enemigo else "",
        "w": len([k for k in partida.victorias if k < 48]),
        "r": partida.nivel_reino,
    }
    partida.piedras_espirituales = 30
    partida.mazos = []
    partida.mazo_activo = -1
    partida.nivel_reino = 0
    partida.vida_hroe = None
    partida.victorias = []
    partida.coleccion = {}
    partida.secta = "esp"
    partida.secta_elegida_confirmada = None
    partida.materiales = {"h": 0, "n": 0, "p": 0}
    partida.pildoras = {}
    partida.atuendo = {}
    partida.bestia_equipada = None
    partida.equipo_guardado = {}
    partida.equipado = {}
    partida.usos_equipo = {}
    from app.engine.state import nuevas_misiones

    partida.misiones = nuevas_misiones()
    partida.misiones_reclamadas = {}
    return resumen


def mazo_para_combate(
    partida: Partida, aleatorio: Callable[[], float]
) -> list[str]:
    """Mazo del jugador para el combate (`actDeck` o automático).

    Args:
        partida: partida con mazos/colección/secta.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Lista de 40 ids (activa si es válida, si no automática).
    """
    mazo = None
    if 0 <= partida.mazo_activo < len(partida.mazos):
        mazo = partida.mazos[partida.mazo_activo]
    plano = mazo_activo_plano(mazo, partida.secta, partida.coleccion)
    if plano:
        return list(plano)
    return construir_mazo(
        partida.secta,
        con_coleccion=True,
        coleccion=partida.coleccion,
        aleatorio=aleatorio,
    )


def mazo_enemigo(
    enemigo: EnemigoCatalogo, aleatorio: Callable[[], float]
) -> list[str]:
    """Mazo del enemigo (`deck(ch.s, 0, ch.li + ch.d)`).

    Args:
        enemigo: ficha aplanada.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Lista de 40 ids de la secta del enemigo.
    """
    return construir_mazo(
        enemigo.secta if enemigo.secta in SECTAS else "esp",
        extras=(enemigo.indice_nivel or 0) + (enemigo.dificultad or 0),
        aleatorio=aleatorio,
    )


def aplicar_victoria(
    partida: Partida,
    enemigo: EnemigoCatalogo,
    indice: int | None,
    vida_combate: int | None,
    aleatorio: Callable[[], float],
) -> dict[str, Any]:
    """Efectos de campaña al vencer (`chk` rama `E.hp <= 0`).

    Args:
        partida: partida a mutar.
        enemigo: ficha del enemigo vencido.
        indice: índice en `ENEMIGOS` (None = genérico).
        vida_combate: vida final del héroe.
        aleatorio: callback float en ``[0, 1)``.

    Returns:
        Resumen: ``primera``, ``recompensas``, ``materiales``,
        ``reliquia``, ``mision_secundaria``, ``ascenso``,
        ``vida_max_reseteada``, ``receta``.
    """
    primera = indice is not None and indice not in partida.victorias
    reino0 = partida.nivel_reino
    victorias0 = len(partida.victorias)
    if primera and indice is not None:
        partida.victorias.append(indice)
        if (
            enemigo.dificultad == 5
            and not enemigo.indice_mazmorra
            and partida.nivel_reino < REINO_MAX_ASCENSO
        ):
            ascender_reino(partida)
    mantener_vida(partida, vida_combate)
    vida_max_reseteada = False
    if (enemigo.dificultad == 5 and not enemigo.indice_mazmorra) or (
        indice is not None and es_jefe_final_mazmorra(indice)
    ):
        partida.vida_hroe = None
        vida_max_reseteada = True
    receta = None
    if enemigo.receta and not partida.recetas.get(enemigo.receta):
        partida.recetas[enemigo.receta] = 1
        receta = enemigo.receta
    recompensas = generar_rareza_recompensa(
        aleatorio, enemigo.rareza_recompensa
    )
    contadores_victoria(partida, enemigo)
    materiales = materiales_victoria(
        enemigo, aleatorio, primera=primera
    )
    partida.materiales["h"] = (
        partida.materiales.get("h", 0) + materiales["h"]
    )
    partida.materiales["p"] = (
        partida.materiales.get("p", 0) + materiales["p"]
    )
    partida.materiales["n"] = (
        partida.materiales.get("n", 0) + materiales["n"]
    )
    partida.piedras_espirituales += materiales["s"]
    partida.misiones["ge"] = partida.misiones.get("ge", 0) + materiales["s"]
    tes = None
    if enemigo.dificultad >= 4:
        partida.pildoras["tes"] = partida.pildoras.get("tes", 0) + 1
        tes = 1
    reliquia = gotear_reliquia(partida, enemigo, aleatorio)
    mision_texto = None
    if primera and enemigo.indice_mision and enemigo.fase_mision == 2:
        mision_texto = otorgar_mision_secundaria(
            partida, enemigo, aleatorio
        )
    return {
        "primera": primera,
        "indice": indice,
        "reino0": reino0,
        "victorias0": victorias0,
        "recompensas": recompensas,
        "materiales": {**materiales, **({"tes": tes} if tes else {})},
        "reliquia": reliquia,
        "mision_secundaria": mision_texto,
        "ascenso": partida.nivel_reino > reino0,
        "vida_max_reseteada": vida_max_reseteada,
        "receta": receta,
    }
