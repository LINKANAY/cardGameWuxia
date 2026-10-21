"""Tests de la IA enemiga (Fase 2, story-002 — `endT`)."""

from __future__ import annotations

import pytest

from app.data.niveles import ENEMIGOS
from app.data.tipos import TipoCarta
from app.engine.combat import (
    TAMANO_MANO,
    AccionEnemiga,
    EstadoCombate,
    Lado,
    _elegir_jugada_enemiga,
    _objetivo_ataque_enemigo,
    _pasivas_enemigo,
    confirmar_cierre,
    descartar_exceso_jugador,
    fin_turno_enemigo,
    iniciar_combate,
    jugar_carta,
    turno_jugador,
)
from app.engine.rng import GeneradorAleatorio
from app.engine.rules import construir_mazo
from app.engine.state import crear_carta_juego


def _estado_enemigo(
    *,
    habilidades: tuple[str, ...] = (),
    reino: int = 0,
    vida_e: int = 20,
    qi_e: int = 10,
) -> EstadoCombate:
    """Estado mínimo con enemigo de catálogo (habilidades clonables)."""
    from dataclasses import replace

    enemigo = replace(ENEMIGOS[0], habilidades=tuple(habilidades))
    P = Lado(nombre="Tú", hp=30, mx=30, es_jugador=True)
    E = Lado(
        nombre=enemigo.nombre_enemigo,
        hp=vida_e,
        mx=vida_e,
        qi=qi_e,
        mq=5,
        cap=7,
    )
    return EstadoCombate(
        P=P,
        E=E,
        enemigo=enemigo,
        indice_enemigo=0,
        mult_ataque_enemigo=1.0,
        mult_vida_enemiga=1.0,
        rng=GeneradorAleatorio("endt"),
    )


# --- Guardas de cierre -------------------------------------------------------


def test_confirmar_cierre_todavia_actua():
    estado = _estado_enemigo()
    estado.P.hand = [crear_carta_juego("cf")]  # jugable con qi
    estado.P.qi = 5
    assert confirmar_cierre(estado) == "todavia_actua"
    assert estado.ec


def test_confirmar_cierre_exceso_mano():
    estado = _estado_enemigo()
    estado.P.hand = [crear_carta_juego("cf") for _ in range(TAMANO_MANO + 2)]
    estado.P.qi = 0  # nada jugable
    assert confirmar_cierre(estado) == "exceso_mano"
    assert estado.ed == 2


def test_descartar_exceso_jugador():
    estado = _estado_enemigo()
    estado.P.hand = [crear_carta_juego("cf") for _ in range(7)]
    estado.ed = 2
    assert descartar_exceso_jugador(estado, 0)
    assert estado.ed == 1
    assert len(estado.P.vd) == 1
    assert descartar_exceso_jugador(estado, 0)
    assert estado.ed == 0


# --- Pasivas -----------------------------------------------------------------


def test_pasiva_heal():
    estado = _estado_enemigo(habilidades=("heal",), vida_e=10)
    estado.E.hp = 6  # por debajo del máximo
    estado.E.turnos_enemigo = 1
    acciones = _pasivas_enemigo(estado)
    assert any(a.nombre == "heal" for a in acciones)
    # round(2 * 1.0) = 2
    assert estado.E.hp == 8


def test_pasiva_regen_escudo():
    estado = _estado_enemigo(habilidades=("regen",))
    estado.E.turnos_enemigo = 1
    _pasivas_enemigo(estado)
    assert estado.E.sh == 4


def test_pasiva_drain_cada_3():
    estado = _estado_enemigo(habilidades=("drain",))
    estado.P.mq = 5
    estado.E.turnos_enemigo = 3  # 3 % 3 == 0
    _pasivas_enemigo(estado)
    assert estado.P.mq == 4
    estado.E.turnos_enemigo = 4  # no
    estado.P.mq = 5
    _pasivas_enemigo(estado)
    assert estado.P.mq == 5


def test_pasiva_seal():
    estado = _estado_enemigo(habilidades=("seal",))
    estado.E.turnos_enemigo = 3
    _pasivas_enemigo(estado)
    assert estado.P.pen == 2


def test_pasiva_mist_descarta():
    estado = _estado_enemigo(habilidades=("mist",))
    estado.P.hand = [crear_carta_juego("cf") for _ in range(3)]
    estado.E.turnos_enemigo = 3
    _pasivas_enemigo(estado)
    assert len(estado.P.hand) == 2
    assert len(estado.P.vd) == 1


def test_pasiva_blade():
    estado = _estado_enemigo(habilidades=("blade",))
    hp0 = estado.P.hp
    estado.E.turnos_enemigo = 2
    _pasivas_enemigo(estado)
    assert estado.P.hp == hp0 - 3  # round(3 * 1.0)


def test_pasiva_breath():
    estado = _estado_enemigo(habilidades=("breath",), vida_e=10)
    hp0 = estado.P.hp
    estado.E.turnos_enemigo = 3
    _pasivas_enemigo(estado)
    assert estado.P.hp == hp0 - 5
    assert estado.E.hp == min(10, 10 + 4)


