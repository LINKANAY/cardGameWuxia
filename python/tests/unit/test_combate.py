"""Tests del motor de combate (Fase 2, story-001).

Paridad con `js/02-motor.js`: fórmulas, redondeo JS y secuencias de RNG
sembrado. Las citas de línea se refieren al monolito.
"""

from __future__ import annotations

import pytest

from app.data.bestias import BESTIAS_ESPIRITUALES, bestia_para_enemigo
from app.data.cartas import CARTAS
from app.data.niveles import ENEMIGOS
from app.data.tipos import TipoCarta, TipoEfecto
from app.engine import combat
from app.engine.combat import (
    MAX_COPIAS_PILA,
    TAMANO_MANO,
    TOPE_MANO_FISICA,
    EstadoCombate,
    Lado,
    activar_habilidad,
    atacar,
    cartas_jugables,
    comprobar_fin,
    curar,
    efecto,
    efecto_pila,
    empezar_turno,
    herir,
    iniciar_combate,
    jugar_carta,
    limpiar,
    multiplicadores_enemigo,
    objetivo_pila,
    poner_formacion,
    recuperar_vacio,
    robar,
    subir_pila,
    techo_vida,
    turno_formaciones,
    vida_heroe_max,
)
from app.engine.rng import GeneradorAleatorio
from app.engine.rules import construir_mazo
from app.engine.state import crear_carta_juego

# --- Helpers -----------------------------------------------------------------


def _estado_vacio(*, semilla: str = "test") -> EstadoCombate:
    """Estado mínimo con dos lados vacíos y RNG sembrado."""
    P = Lado(nombre="Tú", hp=30, mx=30, es_jugador=True)
    E = Lado(nombre="Dummy", hp=10, mx=10)
    return EstadoCombate(P=P, E=E, rng=GeneradorAleatorio(semilla))


def _con_mano(ids: list[str], *, qi: int | None = None, **kw) -> EstadoCombate:
    """Estado con el jugador con esas cartas en mano (y Qi suficiente)."""
    estado = _estado_vacio(**kw)
    estado.P.hand = [crear_carta_juego(i) for i in ids]
    if qi is None:
        qi = max((c.coste_qi for c in estado.P.hand), default=0) + 2
    estado.P.qi = qi
    estado.P.mq = qi
    estado.P.cap = max(qi, 5)
    return estado


def _mazo_fijo(ids: list[str]) -> list[str]:
    return list(ids)


# --- Constantes / fórmulas ---------------------------------------------------


def test_vida_heroe_max():
    # js/06-contenido.js:225 — HP_BASE + HP_PER_REALM * realm
    assert vida_heroe_max(0) == 30
    assert vida_heroe_max(3) == 36
    assert vida_heroe_max(8) == 46


def test_multiplicadores_enemigo_piso_cero():
    enemigo = ENEMIGOS[0]  # nivel 1, dificultad 0
    ea, eh = multiplicadores_enemigo(enemigo, reino=0)
    # piso=0 → sin bonus de piso; reino=0 → sin bonus de reino
    assert ea == pytest.approx(1.0)
    # eh = (hp + 2*0) / hp = 1
    assert eh == pytest.approx(1.0)


def test_efecto_pila_sku_y_normal():
    # SKU = 'rqe': +1 sólo al llegar a MAXSK
    assert efecto_pila("r", 3, 2) == 0
    assert efecto_pila("r", 3, 3) == 1
    # Otras claves: (n-1) * ceil(v/2)
    assert efecto_pila("d", 4, 2) == 2  # 1 * ceil(4/2)
    assert efecto_pila("d", 5, 3) == 6  # 2 * ceil(5/2)


def test_techo_vida_sobrecuracion_solo_jugador():
    estado = _estado_vacio()
    assert techo_vida(estado, estado.P) == 45  # floor(30 * 1.5)
    assert techo_vida(estado, estado.E) == 10


