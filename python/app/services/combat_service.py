"""Casos de uso del combate — sesiones en memoria + campaña.

Puerto del flujo `begin`/`play`/`hit`/`act`/`endT`/`chk` del monolito
(`js/02-motor.js`) y de los efectos de campaña de `chk` (`js/02-motor.js:46`).

El estado de combate en curso **no** se persiste (igual que el monolito:
`P`/`E` viven en memoria de módulo). Sólo la `Partida` se auto-guarda
vía `SessionStore.mutate` cuando un evento de campaña lo exige.

El RNG de combate es un `GeneradorAleatorio` por sesión (semilla de
tiempo); el de campaña usa el mismo flujo para recompensas.
"""

from __future__ import annotations

import time

from app.core.errors import NotFoundError, ValidationError
from app.data.cartas import CARTAS
from app.data.niveles import ENEMIGOS
from app.data.pildoras import PILDORAS
from app.data.tipos import EnemigoCatalogo, TipoCarta
from app.engine import campaign, combat
from app.engine.combat import AccionEnemiga, EstadoCombate
from app.engine.rng import GeneradorAleatorio
from app.engine.rules import descripcion_carta
from app.engine.state import CartaJuego, Partida, crear_carta_juego
from app.services.horno_service import HornoService
from app.state.session_store import SessionStore


def _sembrar_rng() -> GeneradorAleatorio:
    """RNG de sesión con semilla de tiempo (`Math.random` en el JS)."""
    return GeneradorAleatorio(f"cb-{time.time_ns()}")


def _carta_snapshot(c: CartaJuego) -> dict:
    """Dict de una carta jugable para la UI."""
    d = c.definicion
    habilidad = c.habilidad_activa
    return {
        "id": c.identificador,
        "nombre": c.nombre,
        "coste": c.coste_qi,
        "tipo": d.tipo.value,
        "ataque": c.ataque,
        "vida": c.vida,
        "lista": c.lista_para_atacar,
        "provocar": d.provocar,
        "impetu": d.impetu,
        "robar_vida": bool(d.robar_vida),
        "crece": c.crece,
        "usada": c.usada,
        "bestia": c.es_bestia,
        "reliquia": d.reliquia,
        "dano_criatura": d.dano_criatura,
        "mejora_aliada": (
            {
                "ataque": d.mejorar_aliada.ataque,
                "vida": d.mejorar_aliada.vida,
            }
            if d.mejorar_aliada
            else None
        ),
        "habilidad": (
            {
                "coste": habilidad.coste_qi,
                "efecto": habilidad.tipo.value,
                "valor": habilidad.valor,
                "descripcion": habilidad.descripcion,
            }
            if habilidad
            else None
        ),
        "formacion": (
            {
                "pa": d.mejora_ataque_al_trazar or 0,
                "ph": d.mejora_vida_al_trazar or 0,
                "ts": (
                    [
                        d.efecto_inicio_turno[0].value,
                        d.efecto_inicio_turno[1],
                    ]
                    if d.efecto_inicio_turno
                    else None
                ),
            }
            if d.tipo in (TipoCarta.FORMACION, TipoCarta.RUNA)
            else None
        ),
        "descripcion": descripcion_carta(d),
    }


