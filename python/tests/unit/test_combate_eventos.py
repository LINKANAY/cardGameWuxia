"""Eventos de mapa y píldoras de bolsa (Fase 3, fix story-007).

Paridad con `EV`/`evPick` (js/06-contenido.js:213, js/07-campamento.js:108)
y `usePill`/`battlePill` (js/06-contenido.js:165-166).
"""

from __future__ import annotations

from app.data.cartas import CARTAS
from app.data.pildoras import PILDORAS
from app.engine import combat
from app.engine.combat import (
    EVENTOS_MAPA,
    EstadoCombate,
    Lado,
    aplicar_pildora_bolsa,
    elegir_evento_mapa,
    puede_usar_pildora,
    resolver_evento_mapa,
    turno_jugador,
)
from app.engine.rng import GeneradorAleatorio
from app.engine.state import crear_carta_juego


class _RNGCero:
    """RNG que devuelve siempre 0 (fuerza el evento de mapa)."""

    def random(self) -> float:
        return 0.0

    def barajar(self, lista):
        return list(lista)


def _estado_con_evento() -> EstadoCombate:
    """Estado recién pasado al turno 2 con evento de mapa activo."""
    P = Lado(nombre="Tú", hp=30, mx=30, es_jugador=True)
    E = Lado(nombre="Dummy", hp=20, mx=20)
    ids = list(CARTAS)[:8]
    P.dk = [crear_carta_juego(i) for i in ids]
    estado = EstadoCombate(P=P, E=E, rng=_RNGCero())
    estado.P.numero_turno = 1
    turno_jugador(estado)
    return estado


def _estado_bolsa(bolsa: list[str], *, hp: int = 20) -> EstadoCombate:
    P = Lado(nombre="Tú", hp=hp, mx=30, es_jugador=True)
    E = Lado(nombre="Dummy", hp=20, mx=20)
    P.bolsa_pildoras = list(bolsa)
    return EstadoCombate(P=P, E=E, rng=GeneradorAleatorio("bolsa"))


# --- Eventos de mapa ---------------------------------------------------------


def test_turno_jugador_activa_evento_de_mapa():
    estado = _estado_con_evento()
    assert estado.P.numero_turno == 2
    assert estado.ev is not None
    assert estado.ev in EVENTOS_MAPA
    assert estado.lock is True
    assert any(linea.startswith("Evento: ") for linea in estado.logs)


def test_elegir_evento_mapa_respeta_tabla():
    estado = _estado_con_evento()
    elegido = elegir_evento_mapa(estado)
    assert elegido in EVENTOS_MAPA


def test_resolver_evento_desbloquea_y_loguea():
    estado = _estado_con_evento()
    # Opción 1 de la Cueva ancestral: "Ignorarla" (sin efectos).
    assert resolver_evento_mapa(estado, 1) is True
    assert estado.ev is None
    assert estado.lock is False
    assert estado.logs[-1] == "Cueva ancestral: Sigues tu camino."


def test_resolver_evento_aplica_efecto():
    estado = _estado_con_evento()
    qi_antes = estado.P.qi
    hp_antes = estado.P.hp
    # Opción 0: +3 Qi y −3 vida.
    assert resolver_evento_mapa(estado, 0) is True
    assert estado.P.qi == qi_antes + 3
    assert estado.P.hp == hp_antes - 3


def test_resolver_evento_sin_evento_rechazado():
    estado = _estado_con_evento()
    assert resolver_evento_mapa(estado, 0) is True
    assert resolver_evento_mapa(estado, 0) is False


def test_resolver_evento_opcion_invalida_rechazada():
    estado = _estado_con_evento()
    assert resolver_evento_mapa(estado, 99) is False
    assert estado.ev is not None
    assert estado.lock is True


def test_resolver_evento_no_bloquea_si_no_hay_fin():
    estado = _estado_con_evento()
    resolver_evento_mapa(estado, 1)
    assert estado.fin == ""
    assert estado.lock is False


def test_resolver_evento_mata_enemigo_bloquea():
    estado = _estado_con_evento()
    estado.E.hp = 0
    # Fin ya detectado antes de resolver: el lock de fin se mantiene.
    assert estado.lock is True
    resolver_evento_mapa(estado, 1)
    assert estado.fin == "w"
    assert estado.lock is True


# --- Píldoras de bolsa -------------------------------------------------------


def test_puede_usar_pildora_requiere_bolsa():
    estado = _estado_bolsa([])
    assert puede_usar_pildora(estado, "cur") is False


def test_puede_usar_pildora_guards():
    estado = _estado_bolsa(["cur"])
    assert puede_usar_pildora(estado, "cur") is True
    estado.lock = True
    assert puede_usar_pildora(estado, "cur") is False
    estado.lock = False
    estado.fin = "w"
    assert puede_usar_pildora(estado, "cur") is False
    estado.fin = ""
    estado.P.pildoras_usadas = 2
    assert puede_usar_pildora(estado, "cur") is False


def test_battle_pill_cur_cura_y_cuenta_uso():
    estado = _estado_bolsa(["cur"], hp=10)
    aplicar_pildora_bolsa(estado, "cur", stock_restante=1)
    assert estado.P.hp == 20  # 10 + 10
    assert estado.P.pildoras_usadas == 1
    assert "cur" in estado.P.bolsa_pildoras
    assert estado.logs[-1] == (
        f"Usas {PILDORAS['cur'].nombre} (1/2)"
    )


def test_battle_pill_agota_stock_la_retira_de_bolsa():
    estado = _estado_bolsa(["cur", "fue"])
    aplicar_pildora_bolsa(estado, "cur", stock_restante=0)
    assert "cur" not in estado.P.bolsa_pildoras
    assert "fue" in estado.P.bolsa_pildoras


def test_battle_pill_fue_mata_y_bloquea():
    estado = _estado_bolsa(["fue"], hp=30)
    estado.E.hp = 5
    aplicar_pildora_bolsa(estado, "fue", stock_restante=1)
    assert estado.E.hp <= 0
    assert estado.fin == "w"
    assert estado.lock is True


def test_battle_pill_qi_r_aumenta_qi():
    estado = _estado_bolsa(["qiR"])
    estado.P.qi = 1
    aplicar_pildora_bolsa(estado, "qiR", stock_restante=1)
    assert estado.P.qi == 5


def test_battle_pill_cng_congela_rivales():
    estado = _estado_bolsa(["cng"])
    enemigo = crear_carta_juego(next(iter(CARTAS)))
    estado.E.bd = [enemigo]
    aplicar_pildora_bolsa(estado, "cng", stock_restante=1)
    assert enemigo.congelada is True