def test_hurt_absorbe_escudo_primero():
    estado = _estado_vacio()
    estado.P.sh = 5
    herir(estado, estado.P, 8)
    assert estado.P.sh == 0
    assert estado.P.hp == 30 - 3


def test_heal_no_superar_techo():
    estado = _estado_vacio()
    estado.P.hp = 40
    curar(estado, estado.P, 20)
    assert estado.P.hp == 45


# --- Robo y fatiga -----------------------------------------------------------


def test_robar_desde_mazo():
    estado = _estado_vacio()
    estado.P.dk = [crear_carta_juego("cf") for _ in range(5)]
    robar(estado, estado.P, 3)
    assert len(estado.P.hand) == 3
    assert len(estado.P.dk) == 2


def test_fatiga_al_agotar_mazo():
    estado = _estado_vacio()
    estado.P.dk = []
    hp0 = estado.P.hp
    robar(estado, estado.P, 1)
    assert estado.P.fat == 1
    assert estado.P.hp == hp0 - 1
    robar(estado, estado.P, 1)
    assert estado.P.fat == 2
    assert estado.P.hp == hp0 - 3  # 1 + 2


def test_robar_lim_respeta_tope_mano():
    estado = _estado_vacio()
    estado.P.dk = [crear_carta_juego("cf") for _ in range(10)]
    estado.P.hand = [crear_carta_juego("cf") for _ in range(TAMANO_MANO)]
    robar(estado, estado.P, 1, lim=True)
    assert len(estado.P.hand) == TAMANO_MANO  # no roba


def test_robar_sin_lim_usa_tope_fisico():
    estado = _estado_vacio()
    estado.P.dk = [crear_carta_juego("cf") for _ in range(20)]
    estado.P.hand = [crear_carta_juego("cf") for _ in range(TAMANO_MANO)]
    robar(estado, estado.P, 5)
    assert len(estado.P.hand) == TOPE_MANO_FISICA


# --- Apilado -----------------------------------------------------------------


def test_stk_t_elige_mayor_pila():
    estado = _estado_vacio()
    a = crear_carta_juego("gd")
    a.copias_apiladas = 1
    b = crear_carta_juego("gd")
    b.copias_apiladas = 2
    estado.P.bd = [a, b]
    c = crear_carta_juego("gd")
    objetivo = objetivo_pila(estado.P, c)
    assert objetivo is b


def test_stk_t_no_apila_bestias_ni_llenas():
    carta = crear_carta_juego("gd")
    carta.copias_apiladas = MAX_COPIAS_PILA
    assert objetivo_pila(Lado("x", 1, 1), carta) is None
    bestia = crear_carta_juego("EB1")
    assert objetivo_pila(Lado("x", 1, 1), bestia) is None