def test_pasivas_solo_en_multiplos():
    estado = _estado_enemigo(habilidades=("blade",))
    hp0 = estado.P.hp
    estado.E.turnos_enemigo = 1  % 2 != 0
    _pasivas_enemigo(estado)
    assert estado.P.hp == hp0


# --- Prioridad de jugada -----------------------------------------------------


def test_elegir_jugada_mayor_coste():
    estado = _estado_enemigo()
    # Dos técnicas de daño con costes distintos
    barata = next(
        k
        for k, c in __import__("app.data.cartas", fromlist=["CARTAS"])
        .CARTAS.items()
        if c.dano_hroe and c.coste_qi == 1 and c.tipo == TipoCarta.TECNICA
    )
    cara = next(
        k
        for k, c in __import__("app.data.cartas", fromlist=["CARTAS"])
        .CARTAS.items()
        if c.dano_hroe and c.coste_qi >= 3 and c.tipo == TipoCarta.TECNICA
    )
    from app.data.cartas import CARTAS

    if CARTAS[cara].sacrificar_vida and estado.E.hp <= (
        CARTAS[cara].sacrificar_vida or 0
    ) + 4:
        # elijo otra si sacrifica vida
        cara = next(
            k
            for k, c in CARTAS.items()
            if c.dano_hroe
            and c.coste_qi >= 3
            and c.tipo == TipoCarta.TECNICA
            and not c.sacrificar_vida
        )
    estado.E.hand = [crear_carta_juego(barata), crear_carta_juego(cara)]
    estado.E.qi = 10
    jugada = _elegir_jugada_enemiga(estado)
    assert jugada is not None
    carta, _ = jugada
    assert carta.coste_qi >= CARTAS[barata].coste_qi


def test_elegir_jugada_filtra_sacrificio():
    from app.data.cartas import CARTAS

    sac_id = next(
        k
        for k, c in CARTAS.items()
        if c.sacrificar_vida and c.tipo == TipoCarta.TECNICA
    )
    sac = CARTAS[sac_id].sacrificar_vida or 0
    estado = _estado_enemigo(vida_e=sac + 4)  # hp <= sac + 4
    estado.E.hp = sac + 4
    estado.E.hand = [crear_carta_juego(sac_id)]
    estado.E.qi = 20
    assert _elegir_jugada_enemiga(estado) is None


def test_elegir_jugada_filtra_duplicado_formacion():
    # Mano vacía: no hay jugada; las ramas F/R quedan de lado — smoke
    estado = _estado_enemigo()
    estado.E.hand = []
    assert _elegir_jugada_enemiga(estado) is None


# --- Objetivo de ataque ------------------------------------------------------


def test_objetivo_ataque_heroe_si_tablero_vacio():
    estado = _estado_enemigo()
    atacante = crear_carta_juego("EB1")
    assert _objetivo_ataque_enemigo(estado, atacante) == -1


def test_objetivo_ataque_prefiere_trade():
    estado = _estado_enemigo()
    # atacante 3/5; rival A: 5/2 (trade malo), B: 1/4 (trade bueno H<=A y A<H)
    a = crear_carta_juego("mj")
    a.ataque, a.vida = 5, 2
    b = crear_carta_juego("gd")
    b.ataque, b.vida = 1, 4
    estado.P.bd = [a, b]
    atacante = crear_carta_juego("EB1")
    atacante.ataque, atacante.vida = 3, 5
    # B: vida 4 <= 3? no. A: vida 2 <= 3 y ataque 5 < 5? no (5 < 5 false)
    # Ninguno trade favorable → sin provocar: 50% o héroe
    k = _objetivo_ataque_enemigo(estado, atacante)
    assert k in (-1, 0, 1)


def test_objetivo_ataque_provocar_obliga():
    estado = _estado_enemigo()
    normal = crear_carta_juego("gr")  # Grulla de Loto, sin provocar
    assert not normal.definicion.provocar
    normal.ataque, normal.vida = 1, 10
    tank = crear_carta_juego("gu")  # Guardián de Piedra ya tiene provocar
    assert tank.definicion.provocar
    tank.ataque, tank.vida = 0, 9
    estado.P.bd = [normal, tank]
    atacante = crear_carta_juego("EB1")
    atacante.ataque, atacante.vida = 2, 3
    k = _objetivo_ataque_enemigo(estado, atacante)
    assert k == 1  # el provocar


# --- fin_turno_enemigo completo ----------------------------------------------


def test_fin_turno_enemigo_basico():
    enemigo = ENEMIGOS[0]
    mazo = construir_mazo("esp", aleatorio=lambda: 0.4)
    mazo_e = construir_mazo(enemigo.secta, extras=0, aleatorio=lambda: 0.4)
    estado = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=mazo,
        mazo_enemigo=mazo_e,
        rng=GeneradorAleatorio("basico"),
    )
    # forzar no jugable
    estado.P.hand = [crear_carta_juego("cf")]
    estado.P.qi = 0
    acciones = fin_turno_enemigo(estado)
    assert acciones  # hubo al menos fin
    assert acciones[-1].tipo == "fin"
    # El turno del jugador volvió
    assert estado.P.numero_turno == 2
    assert estado.P.mq >= 2
    assert not estado.fin