def _lado_snapshot(lado) -> dict:
    """Dict de un lado del combate para la UI."""
    return {
        "nombre": lado.nombre,
        "hp": lado.hp,
        "mx": lado.mx,
        "qi": lado.qi,
        "mq": lado.mq,
        "cap": lado.cap,
        "sh": lado.sh,
        "mazo": len(lado.dk),
        "cartas_mazo": [_carta_snapshot(c) for c in lado.dk],
        "mano": [_carta_snapshot(c) for c in lado.hand],
        "tablero": [_carta_snapshot(c) for c in lado.bd],
        "vacio": [_carta_snapshot(c) for c in lado.vd],
        "turnos": lado.numero_turno or lado.turnos_enemigo,
        "pouch": list(lado.bolsa_pildoras),
        "usos": lado.pildoras_usadas,
        # --- formaciones / runas (`fmH`/`bdg` de js/04-mazos-formaciones.js) ---
        "fm": (
            {
                "id": lado.fm.identificador,
                "nombre": lado.fm.nombre,
                "pa": lado.fm.ataque_fisico,
                "ph": lado.fm.vida_fisica,
                "desc": descripcion_carta(CARTAS[lado.fm.identificador]),
            }
            if lado.fm
            else None
        ),
        "rn": [
            {
                "id": r.identificador,
                "nombre": r.nombre,
                "du": r.duracion_restante,
                "desc": descripcion_carta(CARTAS[r.identificador]),
            }
            for r in lado.rn
        ],
        "atkb": lado.atkb,
        "bo": bool(lado.bo),
        "opa": lado.opa,
        "oph": lado.oph,
        "salvavidas": bool(lado.esc or lado.revivir or lado.artefacto),
    }


def _evento_snapshot(ev) -> dict:
    return {"tipo": ev.tipo, "datos": ev.datos}


def _accion_snapshot(a: AccionEnemiga) -> dict:
    return {
        "tipo": a.tipo,
        "carta": a.carta,
        "nombre": a.nombre,
        "objetivo_nombre": a.objetivo_nombre,
        "habla": a.habla,
        "datos": a.datos,
    }