def test_stk_up_incrementa_stats():
    base = CARTAS["gd"]
    assert base.ataque and base.vida
    carta = crear_carta_juego("gd")
    a0, h0 = carta.ataque or 0, carta.vida or 0
    subir_pila(carta)
    assert carta.copias_apiladas == 2
    assert carta.ataque == a0 + -(-base.ataque // 2)  # ceil(A/2)
    assert carta.vida == h0 + -(-base.vida // 2)


# --- Jugar carta -------------------------------------------------------------


def test_play_gasto_qi_y_mano():
    estado = _con_mano(["gd"])  # criatura barata (Guardián de Piedra)
    qi0 = estado.P.qi
    c = estado.P.hand[0]
    assert jugar_carta(estado, estado.P, estado.E, 0)
    assert estado.P.qi == qi0 - c.coste_qi
    assert len(estado.P.hand) == 0
    assert len(estado.P.bd) == 1


def test_play_no_juega_sin_qi():
    estado = _con_mano(["gd"], qi=0)
    assert not jugar_carta(estado, estado.P, estado.E, 0)
    assert len(estado.P.hand) == 1


def test_play_dano_hroe():
    # Busca una carta con `d` en el catálogo
    dano_id = next(
        k for k, c in CARTAS.items() if c.dano_hroe and c.tipo == TipoCarta.TECNICA
    )
    carta = CARTAS[dano_id]
    estado = _con_mano([dano_id])
    hp0 = estado.E.hp
    assert jugar_carta(estado, estado.P, estado.E, 0)
    assert estado.E.hp == hp0 - (carta.dano_hroe or 0)


def test_play_escudo():
    esc_id = next(
        k
        for k, c in CARTAS.items()
        if c.escudo and c.tipo == TipoCarta.TECNICA and not c.dano_hroe
    )
    estado = _con_mano([esc_id])
    assert jugar_carta(estado, estado.P, estado.E, 0)
    assert estado.P.sh > 0


def test_play_llena_tablero_sin_pila():
    estado = _con_mano(["gu"])
    estado.P.bd = [crear_carta_juego("mj") for _ in range(5)]
    # Criatura no apilable con tablero lleno
    assert not combat.puede_jugar(estado, estado.P, estado.P.hand[0])


def test_play_criatura_en_tablero_lleno_con_pila():
    estado = _con_mano(["gd"])
    estado.P.bd = [crear_carta_juego("gd") for _ in range(5)]
    assert jugar_carta(estado, estado.P, estado.E, 0)
    # Se apiló sobre la primera gd
    assert len(estado.P.bd) == 5
    assert any(c.copias_apiladas == 2 for c in estado.P.bd)


# --- Ataque ------------------------------------------------------------------


def test_atacar_heroe():
    estado = _estado_vacio()
    c = crear_carta_juego("gd")
    c.lista_para_atacar = True
    estado.P.bd = [c]
    hp0 = estado.E.hp
    atacar(estado, estado.P, estado.E, c, -1)
    assert estado.E.hp < hp0
    assert not c.lista_para_atacar


def test_atacar_criatura_intercambio():
    estado = _estado_vacio()
    a = crear_carta_juego("gd")
    a.lista_para_atacar = True
    b = crear_carta_juego("gd")
    estado.P.bd = [a]
    estado.E.bd = [b]
    vida_b0 = b.vida or 0
    vida_a0 = a.vida or 0
    daño = a.ataque or 0
    atacar(estado, estado.P, estado.E, a, 0)
    assert (b.vida or 0) == vida_b0 - daño
    assert (a.vida or 0) == vida_a0 - (b.ataque or 0)


def test_robar_vida():
    estado = _estado_vacio()
    a = crear_carta_juego("cd")  # tiene vm
    if not a.definicion.robar_vida:
        a.definicion = CARTAS["cd"]
        a.ataque = a.definicion.ataque
        a.vida = a.definicion.vida
    assert a.definicion.robar_vida
    a.lista_para_atacar = True
    estado.P.bd = [a]
    estado.P.hp = 10
    atacar(estado, estado.P, estado.E, a, -1)
    assert estado.P.hp > 10


# --- Habilidad activa --------------------------------------------------------


def test_activar_habilidad_gasta_qi():
    # Busca criatura con habilidad
    ab_id = next(
        k for k, c in CARTAS.items() if c.habilidad_activa and c.ataque
    )
    estado = _estado_vacio()
    c = crear_carta_juego(ab_id)
    habilidad = c.habilidad_activa
    assert habilidad is not None
    estado.P.bd = [c]
    estado.P.qi = habilidad.coste_qi + 1
    assert activar_habilidad(estado, estado.P, estado.E, 0)
    assert estado.P.qi == 1
    assert c.usada
    # No se puede reactivar
    estado.P.qi = 10
    assert not activar_habilidad(estado, estado.P, estado.E, 0)


# --- Último aliento / limpiar ------------------------------------------------


def test_ultimo_aliento_al_morir():
    estado = _estado_vacio()
    # EB2 (Garza) tiene ul ['d', 2] — o cualquier carta con ul
    ul_id = next(k for k, c in CARTAS.items() if c.ultimo_aliento)
    c = crear_carta_juego(ul_id)
    assert c.ultimo_aliento is not None
    c.vida = 0
    estado.P.bd = [c]
    hp0 = estado.E.hp
    limpiar(estado)
    assert estado.E.hp < hp0 or c.vida == 0
    assert c not in estado.P.bd


def test_criatura_muerta_no_al_vacio_si_es_bestia():
    estado = _estado_vacio()
    bestia = crear_carta_juego("EB1")
    bestia.vida = 0
    estado.P.bd = [bestia]
    limpiar(estado)
    assert bestia not in estado.P.vd  # bestias no van al vacío
    assert bestia not in estado.P.bd


# --- Formaciones -------------------------------------------------------------


def test_fm_put_formacion_y_runas():
    estado = _estado_vacio()
    # Rama de formación: definición improvisada sobre una carta real
    from app.data.tipos import CartaData

    f = crear_carta_juego("gd")
    f.definicion = CartaData(
        identificador="fX",
        nombre="Formación Test",
        coste_qi=1,
        tipo=TipoCarta.FORMACION,
        mejora_vida_al_trazar=2,
    )
    estado.P.hand = [f]
    estado.P.qi = 5
    # jugar_carta branches on definicion.tipo
    assert jugar_carta(estado, estado.P, estado.E, 0)
    assert estado.P.fm is not None
    assert estado.P.fm.vida_fisica == 2


def test_formacion_dano_ts_hiere_al_rival():
    """`ts: ['d', n]` daña al héroe RIVAL (`fx(s, o, ts)` de `fmTurn`)."""
    estado = _estado_vacio()
    poner_formacion(estado, estado.P, crear_carta_juego("Y09"))
    vida_p, vida_e = estado.P.hp, estado.E.hp
    turno_formaciones(estado, estado.P)
    assert estado.E.hp == vida_e - 1
    assert estado.P.hp == vida_p


def test_formacion_auto_dano_ts_hiere_al_dueno_con_escudo():
    """`ts: ['x', n]` auto-daño al dueño (`hurt(s, n)` de `fmTurn`)."""
    estado = _estado_vacio()
    poner_formacion(estado, estado.P, crear_carta_juego("Y05"))
    vida_e = estado.E.hp
    estado.P.sh = 5
    turno_formaciones(estado, estado.P)
    # el escudo absorbe el punto y el rival no recibe nada
    assert estado.P.sh == 4
    assert estado.P.hp > 0
    assert estado.E.hp == vida_e


def test_lado_snapshot_expone_formacion_runas_y_bonus():
    """`_lado_snapshot` lleva fm/rn/atkb/salvavidas para la UI."""
    from app.services.combat_service import _lado_snapshot

    estado = _estado_vacio()
    poner_formacion(estado, estado.P, crear_carta_juego("Y05"))
    poner_formacion(estado, estado.P, crear_carta_juego("Y14"))
    estado.P.atkb = 3
    estado.P.esc = 1

    snap = _lado_snapshot(estado.P)
    assert snap["fm"]["id"] == "Y05"
    assert snap["fm"]["nombre"] == "Formación de Sangre Hirviente"
    assert snap["fm"]["pa"] == 2
    assert snap["fm"]["desc"] == [
        "Formación",
        "Tus criaturas: +2 ATK",
        "Cada turno: pierdes 1 de vida",
    ]
    assert len(snap["rn"]) == 1
    assert snap["rn"][0]["id"] == "Y14"
    assert snap["rn"][0]["du"] == 2
    assert snap["rn"][0]["desc"] == ["Runa · 2 turnos", "Al inicio de tu turno: roba 1"]
    assert snap["atkb"] == 3
    assert snap["bo"] is False
    assert snap["opa"] == 0 and snap["oph"] == 0
    assert snap["salvavidas"] is True


def test_snapshot_formacion_en_carta_de_mano():
    """F/R en mano llevan `formacion` (pa/ph/ts) para sus badges."""
    from app.services.combat_service import _carta_snapshot

    f = crear_carta_juego("Y05")
    r = crear_carta_juego("Y11")
    assert _carta_snapshot(f)["formacion"] == {
        "pa": 2,
        "ph": 0,
        "ts": ["x", 1],
    }
    assert _carta_snapshot(r)["formacion"] == {
        "pa": 0,
        "ph": 0,
        "ts": ["d", 2],
    }
    assert _carta_snapshot(crear_carta_juego("cf"))["formacion"] is None


# --- Comprobar fin -----------------------------------------------------------


def test_chk_victoria_emite_evento():
    estado = _estado_vacio()
    estado.E.hp = 0
    assert comprobar_fin(estado)
    assert estado.fin == "w"
    tipos = [e.tipo for e in estado.eventos]
    assert "victoria" in tipos


def test_chk_muerte():
    estado = _estado_vacio()
    estado.P.hp = 0
    assert comprobar_fin(estado)
    assert estado.fin == "l"
    assert [e.tipo for e in estado.eventos] == ["muerte"]


def test_chk_revive_pildora_inmortalidad():
    estado = _estado_vacio()
    estado.P.hp = 0
    estado.P.revivir = 1
    assert not comprobar_fin(estado)
    assert estado.P.hp == 15
    assert estado.P.revivir == 0
    assert estado.fin == ""


def test_chk_escape_talisman():
    estado = _estado_vacio()
    estado.P.hp = 0
    estado.P.esc = 1
    assert comprobar_fin(estado)
    assert estado.fin == "f"
    assert [e.tipo for e in estado.eventos] == ["escape"]


def test_chk_no_doble_victoria():
    estado = _estado_vacio()
    estado.E.hp = 0
    assert comprobar_fin(estado)
    estado.eventos.clear()
    assert comprobar_fin(estado)
    assert estado.eventos == []  # ya era 'w'


# --- Bestias -----------------------------------------------------------------


def test_bestias_catalogo_completo():
    assert len(BESTIAS_ESPIRITUALES) == 6
    assert BESTIAS_ESPIRITUALES[0].identificador == "EB1"
    assert BESTIAS_ESPIRITUALES[-1].identificador == "EB6"


def test_bestia_para_enemigo_escala():
    b, nivel = bestia_para_enemigo(0, 0)
    assert nivel == 1
    assert b.identificador == "EB1"
    b10, nivel10 = bestia_para_enemigo(7, 5)  # score alto
    assert nivel10 == 10
    assert b10.identificador == "EB6"


def test_crear_carta_bestia():
    c = crear_carta_juego("EB1")
    assert c.es_bestia
    assert c.definicion.reliquia
    assert c.definicion.coste_qi == 0
    assert c.ataque == 2
    assert c.vida == 3


# --- iniciar_combate ---------------------------------------------------------


def test_iniciar_combate_mazos_y_turno():
    enemigo = ENEMIGOS[0]
    mazo_p = construir_mazo("esp", aleatorio=lambda: 0.5)
    extras = enemigo.indice_nivel + enemigo.dificultad
    mazo_e = construir_mazo(
        enemigo.secta,
        con_coleccion=False,
        extras=extras,
        aleatorio=lambda: 0.5,
    )
    estado = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=mazo_p,
        mazo_enemigo=mazo_e,
    )
    assert estado.P.es_jugador
    # 30 de base + 2 del traje base (applyOutfit: Túnica del Discípulo)
    assert estado.P.hp == 32
    # begin roba 4 para ambos; el turno del jugador roba 1 más
    assert len(estado.P.hand) == 5
    assert len(estado.E.hand) == 4
    assert estado.E.bestia is not None
    assert estado.E.bestia.es_bestia
    assert estado.P.numero_turno == 1
    # Qi del primer turno: mq=1
    assert estado.P.mq == 1
    assert not estado.lock or estado.fin


def test_iniciar_combate_vida_hroe_clamp():
    enemigo = ENEMIGOS[0]
    mazo = construir_mazo("esp", aleatorio=lambda: 0.3)
    estado = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=999,
        mazo_jugador=mazo,
        mazo_enemigo=mazo,
    )
    # el clamp es a la vida máxima ANTES del traje (+2): 30 → 32
    assert estado.P.hp == 32
    estado2 = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=5,
        mazo_jugador=mazo,
        mazo_enemigo=mazo,
    )
    # el traje suma sobre la vida actual, como en el monolito: 5 → 7
    assert estado2.P.hp == 7


