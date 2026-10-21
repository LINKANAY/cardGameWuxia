"""Jardín Medicinal — datos y estado por defecto (contenido nuevo).

No existe en el monolito: es el módulo nuevo acordado para la pestaña
«Jardín». El estilo sigue el de `app.data.hierbas`: constantes de
balance en `CFG`, catálogos congelados con dataclass y constructores
de estado con sanitizado tolerante a saves viejos o corruptos.

Qué contiene:

- `CFG`: duraciones por rareza (2–45 min), rendimiento de la cosecha,
  descuento de las formaciones de crecimiento, umbral de «listo»,
  reino mínimo por rareza, botín de boticario y semillas iniciales.
- `FORMACIONES`: 6 formaciones de crecimiento (objeto nuevo, con
  rareza propia) equipables en la ranura del jardín.
- `MEJORAS`: escalera de la cuadrícula 4 → 6 → 9 → 12 casillas con su
  coste en materiales (`h/n/p`) y su reino mínimo.
- `nuevo_jardin`/`desde_jardin`: estado bajo la clave `jdn` de
  `Partida` (clave backend, igual que `xn` del horno). Las semillas
  viven en `sd` y las formaciones de crecimiento en `fg`.

Las plantas son las 11 hierbas del Horno (`app.data.hierbas`): al
cosechar entran en `Partida.horno["hierbas"]`, listas para refinar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.data.hierbas import HIERBA, HIERBAS

#: Claves nuevas de `Partida.a_dict` (sólo backend, como `xn`).
CLAVE_JARDIN: str = "jdn"
CLAVE_SEMILLAS: str = "sd"
CLAVE_FORMACIONES: str = "fg"

#: Números de balance (decisión de diseño; no hay líneas del JS).
CFG: dict[str, Any] = {
    # --- Crecimiento: duración total por rareza de la hierba (ms) ---
    "DURACION_POR_RAREZA": {
        0: 2 * 60_000,  # 2 min
        1: 6 * 60_000,  # 6 min
        2: 12 * 60_000,  # 12 min
        3: 25 * 60_000,  # 25 min
        4: 45 * 60_000,  # 45 min
    },
    # --- Hierbas que rinde una cosecha según la rareza ---
    "RENDIMIENTO_POR_RAREZA": {0: 1, 1: 1, 2: 2, 3: 2, 4: 3},
    # --- La formación de crecimiento descuenta esto del total ---
    "DESCUENTO_POR_RAREZA": {0: 0.05, 1: 0.10, 2: 0.15, 3: 0.20, 4: 0.30},
    # --- Cada piedra espiritual quita 5 % del tiempo restante ---
    "REDUCCION_PIEDRA": 0.05,
    # --- Si el resto baja de aquí, la planta queda lista ---
    "UMBRAL_LISTO_MS": 1000,
    # --- Reino mínimo para sembrar cada rareza ---
    "REINO_POR_RAREZA": {0: 0, 1: 1, 2: 3, 3: 5, 4: 7},
    # --- Semillas con las que nace una partida nueva ---
    "SEMILLAS_INICIALES": {"hs": 2},
    # --- Casillas de la cuadrícula de partida nueva (nivel 0) ---
    "CASILLAS_BASE": 4,
    # --- Botín de un boticario vencido ---
    "BOTIN_SEMILLAS_MIN": 1,
    "BOTIN_SEMILLAS_MAX": 2,
    "BOTIN_PROB_SEGUNDA": 0.35,
    "BOTIN_INCREM_POR_DIF": 0.05,
    "BOTIN_PROB_FORMACION": 0.30,
    # Mismas claves/valores que BOTIN_RAREZA_POR_DIF del horno (0.25):
    # a mayor dificultad pesan más las cosas raras.
    "PESO_RAREZA_POR_DIF": 0.25,
    "FORMACIONES_PESO": {0: 40, 1: 25, 2: 12, 3: 5, 4: 2},
    "BOTIN_MAT_H_BASE": 2,
    "BOTIN_MAT_H_DIF": 1,
    "BOTIN_MAT_P_BASE": 1,
    "BOTIN_MAT_N_DIF": 3,
    # --- Regalo al subir de reino: formación de rareza reino // 3 ---
    "REGALO_FORMACION_DIVISOR": 3,
}


@dataclass(frozen=True, slots=True)
class FormacionData:
    """Formación de crecimiento (objeto nuevo del jardín).

    Atributos:
        identificador: id corto (`fc1`…`fc6`).
        nombre: nombre visible.
        glifo: carácter chino del icono.
        rareza: 0–4; manda el descuento de `DESCUENTO_POR_RAREZA`.
        descripcion: texto que se muestra en la ranura.
    """

    identificador: str
    nombre: str
    glifo: str
    rareza: int
    descripcion: str


#: Catálogo de formaciones de crecimiento (orden literal).
FORMACIONES: tuple[FormacionData, ...] = (
    FormacionData(
        "fc1", "Círculo de Rocío", "露", 0,
        "El rocío eterno moja las raíces mientras duermen.",
    ),
    FormacionData(
        "fc2", "Tierra Fértil", "壤", 0,
        "La tierra recuerda cada cosecha que ya alimentó.",
    ),
    FormacionData(
        "fc3", "Sello de Raíces", "根", 1,
        "Las raíces beben del tiempo detenido.",
    ),
    FormacionData(
        "fc4", "Rueda de las Cuatro Estaciones", "四", 2,
        "Primavera, verano, otoño e invierno giran en un solo día.",
    ),
    FormacionData(
        "fc5", "Sello del Jardín Celeste", "园", 3,
        "Un jardín flotante donde nada se marchita.",
    ),
    FormacionData(
        "fc6", "Dao de la Cosecha Eterna", "收", 4,
        "La cosecha eterna: todo brota a la vez.",
    ),
)

#: Índice por id.
FORMACION: dict[str, FormacionData] = {
    formacion.identificador: formacion for formacion in FORMACIONES
}


@dataclass(frozen=True, slots=True)
class MejoraData:
    """Nivel de la cuadrícula (`MEJORAS[nivel]`).

    Atributos:
        nivel: índice 0 (base) en adelante.
        casillas: nº de casillas que tiene ese nivel.
        coste: materiales de la mejora (`h/n/p`); vacío en el nivel 0.
        reino_min: nivel de reino exigido para comprarla.
    """

    nivel: int
    casillas: int
    coste: dict[str, int]
    reino_min: int


#: Escalera 4 → 6 → 9 → 12 casillas.
MEJORAS: tuple[MejoraData, ...] = (
    MejoraData(0, 4, {}, 0),
    MejoraData(1, 6, {"h": 15, "n": 5, "p": 5}, 2),
    MejoraData(2, 9, {"h": 30, "n": 15, "p": 15}, 5),
    MejoraData(3, 12, {"h": 60, "n": 30, "p": 30}, 8),
)


def _entero_js(valor: Any) -> int:
    """Trunca hacia cero como el operador `| 0` del JS (0 si no es número)."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def duracion_base(identificador: str) -> int:
    """Duración total (ms) de la planta sin formación, por su rareza.

    Args:
        identificador: id de hierba (`HIERBA`).

    Returns:
        Milisegundos de crecimiento.

    Raises:
        KeyError: el id no está en el catálogo de hierbas.
    """
    return CFG["DURACION_POR_RAREZA"][HIERBA[identificador].rareza]