class CombatService:
    """Orquesta un combate activo por slot y aplica campaña al terminar."""

    def __init__(self, store: SessionStore):
        self._store = store
        self._combates: dict[str, EstadoCombate] = {}
        self._campaña_pendiente: dict[str, list] = {}
        # Recompensas de la última victoria aún sin elegir (`rw` en js/02-motor.js:46).
        self._rw_pendiente: dict[str, list[str]] = {}

    def _asegurar_partida(self, slot: str) -> None:
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    def _estado(self, slot: str) -> EstadoCombate:
        estado = self._combates.get(slot)
        if estado is None:
            raise ValidationError(
                "No hay combate en curso en este slot",
                code="sin_combate",
            )
        return estado

    @staticmethod
    def _acciones_permitidas(estado: EstadoCombate) -> None:
        """Guard de acciones del jugador (`pl`/`go` de js/07-campamento.js).

        Bloquea mientras haya un evento de mapa pendiente (`lock`), combate
        terminado o modales de descarte/recuperación (`ED`/`VP`/`PD`).
        """
        if (
            estado.lock
            or estado.fin
            or estado.pd
            or estado.vp_n
            or estado.ed
        ):
            raise ValidationError(
                "El combate no permite acciones ahora",
                code="combate_bloqueado",
            )

    def _enemigo(self, indice: int) -> EnemigoCatalogo:
        if indice < 0 or indice >= len(ENEMIGOS):
            raise ValidationError(
                f"Enemigo desconocido: {indice}", code="enemigo_invalido"
            )
        return ENEMIGOS[indice]

    def _pildoras_inicio(
        self, partida: Partida, pildoras: list[str]
    ) -> list[str]:
        """Valida y consume píldoras de inicio (`eqp` + `pil[k]--`)."""
        elegidas: list[str] = []
        for ident in pildoras:
            if ident not in PILDORAS:
                raise ValidationError(
                    f"Píldora desconocida: '{ident}'",
                    code="pildora_desconocida",
                )
            if partida.pildoras.get(ident, 0) <= 0:
                raise ValidationError(
                    f"No tienes píldoras '{ident}'",
                    code="pildoras_insuficientes",
                )
            partida.pildoras[ident] -= 1
            if partida.pildoras[ident] <= 0:
                del partida.pildoras[ident]
            elegidas.append(ident)
        return elegidas

    def snapshot(self, slot: str) -> dict:
        """Estado del combate activo, o `None` si no hay."""
        estado = self._combates.get(slot)
        if estado is None:
            return {"activo": False}
        return {
            "activo": True,
            "fin": estado.fin,
            "lock": estado.lock,
            "logs": list(estado.logs),
            "jugador": _lado_snapshot(estado.P),
            "enemigo": _lado_snapshot(estado.E),
            "indice_enemigo": estado.indice_enemigo,
            "pd": [_carta_snapshot(c) for c in estado.pd],
            "vp_n": estado.vp_n,
            "ed": estado.ed,
            "ec": estado.ec,
            "sel": estado.sel,
            "tg": estado.tg,
            "ev": (
                {
                    "nombre": estado.ev.nombre,
                    "texto": estado.ev.texto,
                    "opciones": [o.etiqueta for o in estado.ev.opciones],
                }
                if estado.ev
                else None
            ),
            "eventos": [_evento_snapshot(e) for e in estado.eventos],
            "pildoras_stock": dict(
                self._store.get_or_create(slot).pildoras
            ),
            "vida_hroe_max": combat.vida_heroe_max(
                self._store.get_or_create(slot).nivel_reino
            )
            if estado.P.es_jugador
            else None,
        }

    def iniciar(
        self,
        slot: str,
        indice_enemigo: int,
        pildoras: list[str] | None = None,
        bolsa: list[str] | None = None,
    ) -> dict:
        """Empieza un combate (`begin(k)`).

        Args:
            slot: slot de la partida.
            indice_enemigo: índice en `ENEMIGOS`.
            pildoras: píldoras de inicio (`eqp`); se consumen al empezar.
            bolsa: píldoras de combate (`eqpB`); se consumen al usarse.

        Returns:
            Snapshot del combate + `campaña` pendiente (vacía al inicio).
        """
        self._asegurar_partida(slot)
        enemigo = self._enemigo(indice_enemigo)
        rng = _sembrar_rng()
        pildoras = pildoras or []
        bolsa = bolsa or []
        self._validar_pildoras(slot, pildoras, consumir=False)
        self._validar_pildoras(slot, bolsa, consumir=False)

        def preparar(partida: Partida):
            elegidas = self._pildoras_inicio(partida, pildoras)
            bolsa_elegida = [
                k
                for k in bolsa
                if partida.pildoras.get(k, 0) > 0
            ]
            mazo_j = campaign.mazo_para_combate(partida, rng.random)
            mazo_e = campaign.mazo_enemigo(enemigo, rng.random)
            bestia = None
            if partida.bestia_equipada:
                try:
                    bestia = crear_carta_juego(partida.bestia_equipada)
                except KeyError:
                    bestia = None
            return (
                elegidas,
                bolsa_elegida,
                mazo_j,
                mazo_e,
                bestia,
                partida.vida_hroe,
                partida.nivel_reino,
                dict(partida.equipado),
                dict(partida.equipo_guardado),
                dict(partida.usos_equipo),
                dict(partida.atuendo),
                partida.secta,
                list(partida.victorias),
            )

        (
            elegidas,
            bolsa_elegida,
            mazo_j,
            mazo_e,
            bestia,
            vida,
            reino,
            equipado,
            equipo,
            usos,
            atuendo,
            secta,
            victorias,
        ) = self._store.mutate(slot, preparar)
        estado = combat.iniciar_combate(
            enemigo=enemigo,
            indice_enemigo=indice_enemigo,
            reino=reino,
            vida_hroe=vida,
            mazo_jugador=mazo_j,
            mazo_enemigo=mazo_e,
            pildoras_inicio=elegidas,
            bolsa=bolsa_elegida,
            rng=rng,
            equipar_bestia_jugador=bestia,
            equipado=equipado,
            equipo_guardado=equipo,
            usos_equipo=usos,
            atuendo=atuendo,
            secta=secta,
            victorias=victorias,
        )
        self._combates[slot] = estado
        campaña = self._consumir_eventos(slot, estado)
        return {
            "combate": self.snapshot(slot),
            "campaña": campaña,
        }

    def _validar_pildoras(
        self, slot: str, pildoras: list[str], *, consumir: bool
    ) -> None:
        """Valida ids y stock de píldoras sin consumir nada por defecto.

        Args:
            slot: partida dueña del inventario.
            pildoras: ids a validar.
            consumir: si True, descuenta una unidad de cada una (ya
                validadas) — usado por las píldoras de inicio.
        """
        if not pildoras:
            return
        partida = self._store.get_or_create(slot)
        for ident in pildoras:
            if ident not in PILDORAS:
                raise ValidationError(
                    f"Píldora desconocida: '{ident}'",
                    code="pildora_desconocida",
                )
            if partida.pildoras.get(ident, 0) <= 0:
                raise ValidationError(
                    f"No tienes píldoras '{ident}'",
                    code="pildoras_insuficientes",
                )
        if consumir:
            for ident in pildoras:
                partida.pildoras[ident] -= 1
                if partida.pildoras[ident] <= 0:
                    del partida.pildoras[ident]

    def jugar(
        self, slot: str, indice: int, objetivo: int | None = None
    ) -> dict:
        """Juega una carta de mano (`play`)."""
        estado = self._estado(slot)
        self._acciones_permitidas(estado)
        ok = combat.jugar_carta(
            estado, estado.P, estado.E, indice, objetivo
        )
        if not ok:
            raise ValidationError(
                "No se puede jugar esa carta", code="jugada_invalida"
            )
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def atacar(self, slot: str, atacante: int, objetivo: int) -> dict:
        """Ataca con una criatura (`hit`). Objetivo -1 = héroe."""
        estado = self._estado(slot)
        self._acciones_permitidas(estado)
        if atacante >= len(estado.P.bd):
            raise ValidationError(
                "Criatura atacante inválida", code="atacante_invalido"
            )
        if objetivo >= len(estado.E.bd):
            raise ValidationError(
                "Criatura objetivo inválida", code="objetivo_invalido"
            )
        criatura = estado.P.bd[atacante]
        combat.atacar(estado, estado.P, estado.E, criatura, objetivo)
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def activar(self, slot: str, indice: int) -> dict:
        """Activa la habilidad de una criatura (`act`)."""
        estado = self._estado(slot)
        self._acciones_permitidas(estado)
        if indice >= len(estado.P.bd):
            raise ValidationError(
                "Criatura inválida", code="criatura_invalida"
            )
        ok = combat.activar_habilidad(estado, estado.P, estado.E, indice)
        if not ok:
            raise ValidationError(
                "No se puede activar esa habilidad",
                code="habilidad_invalida",
            )
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def fin_turno(self, slot: str, forzar: bool = False) -> dict:
        """Cierra el turno y ejecuta la IA enemiga (`endT`)."""
        estado = self._estado(slot)
        resultado = combat.confirmar_cierre(estado, forzar=forzar)
        if resultado != "ok":
            raise ValidationError(
                f"No se puede cerrar el turno ({resultado})",
                code=f"cierre_{resultado}",
            )
        acciones = combat.fin_turno_enemigo(estado, forzar=forzar)
        campaña = self._consumir_eventos(slot, estado)
        return {
            "combate": self.snapshot(slot),
            "acciones": [_accion_snapshot(a) for a in acciones],
            "campaña": campaña,
        }

    def descartar_exceso(self, slot: str, indice: int) -> dict:
        """Descarta una carta por exceso de mano (`ED` + `edisc`).

        Al llegar a 0 descartes continúa el turno con la IA enemiga,
        igual que `edisc` de js/07-campamento.js:84 (`endT(true)`).
        """
        estado = self._estado(slot)
        if not combat.descartar_exceso_jugador(estado, indice):
            raise ValidationError(
                "No se puede descartar esa carta",
                code="descarte_invalido",
            )
        campaña = self._consumir_eventos(slot, estado)
        acciones: list[AccionEnemiga] = []
        if estado.ed <= 0:
            acciones = combat.fin_turno_enemigo(estado, forzar=True)
            campaña += self._consumir_eventos(slot, estado)
        resultado: dict = {
            "combate": self.snapshot(slot),
            "campaña": campaña,
        }
        if acciones:
            resultado["acciones"] = [_accion_snapshot(a) for a in acciones]
        return resultado

    def cancelar_exceso(self, slot: str) -> dict:
        """Cancela el exceso de mano y deja seguir jugando (`ED = 0`)."""
        estado = self._estado(slot)
        if not combat.cancelar_exceso(estado):
            raise ValidationError(
                "No hay exceso de mano pendiente",
                code="exceso_inexistente",
            )
        return {"combate": self.snapshot(slot), "campaña": []}

    def elegir_vacio(self, slot: str, indice: int) -> dict:
        """Recupera una carta del Agujero Negro (`vpick`)."""
        estado = self._estado(slot)
        if not combat.recuperar_del_vacio(estado, indice):
            raise ValidationError(
                "No se puede recuperar esa carta",
                code="vacio_invalido",
            )
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def cancelar_vacio(self, slot: str) -> dict:
        """Cancela la recuperación del Agujero Negro (`vdone` sin pick)."""
        estado = self._estado(slot)
        combat.cancelar_vacio(estado)
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def resolver_evento(self, slot: str, opcion: int) -> dict:
        """Elige una opción del evento de mapa activo (`evPick`)."""
        estado = self._estado(slot)
        if not combat.resolver_evento_mapa(estado, opcion):
            raise ValidationError(
                "No hay evento de mapa pendiente con esa opción",
                code="evento_invalido",
            )
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def usar_pildora(self, slot: str, ident: str) -> dict:
        """Usa una píldora de la bolsa durante el combate (`usePill`)."""
        estado = self._estado(slot)
        if not combat.puede_usar_pildora(estado, ident):
            raise ValidationError(
                "No puedes usar esa píldora ahora",
                code="pildora_invalida",
            )
        stock = self._store.get_or_create(slot).pildoras.get(ident, 0)
        if stock <= 0:
            raise ValidationError(
                f"No tienes píldoras '{ident}'",
                code="pildoras_insuficientes",
            )

        def descontar(partida: Partida) -> None:
            partida.pildoras[ident] -= 1
            if partida.pildoras[ident] <= 0:
                del partida.pildoras[ident]

        self._store.mutate(slot, descontar)
        combat.aplicar_pildora_bolsa(estado, ident, stock - 1)
        campaña = self._consumir_eventos(slot, estado)
        return {"combate": self.snapshot(slot), "campaña": campaña}

    def abandonar(self, slot: str) -> dict:
        """Abandona el combate sin efectos de campaña (como escape)."""
        estado = self._estado(slot)
        estado.fin = "f"
        campaña = self._consumir_eventos(slot, estado)
        del self._combates[slot]
        return {"fin": "f", "campaña": campaña}

    def cerrar(self, slot: str) -> dict:
        """Libera la sesión de combate tras un fin ya aplicado."""
        estado = self._estado(slot)
        if not estado.fin:
            raise ValidationError(
                "El combate aún no ha terminado",
                code="combate_en_curso",
            )
        del self._combates[slot]
        return {"fin": estado.fin}

    def reclamar(self, slot: str, indice: int) -> dict:
        """Elige UNA de las 3 recompensas pendientes (`claim`).

        Referencia: js/06-contenido.js:206.
        `col[id] = min(3, (col[id] || 0) + 1)`. No requiere combate activo:
        puede reclamarse tras cerrar la sesión de combate.
        """
        self._asegurar_partida(slot)
        pendientes = self._rw_pendiente.get(slot) or []
        if not pendientes:
            raise ValidationError(
                "No hay recompensas pendientes para reclamar",
                code="recompensa_inexistente",
            )
        if indice < 0 or indice >= len(pendientes):
            raise ValidationError(
                "Índice de recompensa fuera de rango",
                code="recompensa_inexistente",
            )
        id_carta = pendientes[indice]

        def mutador(partida: Partida) -> dict:
            copias = min(3, partida.coleccion.get(id_carta, 0) + 1)
            partida.coleccion[id_carta] = copias
            return {"carta": id_carta, "copias": copias}

        resumen = self._store.mutate(slot, mutador)
        self._rw_pendiente.pop(slot, None)
        return {
            "carta": id_carta,
            "copias": resumen["copias"],
            "recompensas": [],
        }

    def _consumir_eventos(self, slot: str, estado: EstadoCombate) -> list:
        """Aplica eventos de campaña del motor y limpia la cola."""
        eventos = list(estado.eventos)
        estado.eventos.clear()
        resumen: list[dict] = []
        for ev in eventos:
            if ev.tipo == "victoria":
                resumen.append(self._aplicar_victoria(slot, estado, ev))
            elif ev.tipo == "muerte":
                resumen.append(self._aplicar_muerte(slot, estado, ev))
            elif ev.tipo == "escape":
                resumen.append({"tipo": "escape"})
            elif ev.tipo == "revivir":
                resumen.append({"tipo": "revivir", **ev.datos})
            elif ev.tipo == "salvar_artefacto":
                resumen.append(
                    self._aplicar_artefacto(slot, ev.datos.get("artefacto"))
                )
            else:
                resumen.append({"tipo": ev.tipo, **ev.datos})
        return resumen

    def _aplicar_victoria(
        self, slot: str, estado: EstadoCombate, ev
    ) -> dict:
        enemigo = estado.enemigo
        if enemigo is None or estado.indice_enemigo is None:
            return {"tipo": "victoria", "indice": None}
        indice = estado.indice_enemigo
        vida = estado.P.hp if estado.P.hp > 0 else None
        rng = estado.rng or _sembrar_rng()

        def mutador(partida: Partida) -> dict:
            return campaign.aplicar_victoria(
                partida, enemigo, indice, vida, rng.random
            )

        campaña = self._store.mutate(slot, mutador)
        # `rw = genRw(k)` de js/02-motor.js:46: queda pendiente de `claim(i)`.
        self._rw_pendiente[slot] = list(campaña.get("recompensas") or [])
        # Botín del Horno (el JS envuelve `notifyWin` en js/11-horno.js:551:
        # hierbas por victoria, bonus de jefe si `ch.d >= 4`).
        dificultad = enemigo.dificultad or 0
        botin = HornoService(self._store).botin_victoria(
            slot,
            dificultad,
            es_jefe=dificultad >= 4
            or campaign.es_jefe_final_mazmorra(indice),
        )
        return {"tipo": "victoria", **campaña, "botin": botin}

    def _aplicar_muerte(
        self, slot: str, estado: EstadoCombate, ev
    ) -> dict:
        enemigo = estado.enemigo

        def mutador(partida: Partida) -> dict:
            return campaign.muerte_permanente(partida, enemigo)

        resumen = self._store.mutate(slot, mutador)
        return {"tipo": "muerte", **resumen}

    def _aplicar_artefacto(self, slot: str, artefacto: str | None) -> dict:
        """Descuenta un uso del artefacto que salvó al héroe (`du`)."""

        def mutador(partida: Partida) -> dict:
            if not artefacto:
                return {"tipo": "salvar_artefacto", "artefacto": None}
            restantes = max(
                0, partida.usos_equipo.get(artefacto, 0) - 1
            )
            partida.usos_equipo[artefacto] = restantes
            roto = restantes <= 0
            if roto:
                partida.equipo_guardado.pop(artefacto, None)
                for slot_eq in list(partida.equipado):
                    if partida.equipado[slot_eq] == artefacto:
                        partida.equipado[slot_eq] = None
            return {
                "tipo": "salvar_artefacto",
                "artefacto": artefacto,
                "restantes": restantes,
                "roto": roto,
            }

        return self._store.mutate(slot, mutador)