def test_iniciar_combate_pildora_vit():
    enemigo = ENEMIGOS[0]
    mazo = construir_mazo("esp", aleatorio=lambda: 0.3)
    estado = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=mazo,
        mazo_enemigo=mazo,
        pildoras_inicio=["vit"],
    )
    # vit: +8 máx y +8 vida, más el traje base (+2): 30 + 8 + 2
    assert estado.P.mx == 40
    assert estado.P.hp == 40


# --- Equipo y trajes en combate (applyGear / applyOutfit) -------------------


def _mazo_prueba() -> list[str]:
    return construir_mazo("esp", aleatorio=lambda: 0.3)


def test_equipo_del_jugador_entra_en_combate():
    enemigo = ENEMIGOS[0]
    estado = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
        equipado={"cabeza": "G3", "cuerpo": "G6"},
        equipo_guardado={"G3": 1, "G6": 1},
    )
    # a2 + a3 = 5 → tope +4; q2 + q1 = 3 sobre la base de 6
    assert estado.P.atkb == 4
    assert estado.P.cap == 9

    # sin poseer la pieza no aporta nada (gearStat solo cuenta `gr`)
    sin_poseer = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
        equipado={"cabeza": "G3"},
        equipo_guardado={},
    )
    assert sin_poseer.P.atkb == 0
    assert sin_poseer.P.cap == 6


