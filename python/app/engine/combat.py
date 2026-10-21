"""Motor de combate puro — paridad con `js/02-motor.js` (+ deps).

No hay estado global: todo vive en `EstadoCombate`. Las funciones
aceptan el estado y, si necesitan azar, un objeto con `.random()` y
`.barajar()` (típicamente `GeneradorAleatorio`).

Los efectos de campaña (recompensas, muerte permanente, ascenso de
reino) **no** se aplican aquí: `chk()` emite eventos y el servicio de
campaña (`CombatService`) los aplica sobre `Partida`.

Referencias de líneas del monolito se citan como ``js/02-motor.js:N``.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from app.data.cartas import CARTAS, rareza_de
from app.data.equipo import FILAS_EQUIPO_ENEMIGO, PIEZAS
from app.data.narrativa import redondear_js
from app.data.niveles import ENEMIGOS
from app.data.pildoras import PILDORAS
from app.data.tipos import (
    EnemigoCatalogo,
    HabilidadActiva,
    TipoCarta,
    TipoEfecto,
    UltimoAliento,
)
from app.data.trajes import traje
from app.engine import rules
from app.engine.rng import GeneradorAleatorio
from app.engine.state import CartaJuego, crear_carta_juego

# --- Constantes del motor ----------------------------------------------------

#: Tamaño de mano (`HM` de js/02-motor.js:12).
TAMANO_MANO: int = 5
#: Tope físico temporal de mano con efectos (`HX` de js/02-motor.js:16).
TOPE_MANO_FISICA: int = 8
#: Sobrecuración del héroe durante combate = vida máx. × 1.5 (`OVH`).
TOBRECURACION: float = 1.5
#: Máx. copias por pila (`MAXSK` de js/01-datos.js:301).
MAX_COPIAS_PILA: int = 3
#: Claves de efecto que dan +1 al llegar a MAXSK (`SKU` = `'rqe'`).
CLAVES_SKU: str = "rqe"
#: Escalado de vida/daño enemigo (`HP_PER_REALM`, `SCL` de js/06-contenido.js:224-227).
VIDA_BASE_HROE: int = 30
VIDA_POR_REINO: int = 2
ESCALA_ATAQUE_REINO: float = 0.03
ESCALA_ATAQUE_PISO: float = 0.02

#: Probabilidad de evento de mapa al empezar turnos ≥ 2 (`Math.random() < .35`).
PROBABILIDAD_EVENTO: float = 0.35


# --- Lado y estado -----------------------------------------------------------


@dataclass
class PiezaFormacion:
    """Formación activa de un lado (`s.fm` del JS).

    Atributos:
        identificador: id de la carta F (`fm.id`).
        nombre: nombre visible (`fm.n`).
        ataque_fisico: bonus de ataque cuerpo a cuerpo (`fm.pa`).
        vida_fisica: bonus de vida al entrar y al chocar (`fm.ph`).
        efecto_inicio_turno: (`fm.ts`; `(clave_efecto, valor)`).
    """

    identificador: str
    nombre: str
    ataque_fisico: int = 0
    vida_fisica: int = 0
    efecto_inicio_turno: tuple[TipoEfecto, int] | None = None


@dataclass
class PiezaRuna:
    """Runa activa de un lado (`s.rn[i]` del JS).

    Atributos:
        identificador: id de la carta R.
        nombre: nombre visible.
        efecto_inicio_turno: (`ts`; `(clave, valor)`).
        duracion_restante: turnos restantes (`du`; default 3).
    """

    identificador: str
    nombre: str
    efecto_inicio_turno: tuple[TipoEfecto, int] | None = None
    duracion_restante: int = 3


@dataclass
class Lado:
    """Estado de un combatiente (`side()` de js/02-motor.js:11).

    Los buffs dinámicos (`pen`/`atkb`/…) se aplican sólo al lado que
    los tenga; el JS los pone en el objeto del lado (jugador o enemigo).
    """

    nombre: str
    hp: int
    mx: int
    qi: int = 0
    mq: int = 0
    cap: int = 5
    sh: int = 0
    dk: list[CartaJuego] = field(default_factory=list)
    hand: list[CartaJuego] = field(default_factory=list)
    vd: list[CartaJuego] = field(default_factory=list)
    bd: list[CartaJuego] = field(default_factory=list)
    sw: int = 0
    bo: int = 0
    #: Marca de si este lado es el jugador (sobrecuración, VP, qc).
    es_jugador: bool = False
    #: Contador de turnos del enemigo (`E.t`).
    turnos_enemigo: int = 0
    #: Número de turno del jugador (`P.n`).
    numero_turno: int = 0
    fm: PiezaFormacion | None = None
    rn: list[PiezaRuna] = field(default_factory=list)
    fat: int = 0
    # --- buffs dinámicos ---
    pen: int = 0
    atkb: int = 0
    opa: int = 0
    oph: int = 0
    osh: int = 0
    oq: int = 0
    regen: int = 0
    qb: int = 0
    xd: int = 0
    ofd: int = 0
    ofx: str | None = None
    # --- píldoras / supervivencia (sólo jugador en la práctica) ---
    pildoras_inicio: list[str] = field(default_factory=list)
    bolsa_pildoras: list[str] = field(default_factory=list)
    pildoras_usadas: int = 0
    revivir: int = 0
    artefacto: str | None = None
    esc: int = 0
    descartes: int = 0
    # --- marcas de criatura al entrar en combate ---
    bestia: CartaJuego | None = None
    # --- equipo visible en el log (`E.gear`/`E.gb` de enemyGear) ---
    gear: list[str] = field(default_factory=list)
    gear_texto: str = ""


@dataclass
class EventoCombate:
    """Evento emitido por el motor para el servicio de campaña/UI.

    Atributos:
        tipo: clave corta del evento.
        datos: payload según tipo.
    """

    tipo: str
    datos: dict = field(default_factory=dict)


@dataclass
class OpcionEventoMapa:
    """Opción de un evento de mapa (`EV[i].o[j]` de js/06-contenido.js:213).

    Atributos:
        etiqueta: texto del botón (`o[0]`).
        efecto: aplica la opción y devuelve el mensaje de log (`o[1]()`).
    """

    etiqueta: str
    efecto: Callable[[EstadoCombate], str]


@dataclass
class EventoMapa:
    """Evento aleatorio de mapa a partir del turno 2 (`ev` del monolito).

    Atributos:
        nombre: título del evento (`ev.n`).
        texto: descripción (`ev.t`).
        opciones: pares etiqueta+efecto (`ev.o`).
    """

    nombre: str
    texto: str
    opciones: list[OpcionEventoMapa]


@dataclass
class EstadoCombate:
    """Todo el estado de un combate en curso.

    Sustituye a las variables de módulo `P`/`E`/`ch`/`over`/`lock`/…
    del monolito.
    """

    P: Lado
    E: Lado
    enemigo: EnemigoCatalogo | None = None
    #: Índice en `ENEMIGOS` (para `wins` de campaña), o None si es genérico.
    indice_enemigo: int | None = None
    #: Multiplicador de daño enemigo (`EA`).
    mult_ataque_enemigo: float = 1.0
    #: Multiplicador de vida enemiga (`EHm`).
    mult_vida_enemiga: float = 1.0
    #: Fin de combate: `''` | `'w'` | `'l'` | `'f'` (`over`).
    fin: str = ""
    lock: bool = False
    logs: list[str] = field(default_factory=list)
    #: Pila de descartes del mulligan (`PD`).
    pd: list[CartaJuego] = field(default_factory=list)
    #: Nº de cartas que aún hay que recuperar del Agujero Negro (`VP.n`).
    vp_n: int = 0
    #: Nº de descartes por exceso de mano (`ED`).
    ed: int = 0
    #: Confirmación de fin de turno con acciones pendientes (`EC`).
    ec: bool = False
    #: Índice de selección en UI (`sel`).
    sel: int = -1
    #: Índice de objetivo de criatura (`tg`).
    tg: int | None = None
    #: Evento de mapa activo (`ev`), si lo hay.
    ev: EventoMapa | None = None
    #: Contador de logs (`LC`).
    lc: int = 0
    #: Eventos pendientes de consumir por el servicio/campaña.
    eventos: list[EventoCombate] = field(default_factory=list)
    #: Contadores de misiones del jugador (`qs` de `qc`); sólo se emiten.
    rng: GeneradorAleatorio | None = None

    def azar(self) -> float:
        """Siguiente float de azar (`Math.random` / `RNG.random`)."""
        if self.rng is None:
            raise RuntimeError("EstadoCombate.sin RNG inyectado")
        return self.rng.random()

    def entero(self, limite: int) -> int:
        """Entero en ``[0, limite)`` como `Math.floor(Math.random()*n)`."""
        if limite <= 0:
            raise ValueError("entero(limite) requiere limite > 0")
        return math.floor(self.azar() * limite)

    def barajar(self, lista: Sequence[CartaJuego]) -> list[CartaJuego]:
        """Copia barajada (`rnd(a)` = `RNG.shuffle`)."""
        if self.rng is None:
            raise RuntimeError("EstadoCombate.sin RNG inyectado")
        return self.rng.barajar(lista)

    def log(self, mensaje: str) -> None:
        """Añade al registro (`log()` de js/02-motor.js:20)."""
        self.lc += 1
        self.logs.append(mensaje)
        if len(self.logs) > 40:
            self.logs.pop(0)

    def emitir(self, nombre: str, **datos) -> None:
        """Registra un evento para el servicio de campaña."""
        self.eventos.append(EventoCombate(tipo=nombre, datos=datos))


# --- Utilidades de mano / vacío ----------------------------------------------


def a_vacio(lado: Lado, carta: CartaJuego) -> None:
    """Manda una carta al Agujero Negro (`toVoid`)."""
    lado.vd.append(carta)


def a_mano(lado: Lado, carta: CartaJuego) -> None:
    """Pone carta en mano, o al vacío si la mano está al tope físico (`toHand`)."""
    if len(lado.hand) < TOPE_MANO_FISICA:
        lado.hand.append(carta)
    else:
        a_vacio(lado, carta)


def robar(estado: EstadoCombate, lado: Lado, n: int = 1, *, lim: bool = False) -> None:
    """Roba cartas del mazo (`draw` de js/02-motor.js:17).

    Args:
        estado: estado del combate (para logs y azar).
        lado: quién roba.
        n: nº de cartas.
        lim: si True, respeta el tope de mano `HM` (robo de inicio de
            turno); si False, usa el tope físico `HX`.
    """
    cap = TAMANO_MANO if lim else TOPE_MANO_FISICA
    while n > 0 and lado.dk and len(lado.hand) < cap:
        lado.hand.append(lado.dk.pop())
        n -= 1
    if n > 0 and not lado.dk and len(lado.hand) < cap:
        lado.fat = (lado.fat or 0) + 1
        herir(estado, lado, lado.fat)
        estado.log(
            f"{lado.nombre} sufre {lado.fat} de daño por fatiga (mazo agotado)."
        )
    if lim and n > 0 and lado.dk and len(lado.hand) >= TAMANO_MANO:
        estado.log(
            f"{lado.nombre} tiene la mano llena "
            f"({TAMANO_MANO}/{TAMANO_MANO}): no roba al inicio del turno."
        )


def descartar_enemigo_exceso(estado: EstadoCombate, lado: Lado) -> None:
    """Descarta de menor coste hasta el tope de mano (fin de turno enemigo)."""
    while len(lado.hand) > TAMANO_MANO:
        k = 0
        for j, carta in enumerate(lado.hand):
            if carta.coste_qi < lado.hand[k].coste_qi:
                k = j
        g = lado.hand.pop(k)
        a_vacio(lado, g)
        estado.log(
            f"{lado.nombre} descarta {g.nombre} al Agujero Negro "
            "(exceso de mano)."
        )


def descartar_aleatorio(estado: EstadoCombate, lado: Lado, n: int) -> None:
    """El rival descarta N cartas al azar (`voidDiscard` de js/07-campamento.js:71)."""
    k = 0
    while k < n and lado.hand:
        idx = estado.entero(len(lado.hand))
        c = lado.hand.pop(idx)
        a_vacio(lado, c)
        estado.log(f"{lado.nombre} descarta {c.nombre} al Agujero Negro")
        k += 1
    if not k:
        estado.log(f"{lado.nombre} no tiene cartas que descartar")


def ciclar_mano(estado: EstadoCombate, lado: Lado) -> None:
    """Descarta N cartas al azar y roba otras tantas (`cycleHand`)."""
    k = min(len(lado.hand), len(lado.dk))
    for _ in range(k):
        idx = estado.entero(len(lado.hand))
        c = lado.hand.pop(idx)
        a_vacio(lado, c)
    if k:
        estado.log(
            f"{lado.nombre} descarta {k} carta"
            f"{'s' if k > 1 else ''} al Agujero Negro y roba otras tantas"
        )
        robar(estado, lado, k)
    else:
        estado.log(f"{lado.nombre} no puede ciclar su mano")


def recuperar_vacio(
    estado: EstadoCombate,
    lado: Lado,
    carta: CartaJuego,
) -> None:
    """Efectos Abismo/Samsara al jugar la carta (`voidRecover`)."""
    definicion = carta.definicion
    if definicion.abismo_traer:
        n = min(
            definicion.abismo_traer,
            TOPE_MANO_FISICA - len(lado.hand),
            len(lado.vd),
        )
        if n <= 0:
            if lado.vd:
                estado.log(
                    f"{lado.nombre} no tiene espacio en la mano "
                    f"({TOPE_MANO_FISICA}/{TOPE_MANO_FISICA})"
                )
            else:
                estado.log(
                    f"El Agujero Negro de {lado.nombre} está vacío"
                )
        elif lado.es_jugador and definicion.abismo_elegir:
            # Elección manual: el servicio/UI la resuelve (VP).
            estado.vp_n = n
            estado.emitir("elegir_vacio", cantidad=n)
        else:
            for _ in range(n):
                idx = estado.entero(len(lado.vd))
                x = lado.vd.pop(idx)
                lado.hand.append(crear_carta_juego(x.identificador))
                estado.log(
                    f"{lado.nombre} recupera {x.nombre} del Agujero Negro"
                )
    if definicion.samsara:
        k = 0
        while k < definicion.samsara and lado.vd:
            idx = estado.entero(len(lado.vd))
            x = lado.vd.pop(idx)
            lado.dk.append(crear_carta_juego(x.identificador))
            k += 1
        if k:
            lado.dk = estado.barajar(lado.dk)
            estado.log(
                f"{lado.nombre} baraja {k} carta"
                f"{'s' if k > 1 else ''} del Agujero Negro en su mazo"
            )
        else:
            estado.log(f"El Agujero Negro de {lado.nombre} está vacío")


# --- Daño / curación / efectos -----------------------------------------------


def herir(estado: EstadoCombate, lado: Lado, n: int) -> None:
    """Aplica daño a héroe (`hurt` de js/02-motor.js:21)."""
    absorbido = min(lado.sh, n)
    lado.sh -= absorbido
    lado.hp -= n - absorbido


def techo_vida(estado: EstadoCombate, lado: Lado) -> int:
    """Tope de vida durante combate (`hpCap`). Sólo el héroe se sobrecura."""
    if lado.es_jugador:
        return math.floor(lado.mx * TOBRECURACION)
    return lado.mx


def curar(estado: EstadoCombate, lado: Lado, n: int) -> None:
    """Cura sin superar el techo (`heal`)."""
    lado.hp = max(lado.hp, min(techo_vida(estado, lado), lado.hp + n))


def efecto(
    estado: EstadoCombate,
    fuente: Lado,
    objetivo: Lado,
    clave: TipoEfecto,
    valor: int,
) -> None:
    """Aplica un efecto simple (`fx` de js/02-motor.js:25)."""
    if clave == TipoEfecto.DANO_HROE:
        herir(estado, objetivo, valor)
    elif clave == TipoEfecto.CURAR:
        curar(estado, fuente, valor)
    elif clave == TipoEfecto.ROBAR:
        robar(estado, fuente, valor)
    elif clave == TipoEfecto.ESCUDO:
        fuente.sh += valor
    elif clave == TipoEfecto.DRENAR_QI:
        objetivo.pen = min(4, objetivo.pen + valor)
    elif clave == TipoEfecto.GANAR_QI:
        fuente.qi += valor
    elif clave == TipoEfecto.DANO_CRIATURA_AL_AZAR:
        if objetivo.bd:
            idx = estado.entero(len(objetivo.bd))
            objetivo.bd[idx].vida = (objetivo.bd[idx].vida or 0) - valor
        else:
            herir(estado, objetivo, valor)


def limpiar(estado: EstadoCombate) -> None:
    """Elimina criaturas muertas y dispara últimos alientos (`clean`)."""
    for lado, otro in ((estado.P, estado.E), (estado.E, estado.P)):
        muertas = [c for c in lado.bd if (c.vida or 0) <= 0]
        lado.bd = [c for c in lado.bd if (c.vida or 0) > 0]
        for c in muertas:
            if not c.es_bestia:
                a_vacio(lado, c)
                for _ in range(1, c.copias_apiladas):
                    a_vacio(lado, crear_carta_juego(c.identificador))
            aliento = c.ultimo_aliento
            if aliento:
                efecto(estado, lado, otro, aliento.tipo, aliento.valor)
                estado.log(f"{c.nombre}: último aliento")


# --- Apilado de criaturas ----------------------------------------------------


def efecto_pila(clave: str, valor: int, n: int) -> int:
    """Incremento al subir de pila (`skFx` de js/02-motor.js:2)."""
    if clave in CLAVES_SKU:
        return 1 if n >= MAX_COPIAS_PILA else 0
    return (n - 1) * math.ceil(valor / 2)


def objetivo_pila(lado: Lado, carta: CartaJuego) -> CartaJuego | None:
    """Busca pila aceptable para apilar (`stkT`)."""
    if (
        not lado
        or not carta
        or carta.tipo != TipoCarta.CRIATURA
        or carta.es_bestia
    ):
        return None
    r: CartaJuego | None = None
    for x in lado.bd:
        if (
            x.identificador == carta.identificador
            and not x.es_bestia
            and x.copias_apiladas < MAX_COPIAS_PILA
            and (r is None or x.copias_apiladas > r.copias_apiladas)
        ):
            r = x
    return r


def subir_pila(objetivo: CartaJuego) -> CartaJuego:
    """Aplica los bonus de pila (`stkUp` de js/02-motor.js:4-8)."""
    b = objetivo.definicion
    n = objetivo.copias_apiladas + 1
    objetivo.copias_apiladas = n
    objetivo.ataque = (objetivo.ataque or 0) + math.ceil((b.ataque or 0) / 2)
    objetivo.vida = (objetivo.vida or 0) + math.ceil((b.vida or 0) / 2)
    if b.ultimo_aliento:
        objetivo.aliento_apilado = UltimoAliento(
            b.ultimo_aliento.tipo,
            b.ultimo_aliento.valor
            + efecto_pila(b.ultimo_aliento.tipo.value, b.ultimo_aliento.valor, n),
        )
    if b.habilidad_activa:
        habilidad = b.habilidad_activa
        valor = habilidad.valor + efecto_pila(
            habilidad.tipo.value, habilidad.valor, n
        )
        descripcion = _reemplazar_primer_numero(habilidad.descripcion, valor)
        objetivo.habilidad_apilada = HabilidadActiva(
            coste_qi=habilidad.coste_qi,
            tipo=habilidad.tipo,
            valor=valor,
            descripcion=descripcion,
        )
    if b.crece:
        objetivo.crece_apilado = b.crece + (1 if n >= MAX_COPIAS_PILA else 0)
    return objetivo


def _reemplazar_primer_numero(texto: str, nuevo: int) -> str:
    """Sustituye el primer número del texto de habilidad (`replace(/\\d+/, v)`)."""
    partes: list[str] = []
    reemplazado = False
    i = 0
    while i < len(texto):
        if not reemplazado and texto[i].isdigit():
            j = i
            while j < len(texto) and texto[j].isdigit():
                j += 1
            partes.append(str(nuevo))
            reemplazado = True
            i = j
        else:
            partes.append(texto[i])
            i += 1
    return "".join(partes)


def apilar(
    estado: EstadoCombate,
    lado: Lado,
    objetivo: CartaJuego,
    carta: CartaJuego,
) -> CartaJuego:
    """Apila `carta` sobre `objetivo` y marca `fresh` (`stackOn`)."""
    subir_pila(objetivo)
    objetivo.recien_entrante = True
    estado.log(
        f"{lado.nombre} apila {carta.nombre} sobre {objetivo.nombre}: "
        f"pila ×{objetivo.copias_apiladas}, "
        f"Nv {objetivo.copias_apiladas}/{MAX_COPIAS_PILA} "
        f"({objetivo.ataque}/{objetivo.vida})"
    )
    return objetivo


# --- Formaciones y runas -----------------------------------------------------


def poner_formacion(estado: EstadoCombate, lado: Lado, carta: CartaJuego) -> None:
    """Coloca formación o runa (`fmPut` de js/04-mazos-formaciones.js:31)."""
    b = carta.definicion
    if carta.tipo == TipoCarta.FORMACION:
        if lado.fm:
            a_vacio(lado, crear_carta_juego(lado.fm.identificador))
        lado.fm = PiezaFormacion(
            identificador=carta.identificador,
            nombre=carta.nombre,
            ataque_fisico=b.mejora_ataque_al_trazar or 0,
            vida_fisica=b.mejora_vida_al_trazar or 0,
            efecto_inicio_turno=b.efecto_inicio_turno,
        )
        if b.mejora_vida_al_trazar:
            for x in lado.bd:
                x.vida = (x.vida or 0) + b.mejora_vida_al_trazar
        estado.log(f"{lado.nombre} traza la formación {carta.nombre}")
    else:
        if len(lado.rn) >= 2:
            vieja = lado.rn.pop(0)
            a_vacio(lado, crear_carta_juego(vieja.identificador))
        lado.rn.append(
            PiezaRuna(
                identificador=carta.identificador,
                nombre=carta.nombre,
                efecto_inicio_turno=b.efecto_inicio_turno,
                duracion_restante=b.duracion_turnos or 3,
            )
        )
        estado.log(f"{lado.nombre} graba la runa {carta.nombre}")


def turno_formaciones(estado: EstadoCombate, lado: Lado) -> None:
    """Activa formación/runas al empezar turno y expira runas (`fmTurn`)."""
    otro = estado.P if lado is estado.E else estado.E
    piezas: list[PiezaFormacion | PiezaRuna | None] = [lado.fm, *lado.rn]
    for pieza in piezas:
        if pieza is None or not pieza.efecto_inicio_turno:
            continue
        clave, valor = pieza.efecto_inicio_turno
        if clave == TipoEfecto.AUTO_DANO:
            herir(estado, lado, valor)
        else:
            efecto(estado, lado, otro, clave, valor)
        estado.log(f"{pieza.nombre} se activa")
    quedan: list[PiezaRuna] = []
    for r in lado.rn:
        r.duracion_restante -= 1
        if r.duracion_restante > 0:
            quedan.append(r)
        else:
            a_vacio(lado, crear_carta_juego(r.identificador))
    lado.rn = quedan
    limpiar(estado)


# --- Píldoras de combate -----------------------------------------------------


def carta_al_azar(estado: EstadoCombate, rareza_min: int) -> CartaJuego:
    """Carta aleatoria de rareza ≥ `rareza_min` (`rc(m)` de js/01-datos.js:193)."""
    candidatos = [
        ident
        for ident, carta in CARTAS.items()
        if rareza_de(carta) >= rareza_min
    ]
    elegida = candidatos[estado.entero(len(candidatos))]
    return crear_carta_juego(elegida)


def entregar_carta(estado: EstadoCombate, carta: CartaJuego) -> CartaJuego:
    """Pone una carta en mano o al vacío (`toHand` de js/02-motor.js:15)."""
    if len(estado.P.hand) < TAMANO_MANO:
        estado.P.hand.append(carta)
    else:
        a_vacio(estado.P, carta)
    return carta


def usar_pildoras_inicio(estado: EstadoCombate) -> None:
    """Consume las píldoras de inicio (`usePills` de js/01-datos.js:196)."""
    P = estado.P
    for clave in list(P.pildoras_inicio):
        info = PILDORAS.get(clave)
        nombre = info.nombre if info else clave
        if clave == "vit":
            P.mx += 8
            P.hp += 8
        elif clave == "dra":
            P.qi += 3
        elif clave == "cla":
            robar(estado, P, 2)
        elif clave == "esc":
            P.sh += 6
        elif clave == "reg":
            P.regen += 2
        elif clave == "dsp":
            P.cap += 1
            P.mq += 1
            P.qi += 1
        elif clave == "fur":
            herir(estado, estado.E, 4)
        elif clave == "ven":
            estado.E.hp -= 6
        elif clave == "qi2":
            P.qb = 1
            P.qi += 1
        elif clave == "dr2":
            P.xd = 1
            robar(estado, P, 1)
        elif clave == "tor":
            P.sh += 12
        elif clave == "rar":
            # `give(rc(3))` de js/01-datos.js:196 (Épica o mejor en mano).
            entregar_carta(estado, carta_al_azar(estado, 3))
        elif clave == "inm":
            P.revivir = 1
        elif clave == "tes":
            P.esc = 1
        estado.log(f"Usas {nombre}")
    P.pildoras_inicio = []


# --- Eventos de mapa (turno ≥ 2) ---------------------------------------------


def _ev_cueva_qi(estado: EstadoCombate) -> str:
    estado.P.qi += 3
    estado.P.hp -= 3
    return "Absorbes el Qi de la cueva."


def _ev_cultivador_salvar(estado: EstadoCombate) -> str:
    robar(estado, estado.P, 2)
    return "Te agradece con una técnica."


def _ev_pildora_tomar(estado: EstadoCombate) -> str:
    if estado.azar() < 0.5:
        robar(estado, estado.P, 2)
        return "Era un elixir de lucidez."
    estado.P.hp -= 4
    return "Era veneno."


def _ev_tesoro_robar(estado: EstadoCombate) -> str:
    estado.E.sh += 4
    carta = entregar_carta(estado, carta_al_azar(estado, 2))
    return f"Obtienes {carta.nombre}"


def _ev_formacion_entrar(estado: EstadoCombate) -> str:
    P = estado.P
    if P.bd:
        for c in P.bd:
            c.ataque = (c.ataque or 0) + 1
            c.vida = (c.vida or 0) + 1
        return "La formación fortalece a tus criaturas."
    P.hp -= 3
    return "La formación te drena."


def _ev_bestia_domar(estado: EstadoCombate) -> str:
    P = estado.P
    if estado.azar() < 0.5 and len(P.bd) < 5:
        c = crear_carta_juego("ti")
        c.lista_para_atacar = True
        P.bd.append(c)
        return "La bestia te sigue."
    P.hp -= 3
    return "La bestia te muerde."


def _ev_bestia_huir(estado: EstadoCombate) -> str:
    P = estado.P
    P.qi = max(0, P.qi - 1)
    return "Escapas con el aliento corto."


def _ev_tribulacion_resistir(estado: EstadoCombate) -> str:
    P = estado.P
    P.hp -= 4
    P.cap += 1
    P.mq += 1
    return "El rayo templa tu cuerpo."


def _ev_tribulacion_evadir(estado: EstadoCombate) -> str:
    P = estado.P
    if P.hand:
        a_vacio(P, P.hand.pop(estado.entero(len(P.hand))))
    return (
        "Pierdes una carta al esquivar (cae al Agujero Negro)."
    )


def _ev_herencia_absorber(estado: EstadoCombate) -> str:
    estado.P.hp -= 5
    carta = entregar_carta(estado, carta_al_azar(estado, 3))
    return f"Heredas {carta.nombre}"


def _ev_herencia_sellar(estado: EstadoCombate) -> str:
    estado.P.sh += 5
    return "El sello te protege."


#: Eventos aleatorios de mapa (`EV` de js/06-contenido.js:213).
EVENTOS_MAPA: tuple[EventoMapa, ...] = (
    EventoMapa(
        "Cueva ancestral",
        "Una cueva sellada late con Qi antiguo.",
        [
            OpcionEventoMapa(
                "Entrar: +3 Qi, pierdes 3 de vida", _ev_cueva_qi
            ),
            OpcionEventoMapa("Ignorarla", lambda e: "Sigues tu camino."),
        ],
    ),
    EventoMapa(
        "Cultivador herido",
        "Un cultivador agoniza al borde del campo.",
        [
            OpcionEventoMapa("Salvarlo: robas 2 cartas", _ev_cultivador_salvar),
            OpcionEventoMapa(
                "Ignorarlo", lambda e: "Su mirada te persigue."
            ),
        ],
    ),
    EventoMapa(
        "Píldora misteriosa",
        "Una píldora sin etiqueta rueda a tus pies.",
        [
            OpcionEventoMapa(
                "Tomarla: 50% robas 2 cartas, 50% pierdes 4 de vida",
                _ev_pildora_tomar,
            ),
            OpcionEventoMapa(
                "Descartarla", lambda e: "Mejor no arriesgar."
            ),
        ],
    ),
    EventoMapa(
        "Tesoro abandonado",
        "Un cofre sin dueño brilla entre las ruinas.",
        [
            OpcionEventoMapa(
                "Robarlo: carta Rara o mejor, el enemigo gana 4 de escudo",
                _ev_tesoro_robar,
            ),
            OpcionEventoMapa("Dejarlo", lambda e: "No era tuyo."),
        ],
    ),
    EventoMapa(
        "Formación desconocida",
        "Un círculo de runas se enciende bajo tus pies.",
        [
            OpcionEventoMapa(
                "Entrar: tus criaturas ganan +1/+1, sin criaturas pierdes 3 de vida",
                _ev_formacion_entrar,
            ),
            OpcionEventoMapa("Evitarla", lambda e: "Rodeas las runas."),
        ],
    ),
    EventoMapa(
        "Bestia espiritual",
        "Una bestia salvaje te observa entre la niebla.",
        [
            OpcionEventoMapa(
                "Domarla: 50% criatura 3/3, si falla pierdes 3 de vida",
                _ev_bestia_domar,
            ),
            OpcionEventoMapa(
                "Huir: pierdes 1 Qi", _ev_bestia_huir
            ),
        ],
    ),
    EventoMapa(
        "Tribulación menor",
        "Un rayo solitario cae del cielo.",
        [
            OpcionEventoMapa(
                "Resistir: 4 de daño y Qi máximo +1 en este combate",
                _ev_tribulacion_resistir,
            ),
            OpcionEventoMapa("Evadir: descartas una carta", _ev_tribulacion_evadir),
        ],
    ),
    EventoMapa(
        "Herencia antigua",
        "Un ermitaño muerto deja un legado.",
        [
            OpcionEventoMapa(
                "Absorber: carta Épica o mejor, pierdes 5 de vida",
                _ev_herencia_absorber,
            ),
            OpcionEventoMapa("Sellarla: +5 de escudo", _ev_herencia_sellar),
        ],
    ),
)


def elegir_evento_mapa(estado: EstadoCombate) -> EventoMapa:
    """Elige un evento al azar (`EV[Math.random()*EV.length|0]`)."""
    return EVENTOS_MAPA[estado.entero(len(EVENTOS_MAPA))]


def resolver_evento_mapa(estado: EstadoCombate, opcion: int) -> bool:
    """Aplica la opción elegida (`evPick` de js/07-campamento.js:108).

    Args:
        estado: estado del combate con `ev` activo.
        opcion: índice de la opción elegida.

    Returns:
        True si la opción se aplicó.
    """
    ev = estado.ev
    if ev is None or opcion < 0 or opcion >= len(ev.opciones):
        return False
    estado.ev = None
    mensaje = ev.opciones[opcion].efecto(estado)
    estado.log(f"{ev.nombre}: {mensaje}")
    P = estado.P
    techo = techo_vida(estado, P)
    if P.hp > techo:
        P.hp = techo
    estado.lock = comprobar_fin(estado)
    return True


# --- Píldora de bolsa en combate ---------------------------------------------


def puede_usar_pildora(estado: EstadoCombate, ident: str) -> bool:
    """Guards de `usePill` (js/06-contenido.js:166)."""
    P = estado.P
    if estado.lock or estado.fin:
        return False
    if P.pildoras_usadas >= 2:
        return False
    return ident in P.bolsa_pildoras


def aplicar_pildora_bolsa(
    estado: EstadoCombate, ident: str, stock_restante: int
) -> None:
    """Efecto de píldora de bolsa (`battlePill` de js/06-contenido.js:165).

    Args:
        estado: estado del combate.
        ident: clave de la píldora.
        stock_restante: unidades que quedan en el inventario tras el uso
            (para retirarla de la bolsa al agotarse, como el JS).
    """
    P = estado.P
    info = PILDORAS.get(ident)
    nombre = info.nombre if info else ident
    P.pildoras_usadas += 1
    if ident == "cur":
        curar(estado, P, 10)
    elif ident == "qiR":
        P.qi += 4
    elif ident == "rob":
        robar(estado, P, 3)
    elif ident == "fue":
        herir(estado, estado.E, 6)
    elif ident == "pet":
        P.sh += 10
    elif ident == "cng":
        for c in estado.E.bd:
            c.congelada = True
    elif ident == "pur":
        P.pen = 0
        for c in P.bd:
            c.congelada = False
        curar(estado, P, 3)
    elif ident == "fur2":
        for c in P.bd:
            c.ataque = (c.ataque or 0) + 2
    elif ident == "hea2":
        for c in P.bd:
            c.vida = (c.vida or 0) + 5
    elif ident == "vnn":
        for c in estado.E.bd:
            c.vida = (c.vida or 0) - 4
        limpiar(estado)
    estado.log(f"Usas {nombre} ({P.pildoras_usadas}/2)")
    if stock_restante <= 0:
        P.bolsa_pildoras = [
            x for x in P.bolsa_pildoras if x != ident
        ]
    if comprobar_fin(estado):
        estado.lock = True


# --- Jugar carta / atacar ----------------------------------------------------


def puede_jugar(estado: EstadoCombate, lado: Lado, carta: CartaJuego) -> bool:
    """¿Se puede jugar esta carta? (pre-chequeos de `play`)."""
    del estado
    if carta is None or carta.coste_qi > lado.qi:
        return False
    return not (
        carta.tipo == TipoCarta.CRIATURA
        and len(lado.bd) >= 5
        and not objetivo_pila(lado, carta)
    )


def cartas_jugables(estado: EstadoCombate) -> list[CartaJuego]:
    """Mano jugable del jugador (`playableCards` de js/10-jugabilidad-musica.js:5)."""
    return [c for c in estado.P.hand if puede_jugar(estado, estado.P, c)]


def criaturas_activables(estado: EstadoCombate) -> list[CartaJuego]:
    """Criaturas con habilidad usable (`activableCreatures`)."""
    return [
        c
        for c in estado.P.bd
        if c.habilidad_activa
        and not c.usada
        and estado.P.qi >= c.habilidad_activa.coste_qi
    ]


def todavia_puede_actuar(estado: EstadoCombate) -> bool:
    """`canStillAct` de js/10-jugabilidad-musica.js:10."""
    return bool(cartas_jugables(estado) or criaturas_activables(estado))


def jugar_carta(
    estado: EstadoCombate,
    lado: Lado,
    rival: Lado,
    indice: int,
    objetivo: int | None = None,
) -> bool:
    """Juega la carta de mano `indice` (`play` de js/02-motor.js:29-43).

    Returns:
        True si la carta se jugó.
    """
    if indice < 0 or indice >= len(lado.hand):
        return False
    c = lado.hand[indice]
    if not puede_jugar(estado, lado, c):
        return False
    b = c.definicion

    lado.qi -= c.coste_qi
    lado.hand.pop(indice)
    estado.log(f"{lado.nombre} juega {c.nombre}")
    if lado.es_jugador:
        estado.emitir(
            "qc",
            carta=c.identificador,
            tipo_carta=b.tipo.value,
            dano=b.dano_hroe,
            dano_criatura=b.dano_criatura,
            congelar=b.congelar,
            area=bool(b.dano_area or b.tribulacion),
            eq=b.drenar_qi_rival,
            curar=b.curar,
            escudo=b.escudo,
            sacrificar=b.sacrificar_vida,
            espada=b.es_espada and b.tipo != TipoCarta.CRIATURA,
        )

    if b.sacrificar_vida:
        lado.hp -= b.sacrificar_vida
    if b.ganar_qi:
        lado.qi += b.ganar_qi
    if b.curar:
        if b.curar_porcentaje:
            curar(
                estado,
                lado,
                max(
                    b.curar,
                    redondear_js(lado.mx * b.curar_porcentaje / 100),
                ),
            )
        else:
            curar(estado, lado, b.curar)
    if b.escudo:
        lado.sh += b.escudo
    if b.renovar:
        # Devuelve TODA la mano al mazo y baraja (`rf`).
        bk = lado.hand[:]
        lado.hand.clear()
        lado.dk = estado.barajar([*lado.dk, *bk])
        estado.log(
            f"{lado.nombre} devuelve {len(bk)} cartas y renueva su mano"
        )
        robar(estado, lado, b.renovar)
    if b.robar:
        robar(estado, lado, b.robar)
    if b.drenar_qi_rival:
        rival.pen = min(4, rival.pen + b.drenar_qi_rival)

    if b.tipo == TipoCarta.CRIATURA:
        pila = objetivo_pila(lado, c)
        if pila:
            apilar(estado, lado, pila, c)
        else:
            if lado.atkb:
                c.ataque = (c.ataque or 0) + math.ceil(lado.atkb / 2)
            lado.bd.append(c)
            bonus = (lado.fm.vida_fisica if lado.fm else 0) + lado.oph
            c.vida = (c.vida or 0) + bonus
            if b.impetu:
                c.lista_para_atacar = True
        if b.al_entrar:
            efecto(estado, lado, rival, b.al_entrar.tipo, b.al_entrar.valor)
    elif b.tipo in (TipoCarta.FORMACION, TipoCarta.RUNA):
        poner_formacion(estado, lado, c)
    else:
        if b.disipa and (rival.fm or rival.rn):
            if rival.fm:
                a_vacio(rival, crear_carta_juego(rival.fm.identificador))
            for r in rival.rn:
                a_vacio(rival, crear_carta_juego(r.identificador))
            rival.fm = None
            rival.rn = []
            estado.log(
                f"{c.nombre} disipa las formaciones y runas de {rival.nombre}"
            )
        # `(c.d && s.atkb) || 0` del JS: bonus de ataque sólo si hay daño base.
        dano = (b.dano_hroe or 0) + ((b.dano_hroe and lado.atkb) or 0)
        xb = 0
        if b.es_espada:
            if lado.bo and (b.dano_hroe or b.dano_criatura):
                xb = 3
                lado.bo = 0
                estado.log("¡Intención de Espada!")
            lado.sw += 1
            if lado.sw % 3 == 0:
                lado.bo = 1
        if b.dano_hroe:
            dano += xb
        mult = (
            estado.mult_ataque_enemigo if lado is estado.E else 1.0
        )
        if dano:
            herir(estado, rival, redondear_js(dano * mult))
        if b.dano_area:
            ao = redondear_js(b.dano_area * mult)
            for x in rival.bd:
                x.vida = (x.vida or 0) - ao
        if b.dano_criatura:
            daño_criatura = (
                (b.dano_criatura or 0)
                + (lado.atkb or 0)
                + (0 if b.dano_hroe else xb)
            )
            if objetivo is not None and objetivo < len(rival.bd):
                bl = rival.bd[objetivo]
                bl.vida = (bl.vida or 0) - redondear_js(daño_criatura * mult)
                if b.congelar:
                    bl.congelada = True
                estado.log(f"{c.nombre} impacta a {bl.nombre}")
            else:
                herir(estado, rival, redondear_js(daño_criatura * mult))
        if b.mejorar_aliada:
            if objetivo is not None and objetivo < len(lado.bd):
                a = lado.bd[objetivo]
                a.ataque = (a.ataque or 0) + b.mejorar_aliada.ataque
                a.vida = (a.vida or 0) + b.mejorar_aliada.vida
                estado.log(f"{a.nombre} se fortalece")
            else:
                lado.sh += 3
        if b.tribulacion:
            herir(estado, rival, 3)
            herir(estado, lado, 3)
            for x in (*rival.bd, *lado.bd):
                x.vida = (x.vida or 0) - 4
        if b.vacio_descarte:
            descartar_aleatorio(estado, rival, b.vacio_descarte)
        if b.ciclo:
            ciclar_mano(estado, lado)
        if b.abismo_traer or b.samsara:
            recuperar_vacio(estado, lado, c)
        a_vacio(lado, c)

    limpiar(estado)
    # `fin()` de js/07-campamento.js:110: `if (chk()) lock = true`.
    if comprobar_fin(estado):
        estado.lock = True
    return True


def atacar(
    estado: EstadoCombate,
    lado: Lado,
    rival: Lado,
    atacante: CartaJuego,
    objetivo: int,
) -> None:
    """Criatura ataca (`hit` de js/02-motor.js:44).

    Args:
        objetivo: índice en `rival.bd`, o negativo para héroe.
    """
    atacante.lista_para_atacar = False
    bonus_fisico = (lado.fm.ataque_fisico if lado.fm else 0) + lado.opa
    mult = estado.mult_ataque_enemigo if lado is estado.E else 1.0
    daño = redondear_js(((atacante.ataque or 0) + bonus_fisico) * mult)
    if objetivo < 0:
        herir(estado, rival, daño)
        estado.log(f"{atacante.nombre} golpea a {rival.nombre}")
    else:
        if objetivo >= len(rival.bd):
            return
        b = rival.bd[objetivo]
        b.vida = (b.vida or 0) - daño
        bono_def = (rival.fm.ataque_fisico if rival.fm else 0) + rival.opa
        atacante.vida = (atacante.vida or 0) - ((b.ataque or 0) + bono_def)
        estado.log(f"{atacante.nombre} choca con {b.nombre}")
    if atacante.definicion.robar_vida:
        curar(estado, lado, daño)
    if atacante.crece:
        atacante.ataque = (atacante.ataque or 0) + atacante.crece
    limpiar(estado)
    # `go()` de js/07-campamento.js:118: `if (chk()) lock = true`.
    if comprobar_fin(estado):
        estado.lock = True


def activar_habilidad(
    estado: EstadoCombate,
    lado: Lado,
    rival: Lado,
    indice: int,
) -> bool:
    """Activa la habilidad de la criatura en tablero `indice` (`act`)."""
    if estado.lock or estado.fin:
        return False
    if indice < 0 or indice >= len(lado.bd):
        return False
    c = lado.bd[indice]
    habilidad = c.habilidad_activa
    if not habilidad or c.usada or lado.qi < habilidad.coste_qi:
        return False
    lado.qi -= habilidad.coste_qi
    c.usada = True
    efecto(estado, lado, rival, habilidad.tipo, habilidad.valor)
    estado.log(f"{c.nombre} usa {habilidad.descripcion}")
    limpiar(estado)
    # `act()` de js/02-motor.js:27: `if (chk()) lock = true`.
    if comprobar_fin(estado):
        estado.lock = True
    return True


# --- Inicio de turno ---------------------------------------------------------


def iniciar_lado(
    estado: EstadoCombate,
    lado: Lado,
    *,
    nombre: str,
    vida: int,
    capacidad: int,
    ids_mazo: Sequence[str],
) -> Lado:
    """Construye un lado (`side()` de js/02-motor.js:11)."""
    del nombre  # ya está en el lado; se acepta por claridad de API
    lado.mx = vida
    lado.hp = vida
    lado.cap = capacidad
    lado.dk = [crear_carta_juego(i) for i in ids_mazo]
    return lado


def empezar_turno(estado: EstadoCombate, lado: Lado) -> None:
    """Prepara el turno de `lado` (`start` de js/02-motor.js:28)."""
    otro = estado.P if lado is estado.E else estado.E
    lado.mq = min(lado.cap, lado.mq + 1)
    lado.qi = max(0, lado.mq - lado.pen)
    lado.pen = 0
    robar(estado, lado, 1, lim=True)
    for c in lado.bd:
        c.lista_para_atacar = not c.congelada
        c.congelada = False
        c.usada = False
    lado.sh = 0
    if lado.osh:
        lado.sh += lado.osh
    turno_formaciones(estado, lado)
    del otro


def turno_jugador(estado: EstadoCombate) -> None:
    """Empieza el turno del jugador (`turnP` de js/02-motor.js:58)."""
    P = estado.P
    empezar_turno(estado, P)
    if P.pen:
        P.qi = max(0, P.qi - P.pen)
        P.pen = 0
    P.numero_turno = (P.numero_turno or 0) + 1
    if P.numero_turno == 1:
        usar_pildoras_inicio(estado)
        if P.oq:
            P.qi += P.oq
    else:
        if P.regen:
            P.sh += P.regen
        if P.qb:
            P.qi += P.qb
        if P.xd:
            robar(estado, P, P.xd, lim=True)
    estado.lock = False
    if P.numero_turno > 1 and estado.azar() < PROBABILIDAD_EVENTO:
        # Evento de mapa: bloquea hasta que la UI elija opción (`evPick`).
        estado.ev = elegir_evento_mapa(estado)
        estado.log(f"Evento: {estado.ev.nombre}")
        estado.lock = True
    if comprobar_fin(estado):
        estado.lock = True


# --- Fin de combate ----------------------------------------------------------


def comprobar_fin(estado: EstadoCombate) -> bool:
    """Detecta fin de combate (`chk` de js/02-motor.js:45-52).

    Emite eventos de campaña; no muta `Partida`.
    """
    if estado.E.hp <= 0:
        if estado.fin != "w":
            indice = estado.indice_enemigo
            enemigo = estado.enemigo
            estado.emitir(
                "victoria",
                indice=indice,
                dificultad=enemigo.dificultad if enemigo else 0,
                nivel=enemigo.indice_nivel if enemigo else 0,
                es_mazmorra=bool(enemigo and enemigo.indice_mazmorra),
                es_mision=bool(enemigo and enemigo.indice_mision),
                fase_mision=enemigo.fase_mision if enemigo else None,
                receta=enemigo.receta if enemigo else None,
                tribulacion=False,
                vida_enemigo_max=estado.E.mx,
            )
            estado.fin = "w"
        return True
    if estado.P.hp <= 0:
        if estado.P.revivir:
            estado.P.revivir = 0
            estado.P.hp = 15
            estado.log("¡La Píldora de Inmortalidad te devuelve a la vida!")
            estado.emitir("revivir", vida=15)
            return False
        if estado.P.artefacto:
            # La duración/rotura la aplica el servicio sobre la partida.
            objetivo = PIEZAS.get(estado.P.artefacto)
            vida_revive = objetivo.revive if objetivo and objetivo.revive else 1
            estado.emitir("salvar_artefacto", artefacto=estado.P.artefacto)
            estado.P.hp = vida_revive
            if objetivo:
                estado.log(
                    f"¡{objetivo.nombre} te devuelve a la vida con "
                    f"{vida_revive} de vida!"
                )
            estado.P.artefacto = None
            return False
        if estado.P.esc:
            estado.P.esc = 0
            estado.fin = "f"
            estado.log("El Talismán de Escape te saca del combate.")
            estado.emitir("escape")
            return True
        if estado.fin != "l":
            estado.fin = "l"
            estado.emitir("muerte", enemigo=estado.E.nombre)
        return True
    return False


# --- Armado del combate ------------------------------------------------------


def multiplicadores_enemigo(
    enemigo: EnemigoCatalogo,
    reino: int,
) -> tuple[float, float]:
    """`(EA, EHm)` de un enemigo (`enemyMul` de js/06-contenido.js:228).

    Args:
        enemigo: ficha aplanada.
        reino: reino actual del jugador.

    Returns:
        Tupla (multiplicador de ataque, multiplicador de vida).
    """
    piso = enemigo.indice_nivel or 0
    vida_base = enemigo.vida or 1
    eh = (vida_base + VIDA_POR_REINO * reino) / vida_base
    ea = (1 + ESCALA_ATAQUE_REINO * reino) * (
        1 + ESCALA_ATAQUE_PISO * piso
    )
    return ea, eh


def vida_heroe_max(reino: int) -> int:
    """Vida máxima del héroe (`pMaxHp` de js/06-contenido.js:225)."""
    return VIDA_BASE_HROE + VIDA_POR_REINO * reino


def qi_capacidad(reino: int) -> int:
    """Capacidad de Qi (`qiCap` de js/06-contenido.js:224)."""
    return min(12, 6 + reino)


def _mejora_equipo_enemigo(
    estado: EstadoCombate,
    enemigo: EnemigoCatalogo,
) -> None:
    """`enemyGear()` de js/02-motor.js:54 con el catálogo `GEAR`.

    El score decide cuántas filas aportan (`n`), la columna de pieza
    (`t = score // 16`, hasta 2) y el tope de bono (`cp`); los
    nombres quedan en ``E.gear`` para el log de inicio.
    """
    sc = (enemigo.indice_nivel or 0) * 6 + (enemigo.dificultad or 0)
    filas_score = (
        0 if sc < 6 else 1 if sc < 18 else 2 if sc < 30 else 3 if sc < 42 else 4
    )
    columna = min(2, sc // 16)
    cp = 1 if sc < 30 else 2
    bonus_dificultad = (
        1 if enemigo.dificultad == 5 and filas_score < 4 else 0
    )
    filas = FILAS_EQUIPO_ENEMIGO[
        : min(4, filas_score + bonus_dificultad)
    ]
    ataque = 0
    qi = 0
    nombres: list[str] = []
    for fila in filas:
        pieza = PIEZAS[fila[columna]]
        ataque += pieza.ataque
        qi += pieza.qi
        nombres.append(pieza.nombre)
    estado.E.atkb = min(cp, ataque)
    qb = min(cp, qi)
    estado.E.cap += qb
    estado.E.mq += qb
    estado.E.gear = nombres
    partes = []
    if estado.E.atkb:
        partes.append(f"Ataque +{estado.E.atkb}")
    if qb:
        partes.append(f"Qi +{qb}")
    estado.E.gear_texto = ", ".join(partes)


def _bestia_enemiga(
    estado: EstadoCombate,
    enemigo: EnemigoCatalogo,
    reino: int,
) -> None:
    """`enemyBeast` de js/07-campamento.js:103."""
    from app.data.bestias import bestia_para_enemigo

    bestia, nivel = bestia_para_enemigo(
        enemigo.indice_nivel or 0,
        enemigo.dificultad or 0,
    )
    c = crear_carta_juego(bestia.identificador)
    c.es_bestia = True
    c.vida = (c.vida or 0) + nivel // 3 + reino // 2
    c.ataque = (c.ataque or 0) + nivel // 4
    if estado.E.atkb:
        c.ataque = (c.ataque or 0) + math.ceil(estado.E.atkb / 2)
    c.lista_para_atacar = True
    estado.E.bd.append(c)
    estado.E.bestia = c
    estado.log(
        f"{estado.E.nombre} lleva a su bestia espiritual: "
        f"<b>{c.nombre}</b> (nivel {nivel}, {c.ataque}/{c.vida})."
    )


def aplicar_equipo_jugador(
    P: Lado,
    equipado: dict,
    equipo_guardado: dict,
    usos_equipo: dict,
) -> None:
    """Bonos del equipo del jugador (`applyGear()` de js/06-contenido.js:67).

    Suma Ataque y Qi (tope +4 vía `gearStat`) y arma el artefacto si
    está equipado, poseído y con usos restantes (`P.art`).
    """
    bonos = rules.gear_stat(equipado, equipo_guardado)
    P.atkb = bonos["a"]
    P.cap += bonos["q"]
    P.mq += bonos["q"]
    artefacto = equipado.get("artefacto")
    if (
        artefacto
        and equipo_guardado.get(artefacto)
        and usos_equipo.get(artefacto, 0) > 0
    ):
        P.artefacto = artefacto


def aplicar_atuendo(P: Lado, secta: str, atuendo: dict) -> None:
    """Efecto del traje vestido (`applyOutfit()` de js/05-arte.js:173).

    Sin traje de la secta en el armario se usa el índice 0, igual que
    ``outfit[sect] || 0`` del monolito; un índice inexistente no hace
    nada.
    """
    objetivo = traje(secta, atuendo.get(secta) or 0)
    if objetivo is None:
        return
    tipo, valor = objetivo.tipo, objetivo.valor
    if tipo == "hp":
        P.mx += valor
        P.hp += valor
    elif tipo == "sh":
        P.osh = valor
    elif tipo == "q":
        P.oq = valor
    elif tipo == "rg":
        P.regen += valor
    elif tipo == "at":
        P.atkb += valor
    elif tipo == "pa":
        P.opa = valor
    elif tipo == "ph":
        P.oph = valor
    elif tipo == "fd":
        P.ofd = valor
    P.ofx = (
        f'Traje «{objetivo.nombre}»: {objetivo.efecto} '
        f"({objetivo.descripcion})"
    )


def _bestia_domada(
    carta: CartaJuego, victorias: Sequence[int]
) -> bool:
    """¿La bestia equipada está domada? (`BEAST.findIndex` + `wins.includes`)."""
    from app.data.bestias import BESTIAS_DOMADAS

    for bestia in BESTIAS_DOMADAS:
        if bestia.identificador == carta.identificador:
            return rules.bestia_desbloqueada(bestia, list(victorias))
    return False


def iniciar_combate(
    *,
    enemigo: EnemigoCatalogo,
    indice_enemigo: int | None,
    reino: int,
    vida_hroe: int | None,
    mazo_jugador: Sequence[str],
    mazo_enemigo: Sequence[str],
    nombre_jugador: str = "Tú",
    pildoras_inicio: Sequence[str] = (),
    bolsa: Sequence[str] = (),
    rng: GeneradorAleatorio | None = None,
    equipar_bestia_jugador: CartaJuego | None = None,
    equipado: dict | None = None,
    equipo_guardado: dict | None = None,
    usos_equipo: dict | None = None,
    atuendo: dict | None = None,
    secta: str = "esp",
    victorias: Sequence[int] = (),
) -> EstadoCombate:
    """Arma un combate (`begin` de js/02-motor.js:57, sin campaña).

    Args:
        enemigo: ficha del oponente.
        indice_enemigo: índice en `ENEMIGOS` (para victoria).
        reino: reino del jugador (escala de enemigo y vida).
        vida_hroe: vida actual entre combates, o None = vida máx.
        mazo_jugador: 40 ids del mazo activo (o automático).
        mazo_enemigo: ids del mazo del enemigo.
        nombre_jugador: nombre del lado jugador.
        pildoras_inicio: píldoras ya elegidas (`P.pills`).
        bolsa: píldoras de combate de la bolsa (`P.pouch` de `eqpB`).
        rng: generador inyectado.
        equipar_bestia_jugador: bestia equipada ya instanciada.
        equipado: huecos con pieza (`eq`); sus bonos entran en combate.
        equipo_guardado: piezas forjadas (`gr`); condiciona los bonos.
        usos_equipo: usos del artefacto (`du`); activa el revive.
        atuendo: secta → traje vestido (`of`).
        secta: secta del jugador (elige el traje a aplicar).
        victorias: índices de victorias (`wins`); desbloquea la bestia.

    Returns:
        Estado listo para el primer `turno_jugador` (que ya se llama
        aquí, igual que `begin` llama a `turnoP`).
    """
    ea, eh = multiplicadores_enemigo(enemigo, reino)
    vida_max = vida_heroe_max(reino)
    P = Lado(
        nombre=nombre_jugador,
        hp=vida_max,
        mx=vida_max,
        cap=qi_capacidad(reino),
        es_jugador=True,
    )
    P.dk = [crear_carta_juego(i) for i in mazo_jugador]
    if vida_hroe is None:
        P.hp = P.mx
    else:
        P.hp = max(1, min(vida_hroe, P.mx))
    P.pildoras_inicio = list(pildoras_inicio)
    P.bolsa_pildoras = list(bolsa)
    # `applyGear(); applyOutfit();` justo antes de crear al rival.
    aplicar_equipo_jugador(
        P, equipado or {}, equipo_guardado or {}, usos_equipo or {}
    )
    aplicar_atuendo(P, secta, atuendo or {})
    vida_enemigo = redondear_js(enemigo.vida * eh)
    E = Lado(
        nombre=enemigo.nombre_enemigo,
        hp=vida_enemigo,
        mx=vida_enemigo,
        cap=enemigo.capacidad,
    )
    E.dk = [crear_carta_juego(i) for i in mazo_enemigo]

    estado = EstadoCombate(
        P=P,
        E=E,
        enemigo=enemigo,
        indice_enemigo=indice_enemigo,
        mult_ataque_enemigo=ea,
        mult_vida_enemiga=eh,
        rng=rng,
    )
    _mejora_equipo_enemigo(estado, enemigo)
    _bestia_enemiga(estado, enemigo, reino)
    if equipar_bestia_jugador is not None and _bestia_domada(
        equipar_bestia_jugador, victorias
    ):
        if equipar_bestia_jugador.ataque and P.atkb:
            equipar_bestia_jugador.ataque = (
                equipar_bestia_jugador.ataque
                + math.ceil(P.atkb / 2)
            )
        equipar_bestia_jugador.lista_para_atacar = True
        P.bd.append(equipar_bestia_jugador)
    if P.ofd:
        E.hp = max(1, E.hp - P.ofd)
    robar(estado, P, 4)
    robar(estado, E, 4)
    estado.log(f"<b>{E.nombre}:</b> «{enemigo.frase_inicio}»")
    if E.gear:
        extra = f" ({E.gear_texto})" if E.gear_texto else ""
        estado.log(f"{E.nombre} viste {', '.join(E.gear)}{extra}.")
    if P.ofx:
        estado.log(P.ofx)
    turno_jugador(estado)
    return estado


def indice_enemigo_por_catalogo(enemigo: EnemigoCatalogo) -> int:
    """Índice de `enemigo` en `ENEMIGOS` (`CH.indexOf`)."""
    return ENEMIGOS.index(enemigo)


# --- Turno del jugador: fin y exceso de mano ---------------------------------


def puede_cerrar_turno(estado: EstadoCombate) -> bool:
    """¿El jugador puede pasar ya al turno enemigo? (`endT` pre-check)."""
    if estado.lock or estado.fin or estado.pd or estado.vp_n or estado.ed:
        return False
    return not estado.ec


def confirmar_cierre(estado: EstadoCombate, *, forzar: bool = False) -> str:
    """Valida el cierre de turno del jugador (`endT` guards).

    Returns:
        ``'ok'`` | ``'bloqueado'`` | ``'todavia_actua'`` | ``'exceso_mano'``.
    """
    if estado.lock or estado.fin or estado.pd or estado.vp_n or estado.ed:
        return "bloqueado"
    if estado.ec and not forzar:
        return "bloqueado"
    if not forzar and todavia_puede_actuar(estado):
        estado.ec = True
        return "todavia_actua"
    if len(estado.P.hand) > TAMANO_MANO:
        estado.ed = len(estado.P.hand) - TAMANO_MANO
        return "exceso_mano"
    return "ok"


def descartar_exceso_jugador(estado: EstadoCombate, indice: int) -> bool:
    """Descarta una carta del exceso de mano del jugador (`edisc`).

    Cuando `ed` llega a 0, el servicio continúa el turno con
    `fin_turno_enemigo(estado, forzar=True)` (como `edisc` de
    js/07-campamento.js:84).
    """
    if not estado.ed or indice < 0 or indice >= len(estado.P.hand):
        return False
    c = estado.P.hand.pop(indice)
    a_vacio(estado.P, c)
    estado.log(f"Descartas {c.nombre} al Agujero Negro (exceso de mano).")
    estado.ed -= 1
    return True


def cancelar_exceso(estado: EstadoCombate) -> bool:
    """Cancela el modal de exceso y sigue jugando (`ED = 0` de `edHTML`).

    El monolito limpia `ED` en el cliente sin más efectos; aquí hay que
    borrarlo del estado del servidor para no bloquear el turno.

    Returns:
        True si había un exceso pendiente.
    """
    if not estado.ed:
        return False
    estado.ed = 0
    return True


def recuperar_del_vacio(estado: EstadoCombate, indice: int) -> bool:
    """Elige una carta del Agujero Negro durante `VP` (`vpick`)."""
    if not estado.vp_n or indice < 0 or indice >= len(estado.P.vd):
        return False
    x = estado.P.vd.pop(indice)
    estado.P.hand.append(crear_carta_juego(x.identificador))
    estado.log(f"Recuperas {x.nombre} del Agujero Negro")
    estado.vp_n -= 1
    if (
        estado.vp_n <= 0
        or len(estado.P.hand) >= TOPE_MANO_FISICA
        or not estado.P.vd
    ):
        estado.vp_n = 0
    return True


def cancelar_vacio(estado: EstadoCombate) -> None:
    """Cancela la elección del Agujero Negro (`vdone`)."""
    estado.vp_n = 0


# --- Turno enemigo (IA) ------------------------------------------------------


@dataclass
class AccionEnemiga:
    """Paso de la IA enemigo para que la UI lo reproduzca con ritmo.

    Atributos:
        tipo: ``'pasiva'`` | ``'juega'`` | ``'habilidad'`` | ``'ataca'``
            | ``'descarta'`` | ``'fin'``.
        carta: id de la carta implicada, si aplica.
        nombre: nombre visible.
        objetivo_nombre: nombre del objetivo (ataque/td).
        habla: tipo de burbuja del monolito (`say`): ``'a'|'s'|'d'|'c'|'t'``.
        datos: payload extra.
    """

    tipo: str
    carta: str | None = None
    nombre: str | None = None
    objetivo_nombre: str | None = None
    habla: str | None = None
    datos: dict = field(default_factory=dict)


def _elegir_jugada_enemiga(
    estado: EstadoCombate,
) -> tuple[CartaJuego, int] | None:
    """Siguiente jugada de la mano enemiga (`endT` bucle `for (;;)`).

    Filtro y prioridad idénticos al JS: coste ≤ Qi, sin bloqueos
    contextuales, y se juega la de mayor coste (`sort` por `c` desc).
    """
    P, E = estado.P, estado.E
    candidatos: list[tuple[CartaJuego, int]] = []
    for indice, c in enumerate(E.hand):
        b = c.definicion
        if c.coste_qi > E.qi:
            continue
        if (
            b.tipo == TipoCarta.CRIATURA
            and len(E.bd) >= 5
            and not objetivo_pila(E, c)
        ):
            continue
        if b.sacrificar_vida and E.hp <= b.sacrificar_vida + 4:
            continue
        if (
            b.curar
            and E.hp > E.mx - 3
            and not b.ganar_qi
        ):
            continue
        if b.mejorar_aliada and not E.bd:
            continue
        if b.tipo in (TipoCarta.FORMACION, TipoCarta.RUNA):
            if E.fm and E.fm.identificador == c.identificador:
                continue
            if any(r.identificador == c.identificador for r in E.rn):
                continue
        if b.disipa and not P.fm and not P.rn:
            continue
        if b.renovar and len(E.hand) < 4:
            continue
        if b.vacio_descarte and not P.hand:
            continue
        if b.ciclo and len(E.hand) < 3:
            continue
        if (b.abismo_traer or b.samsara) and not E.vd:
            continue
        candidatos.append((c, indice))
    if not candidatos:
        return None
    candidatos.sort(key=lambda par: -par[0].coste_qi)
    return candidatos[0]


def _objetivo_jugada_enemiga(
    estado: EstadoCombate,
    carta: CartaJuego,
) -> tuple[int | None, str | None]:
    """Elige `tg` de la jugada enemiga (criatura rival con más ataque)."""
    b = carta.definicion
    P = estado.P
    objetivo: int | None = None
    nombre_objetivo: str | None = None
    if b.dano_criatura and P.bd:
        objetivo = max(range(len(P.bd)), key=lambda j: P.bd[j].ataque or 0)
        nombre_objetivo = P.bd[objetivo].nombre
    if b.mejorar_aliada and estado.E.bd:
        objetivo = max(
            range(len(estado.E.bd)), key=lambda j: estado.E.bd[j].ataque or 0
        )
    return objetivo, nombre_objetivo


def _habla_enemiga(carta: CartaJuego, nombre_objetivo: str | None) -> str:
    """Clase de burbuja `say` del monolito para la jugada."""
    b = carta.definicion
    if nombre_objetivo:
        return "t"
    if b.tipo == TipoCarta.CRIATURA:
        return "s"
    if (
        b.dano_hroe
        or b.dano_area
        or b.tribulacion
        or b.drenar_qi_rival
        or b.dano_criatura
    ):
        return "a"
    return "d"


def _pasivas_enemigo(estado: EstadoCombate) -> list[AccionEnemiga]:
    """Aplica las pasivas del enemigo al empezar su turno (`endT` rl)."""
    P, E = estado.P, estado.E
    enemigo = estado.enemigo
    acciones: list[AccionEnemiga] = []
    if enemigo is None:
        return acciones
    habilidades = set(enemigo.habilidades)
    t = E.turnos_enemigo
    if "heal" in habilidades:
        cura = redondear_js(2 * estado.mult_vida_enemiga)
        E.hp = min(E.mx, E.hp + cura)
        acciones.append(
            AccionEnemiga(tipo="pasiva", nombre="heal", datos={"cura": cura})
        )
    if "regen" in habilidades:
        E.sh = 4
        acciones.append(AccionEnemiga(tipo="pasiva", nombre="regen"))
    if "drain" in habilidades and t % 3 == 0:
        P.mq = max(1, P.mq - 1)
        estado.log("Maldición: tu Qi máximo baja.")
        acciones.append(AccionEnemiga(tipo="pasiva", nombre="drain"))
    if "seal" in habilidades and t % 3 == 0:
        P.pen = 2
        estado.log("Sello: pierdes 2 Qi el próximo turno.")
        acciones.append(AccionEnemiga(tipo="pasiva", nombre="seal"))
    if "mist" in habilidades and t % 3 == 0 and P.hand:
        idx = estado.entero(len(P.hand))
        a_vacio(P, P.hand.pop(idx))
        estado.log("Un fantasma devora una carta de tu mano.")
        acciones.append(AccionEnemiga(tipo="pasiva", nombre="mist"))
    if "blade" in habilidades and t % 2 == 0:
        dano = redondear_js(3 * estado.mult_ataque_enemigo)
        herir(estado, P, dano)
        estado.log(f"Intención de espada enemiga: {dano} de daño.")
        acciones.append(
            AccionEnemiga(tipo="pasiva", nombre="blade", datos={"dano": dano})
        )
    if "breath" in habilidades and t % 3 == 0:
        dano = redondear_js(5 * estado.mult_ataque_enemigo)
        cura = redondear_js(4 * estado.mult_vida_enemiga)
        herir(estado, P, dano)
        E.hp = min(E.mx, E.hp + cura)
        estado.log("Aliento Primordial.")
        acciones.append(
            AccionEnemiga(
                tipo="pasiva",
                nombre="breath",
                datos={"dano": dano, "cura": cura},
            )
        )
    return acciones


def _objetivo_ataque_enemigo(
    estado: EstadoCombate,
    atacante: CartaJuego,
) -> int:
    """Elige índice de ataque de criatura enemiga (`endT` bucle `hit`).

    Reglas del JS:
    1. Pool = criaturas con provocar si hay alguna.
    2. Trade favorable: H ≤ A atacante y A rival < H atacante.
    3. Limpieza: H ≤ A atacante (aunque muera el atacante).
    4. Si hay provocar, pool[0]; si no, 50% criatura al azar, si no héroe.
    """
    P = estado.P
    hay_provocar = any(b.definicion.provocar for b in P.bd)
    pool = [
        j
        for j in range(len(P.bd))
        if not hay_provocar or P.bd[j].definicion.provocar
    ]
    if not pool:
        return -1
    a = atacante.ataque or 0
    h = atacante.vida or 0
    k = next(
        (
            j
            for j in pool
            if (P.bd[j].vida or 0) <= a and (P.bd[j].ataque or 0) < h
        ),
        None,
    )
    if k is None:
        k = next(
            (
                j
                for j in pool
                if (P.bd[j].vida or 0) <= a and (P.bd[j].ataque or 0) >= a
            ),
            None,
        )
    if k is None:
        if hay_provocar:
            k = pool[0]
        elif P.bd and estado.azar() < 0.5:
            k = pool[estado.entero(len(pool))]
        else:
            k = -1
    return k


def fin_turno_enemigo(
    estado: EstadoCombate,
    *,
    forzar: bool = False,
) -> list[AccionEnemiga]:
    """Turno completo del enemigo (`endT` de js/02-motor.js:59-76).

    Ejecuta todo de forma síncrona (sin `await sl()`); la UI reproduce
    la lista de `AccionEnemiga` con el ritmo que quiera. Si el combate
    termina a mitad, devuelve las acciones parciales y deja `estado.fin`.

    Args:
        estado: estado del combate.
        forzar: ignora la confirmación `EC` (fin de turno forzado).

    Returns:
        Secuencia de acciones de la IA (para animación UI).
    """
    estado.ec = False
    if estado.lock or estado.fin or estado.pd or estado.vp_n or estado.ed:
        return []
    if not forzar and todavia_puede_actuar(estado):
        estado.ec = True
        return []
    if len(estado.P.hand) > TAMANO_MANO:
        estado.ed = len(estado.P.hand) - TAMANO_MANO
        return []

    acciones: list[AccionEnemiga] = []
    estado.lock = True
    estado.sel = -1
    estado.tg = None
    E = estado.E
    E.turnos_enemigo += 1
    empezar_turno(estado, E)

    acciones.extend(_pasivas_enemigo(estado))
    if comprobar_fin(estado):
        acciones.append(AccionEnemiga(tipo="fin", datos={"fin": estado.fin}))
        return acciones

    # Bucle de jugadas: mayor coste primero, hasta no poder más.
    while True:
        jugada = _elegir_jugada_enemiga(estado)
        if jugada is None:
            break
        carta, indice = jugada
        objetivo, nombre_obj = _objetivo_jugada_enemiga(estado, carta)
        jugada_ok = jugar_carta(estado, E, estado.P, indice, objetivo)
        if not jugada_ok:
            break
        acciones.append(
            AccionEnemiga(
                tipo="juega",
                carta=carta.identificador,
                nombre=carta.nombre,
                objetivo_nombre=nombre_obj,
                habla=_habla_enemiga(carta, nombre_obj),
            )
        )
        if comprobar_fin(estado):
            acciones.append(
                AccionEnemiga(tipo="fin", datos={"fin": estado.fin})
            )
            return acciones

    # Habilidades activas de criaturas (no curar si ya casi a tope).
    for c in list(E.bd):
        habilidad = c.habilidad_activa
        if (
            not habilidad
            or c.usada
            or E.qi < habilidad.coste_qi
            or (
                habilidad.tipo == TipoEfecto.CURAR
                and E.hp > E.mx - 3
            )
        ):
            continue
        E.qi -= habilidad.coste_qi
        c.usada = True
        efecto(estado, E, estado.P, habilidad.tipo, habilidad.valor)
        estado.log(f"{c.nombre} usa {habilidad.descripcion}")
        limpiar(estado)
        acciones.append(
            AccionEnemiga(
                tipo="habilidad",
                carta=c.identificador,
                nombre=c.nombre,
                habla="d",
                datos={
                    "efecto": habilidad.tipo.value,
                    "valor": habilidad.valor,
                },
            )
        )
        if comprobar_fin(estado):
            acciones.append(
                AccionEnemiga(tipo="fin", datos={"fin": estado.fin})
            )
            return acciones

    # Ataques de criaturas listas.
    for a in list(E.bd):
        if not a.lista_para_atacar:
            continue
        k = _objetivo_ataque_enemigo(estado, a)
        objetivo_nombre = (
            estado.P.bd[k].nombre
            if 0 <= k < len(estado.P.bd)
            else None
        )
        atacar(estado, E, estado.P, a, k)
        acciones.append(
            AccionEnemiga(
                tipo="ataca",
                carta=a.identificador,
                nombre=a.nombre,
                objetivo_nombre=objetivo_nombre,
                habla="c",
            )
        )
        if comprobar_fin(estado):
            acciones.append(
                AccionEnemiga(tipo="fin", datos={"fin": estado.fin})
            )
            return acciones

    # Exceso de mano al final del turno enemigo.
    descartar_enemigo_exceso(estado, E)
    acciones.append(AccionEnemiga(tipo="descarta"))

    # Vuelve el turno del jugador.
    acciones.append(AccionEnemiga(tipo="fin", datos={"fin": ""}))
    if not estado.fin:
        estado.lock = False
        turno_jugador(estado)
        if comprobar_fin(estado):
            acciones.append(
                AccionEnemiga(tipo="fin", datos={"fin": estado.fin})
            )
    return acciones