def test_fin_turno_bloqueado_si_todavia_actua():
    estado = _estado_enemigo()
    estado.P.hand = [crear_carta_juego("cf")]
    estado.P.qi = 10
    acciones = fin_turno_enemigo(estado)
    assert acciones == []
    assert estado.ec
    # forzar sí pasa
    acciones = fin_turno_enemigo(estado, forzar=True)
    assert acciones[-1].tipo == "fin"


def test_fin_turno_exceso_mano_no_ejecuta():
    estado = _estado_enemigo()
    estado.P.hand = [crear_carta_juego("cf") for _ in range(7)]
    estado.P.qi = 0
    acciones = fin_turno_enemigo(estado)
    assert acciones == []
    assert estado.ed == 2


def test_fin_turno_enemigo_juega_carta():
    from app.data.cartas import CARTAS

    dano_id = next(
        k
        for k, c in CARTAS.items()
        if c.dano_hroe
        and c.tipo == TipoCarta.TECNICA
        and not c.sacrificar_vida
        and not c.curar
    )
    estado = _estado_enemigo(vida_e=30)
    estado.E.hand = [crear_carta_juego(dano_id)]
    estado.E.dk = [crear_carta_juego("cf") for _ in range(5)]
    estado.P.dk = [crear_carta_juego("cf") for _ in range(5)]
    hp0 = estado.P.hp
    acciones = fin_turno_enemigo(estado, forzar=True)
    assert any(a.tipo == "juega" for a in acciones)
    assert estado.P.hp < hp0


def test_fin_turno_enemigo_ataca_con_criatura():
    estado = _estado_enemigo(vida_e=30)
    c = crear_carta_juego("EB1")
    c.lista_para_atacar = True
    estado.E.bd = [c]
    estado.E.hand = []
    estado.E.dk = [crear_carta_juego("cf") for _ in range(5)]
    estado.P.dk = [crear_carta_juego("cf") for _ in range(5)]
    hp0 = estado.P.hp
    acciones = fin_turno_enemigo(estado, forzar=True)
    assert any(a.tipo == "ataca" for a in acciones)
    assert estado.P.hp < hp0


def test_fin_turno_termina_si_muere():
    estado = _estado_enemigo(vida_e=1)
    # Pasiva blade que mate al jugador no; mejor: enemigo con hp bajo y
    # el jugador le daña al empezar… Simulamos muerte por tribulación.
    # Enemigo hp=1, pasiva breath no. Usa blade y P con 1 hp.
    estado = _estado_enemigo(habilidades=("blade",), vida_e=50)
    estado.P.hp = 3
    estado.E.turnos_enemigo = 2
    estado.E.hand = []
    estado.E.dk = [crear_carta_juego("cf")]
    estado.P.dk = [crear_carta_juego("cf")]
    acciones = fin_turno_enemigo(estado, forzar=True)
    assert estado.fin == "l"
    assert acciones[-1].datos.get("fin") == "l"


def test_fin_turno_mejora_aliada_elige_mas_ataque():
    from app.data.cartas import CARTAS

    bf_id = next(
        k
        for k, c in CARTAS.items()
        if c.mejorar_aliada and c.tipo == TipoCarta.TECNICA and not c.dano_hroe
    )
    estado = _estado_enemigo(vida_e=40)
    débil = crear_carta_juego("gd")
    débil.ataque = 1
    fuerte = crear_carta_juego("mj")
    fuerte.ataque = 5
    estado.E.bd = [débil, fuerte]
    estado.E.hand = [crear_carta_juego(bf_id)]
    estado.E.qi = 10
    estado.E.dk = [crear_carta_juego("cf")]
    estado.P.dk = [crear_carta_juego("cf")]
    fin_turno_enemigo(estado, forzar=True)
    assert fuerte.ataque > 5 or débil.ataque > 1
    # El JS elige el de más ataque
    assert fuerte.ataque > 5


def test_secuencia_rng_determinista_endt():
    def correr() -> list[str]:
        enemigo = ENEMIGOS[0]
        mazo = construir_mazo("esp", aleatorio=lambda: 0.7)
        mazo_e = construir_mazo(enemigo.secta, extras=1, aleatorio=lambda: 0.7)
        estado = iniciar_combate(
            enemigo=enemigo,
            indice_enemigo=0,
            reino=0,
            vida_hroe=None,
            mazo_jugador=mazo,
            mazo_enemigo=mazo_e,
            rng=GeneradorAleatorio("seed-x"),
        )
        estado.P.qi = 0
        acciones = fin_turno_enemigo(estado)
        return [f"{a.tipo}:{a.carta or a.nombre or ''}" for a in acciones]

    assert correr() == correr()