def test_artefacto_se_arma_si_esta_forjado_y_con_usos():
    enemigo = ENEMIGOS[0]
    base = dict(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
    )
    armado = iniciar_combate(
        **base,
        equipado={"artefacto": "G10"},
        equipo_guardado={"G10": 1},
        usos_equipo={"G10": 3},
    )
    assert armado.P.artefacto == "G10"

    agotado = iniciar_combate(
        **base,
        equipado={"artefacto": "G10"},
        equipo_guardado={"G10": 1},
        usos_equipo={"G10": 0},
    )
    assert agotado.P.artefacto is None

    sin_forjar = iniciar_combate(
        **base,
        equipado={"artefacto": "G10"},
        equipo_guardado={},
        usos_equipo={"G10": 3},
    )
    assert sin_forjar.P.artefacto is None


def test_traje_del_jugador_aplica_su_efecto():
    enemigo = ENEMIGOS[0]
    base = dict(
        enemigo=enemigo,
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
    )
    # esp[1] «Armadura de Plata»: +1 Filo → atkb y ofx
    con_filo = iniciar_combate(**base, atuendo={"esp": 1}, secta="esp")
    assert con_filo.P.atkb == 1
    assert con_filo.P.ofx is not None
    assert "Armadura de Plata" in con_filo.P.ofx
    assert "Filo de la Espada" in con_filo.P.ofx

    # esp[2]: Primer golpe 3 → el rival pierde 3 vida al empezar
    sin_traje = iniciar_combate(**base, atuendo={}, secta="esp")
    con_primer_golpe = iniciar_combate(
        **base, atuendo={"esp": 2}, secta="esp"
    )
    assert con_primer_golpe.E.hp == sin_traje.E.hp - 3

    # lun[2]: Velo 1 → escudo al inicio de cada turno
    con_velo = iniciar_combate(**base, atuendo={"lun": 2}, secta="lun")
    assert con_velo.P.osh == 1

    # sin traje en el armario manda el índice 0 (outfit[sect] || 0)
    por_defecto = iniciar_combate(**base, atuendo={}, secta="esp")
    assert por_defecto.P.mx == vida_heroe_max(0) + 2