def rendimiento_base(identificador: str) -> int:
    """Hierbas que rinde una cosecha de esa especie (`1 + rareza // 2`).

    Args:
        identificador: id de hierba (`HIERBA`).

    Returns:
        Nº de hierbas del Horno que suma la cosecha.

    Raises:
        KeyError: el id no está en el catálogo de hierbas.
    """
    return CFG["RENDIMIENTO_POR_RAREZA"][HIERBA[identificador].rareza]


def reino_minimo(identificador: str) -> int:
    """Nivel de reino exigido para sembrar esa especie.

    Args:
        identificador: id de hierba (`HIERBA`).

    Returns:
        Índice de reino mínimo (0 = se puede sembrar desde el inicio).

    Raises:
        KeyError: el id no está en el catálogo de hierbas.
    """
    return CFG["REINO_POR_RAREZA"][HIERBA[identificador].rareza]


def descuento_formacion(identificador: str | None) -> float:
    """Descuento de crecimiento que aplica una formación equipada.

    Args:
        identificador: id de `FORMACION`, o None si no hay ninguna.

    Returns:
        Fracción 0–0.3; desconocida o ausente → 0.0.
    """
    if not identificador:
        return 0.0
    formacion = FORMACION.get(identificador)
    if formacion is None:
        return 0.0
    return CFG["DESCUENTO_POR_RAREZA"][formacion.rareza]