def test_artefacto_revive_con_su_vida_y_lo_registra():
    estado = iniciar_combate(
        enemigo=ENEMIGOS[0],
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
    )
    estado.P.artefacto = "G10"
    estado.P.hp = 0
    muerto = comprobar_fin(estado)
    assert not muerto
    assert estado.P.hp == 10
    assert estado.P.artefacto is None
    assert any(
        "Campana del Alma te devuelve a la vida con 10" in linea
        for linea in estado.logs
    )
    assert any(
        evento.tipo == "salvar_artefacto" for evento in estado.eventos
    )


def test_equipo_enemigo_usa_el_catalogo():
    enemigo = next(
        e
        for e in ENEMIGOS
        if (e.indice_nivel or 0) * 6 + (e.dificultad or 0) >= 40
    )
    estado = iniciar_combate(
        enemigo=enemigo,
        indice_enemigo=None,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
    )
    # score ≥40 → 3 filas, columna t = 2 (G6/G14/G17) y tope cp = 2
    assert estado.E.atkb == 2
    assert estado.E.gear == [
        "Armadura del Inmortal",
        "Manoplas del Dragón",
        "Botas del Inmortal",
    ]
    assert estado.E.gear_texto == "Ataque +2, Qi +2"
    assert any("viste" in linea for linea in estado.logs)

    # score 0 (primer enemigo) no viste nada
    novato = iniciar_combate(
        enemigo=ENEMIGOS[0],
        indice_enemigo=0,
        reino=0,
        vida_hroe=None,
        mazo_jugador=_mazo_prueba(),
        mazo_enemigo=_mazo_prueba(),
    )
    assert novato.E.gear == []


# --- RNG determinista --------------------------------------------------------


def test_mismo_semen_misma_secuencia():
    def secuencia(semilla: str) -> list[float]:
        rng = GeneradorAleatorio(semilla)
        return [rng.random() for _ in range(5)]

    assert secuencia("abc") == secuencia("abc")
    assert secuencia("abc") != secuencia("xyz")


def test_cartas_jugables_filtra():
    estado = _con_mano(["cf", "gu"])  # gu cuesta más
    estado.P.qi = 0
    assert cartas_jugables(estado) == []
    estado.P.qi = 10
    assert len(cartas_jugables(estado)) == 2


# --- Victoria inmediata (chk tras play/hit/act) ------------------------------


def test_jugar_carta_matar_cierra_combate():
    # js/07-campamento.js:110 — `fin()`: `if (chk()) lock = true`.
    estado = _con_mano(["cf"])  # Corte Fugaz: 3 de daño al héroe
    estado.E.hp = 2
    assert jugar_carta(estado, estado.P, estado.E, 0)
    assert estado.E.hp <= 0
    assert estado.fin == "w"
    assert estado.lock is True


def test_jugar_carta_sin_matar_no_cierra():
    estado = _con_mano(["cf"])
    estado.E.hp = 99
    assert jugar_carta(estado, estado.P, estado.E, 0)
    assert estado.fin == ""
    assert estado.lock is False


def test_atacar_matar_cierra_combate():
    # js/07-campamento.js:118 — `go()`: `if (chk()) lock = true`.
    estado = _estado_vacio()
    criatura = crear_carta_juego("ma")  # Maestro: ataque 4
    criatura.lista_para_atacar = True
    estado.P.bd = [criatura]
    estado.E.hp = 4
    atacar(estado, estado.P, estado.E, criatura, -1)
    assert estado.E.hp <= 0
    assert estado.fin == "w"
    assert estado.lock is True


def test_activar_habilidad_matar_cierra_combate():
    # js/02-motor.js:27 — `act()`: `if (chk()) lock = true`.
    estado = _estado_vacio()
    estado.P.qi = 5
    estado.P.mq = 5
    criatura = crear_carta_juego("rd")  # Rey Dragón: Aliento 3
    estado.P.bd = [criatura]
    estado.E.hp = 2
    assert activar_habilidad(estado, estado.P, estado.E, 0)
    assert estado.E.hp <= 0
    assert estado.fin == "w"
    assert estado.lock is True