# --- Estado del jardín (clave `jdn`) ---------------------------------------


def nuevo_jardin() -> dict:
    """Estado del jardín de partida nueva (nivel 0, 4 casillas vacías).

    Returns:
        ``{"nivel": 0, "casillas": [None × 4], "formacion": None}``.
        Cada llamada devuelve listas nuevas.
    """
    return {
        "nivel": 0,
        "casillas": [None] * CFG["CASILLAS_BASE"],
        "formacion": None,
    }


def _desde_casilla(valor: Any) -> dict | None:
    """Normaliza una casilla guardada (`None` si es irrecuperable).

    Una casilla sembrada es ``{"planta", "siembra", "reducido"}``:
    `siembra` es epoch ms del momento de siembra y `reducido` los ms ya
    descontados por piedras espirituales (ambos ≥ 0).
    """
    if not isinstance(valor, dict):
        return None
    planta = valor.get("planta")
    if planta not in HIERBA:
        return None
    siembra = valor.get("siembra")
    if not isinstance(siembra, (int, float)) or siembra < 0:
        return None
    reducido = valor.get("reducido", 0)
    if not isinstance(reducido, (int, float)) or reducido < 0:
        reducido = 0
    return {
        "planta": planta,
        "siembra": int(siembra),
        "reducido": int(reducido),
    }


def desde_jardin(guardado: Any) -> dict:
    """Reconstruye el jardín guardado bajo `jdn` (tolerante a basura).

    - No dict → `nuevo_jardin()`.
    - `nivel` recortado a ``len(MEJORAS) - 1``.
    - `casillas` recortado/alargado al tamaño del nivel; ids de planta
      desconocidos o `siembra` inválida → casilla vacía.
    - `formacion` desconocida → None.

    Args:
        guardado: valor leído de la clave `jdn`.

    Returns:
        Estado normalizado listo para `Partida.jardin`.
    """
    if not isinstance(guardado, dict):
        return nuevo_jardin()
    nivel = guardado.get("nivel", 0)
    if not isinstance(nivel, (int, float)) or nivel < 0:
        nivel = 0
    nivel = min(int(nivel), len(MEJORAS) - 1)
    total = MEJORAS[nivel].casillas
    crudas = guardado.get("casillas")
    if not isinstance(crudas, list):
        crudas = []
    casillas = [_desde_casilla(c) for c in crudas[:total]]
    casillas.extend([None] * (total - len(casillas)))
    formacion = guardado.get("formacion")
    if formacion not in FORMACION:
        formacion = None
    return {"nivel": nivel, "casillas": casillas, "formacion": formacion}


def desde_semillas(guardado: Any) -> dict:
    """Reconstruye el inventario de semillas (clave `sd`).

    - No dict (o clave ausente en un save viejo) → semillas iniciales.
    - De un dict sólo se conservan ids de `HIERBA` con cantidad > 0
      (mismo criterio que `desde_horno` con las hierbas).

    Args:
        guardado: valor leído de la clave `sd`.

    Returns:
        Dict id de hierba → nº de semillas.
    """
    if not isinstance(guardado, dict):
        return dict(CFG["SEMILLAS_INICIALES"])
    semillas: dict[str, int] = {}
    for identificador, cantidad in guardado.items():
        numero = _entero_js(cantidad)
        if identificador in HIERBA and numero > 0:
            semillas[identificador] = numero
    return semillas


def desde_formaciones(guardado: Any) -> dict:
    """Reconstruye el inventario de formaciones (clave `fg`).

    Args:
        guardado: valor leído de la clave `fg` (no dict → vacío).

    Returns:
        Dict id de `FORMACION` → nº de copias.
    """
    if not isinstance(guardado, dict):
        return {}
    formaciones: dict[str, int] = {}
    for identificador, cantidad in guardado.items():
        numero = _entero_js(cantidad)
        if identificador in FORMACION and numero > 0:
            formaciones[identificador] = numero
    return formaciones


def semillas_de_especie() -> dict[int, list[str]]:
    """Ids de hierba agrupados por rareza (para regalos y sorteos).

    Returns:
        Rareza → lista de ids de `HIERBAS` de esa rareza.
    """
    agrupadas: dict[int, list[str]] = {}
    for hierba in HIERBAS:
        agrupadas.setdefault(hierba.rareza, []).append(hierba.identificador)
    return agrupadas
