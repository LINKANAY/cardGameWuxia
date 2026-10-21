"""Misiones: progreso, reclamo y seguimiento (`claimQ`/`missionTrack`).

Referencia: js/06-contenido.js:104-126 (`GQ`/`missions`/`qv`/`claimQ`/
`missionGroup`/`missionTrack`). El progreso vive en
``Partida.misiones`` (``qs``) y las reclamadas en
``Partida.misiones_reclamadas`` (``qd``).
"""

from __future__ import annotations

import time

from app.core.errors import NotFoundError, ValidationError
from app.data import NOMBRE_MATERIAL
from app.data.misiones import (
    buscar_mision,
    grupo_mision,
    todas_las_misiones,
    valor_mision,
)
from app.data.pildoras import PILDORAS
from app.engine import rules
from app.engine.rng import GeneradorAleatorio
from app.engine.state import Partida
from app.state.session_store import SessionStore


class MisionService:
    """Casos de uso de misiones sobre una partida del slot."""

    def __init__(self, store: SessionStore):
        self._store = store

    @staticmethod
    def _sembrar_rng() -> GeneradorAleatorio:
        """Semilla por operación (patrón de los demás servicios)."""
        return GeneradorAleatorio(f"mis-{time.time_ns()}")

    def _asegurar_partida(self, slot: str) -> None:
        if not self._store.exists(slot):
            raise NotFoundError(f"No existe la partida del slot '{slot}'")

    def listar(self, slot: str) -> list[dict]:
        """Lista las misiones del jugador con progreso y estado.

        Returns:
            Lista de dicts con los campos de `MisionResumen` más
            ``progreso``, ``reclamada`` y ``lista`` (lista para
            reclamar: ``progreso >= meta`` y no reclamada).
        """
        self._asegurar_partida(slot)
        partida = self._store.get_or_create(slot)
        qs = partida.misiones
        qd = partida.misiones_reclamadas
        resultado = []
        for mision in todas_las_misiones(partida.secta):
            progreso = valor_mision(mision, qs)
            reclamada = bool(qd.get(mision.identificador))
            resultado.append(
                {
                    "identificador": mision.identificador,
                    "nombre": mision.nombre,
                    "descripcion": mision.descripcion,
                    "clave": mision.clave,
                    "meta": mision.meta,
                    "recompensa": mision.recompensa,
                    "progreso": progreso,
                    "reclamada": reclamada,
                    "lista": progreso >= mision.meta and not reclamada,
                    # `missionGroup` del JS: sin esto la UI (que agrupa
                    # por `grupo`) no pinta ninguna misión.
                    "grupo": grupo_mision(mision),
                    "es_general": mision.identificador.startswith("g"),
                }
            )
        return resultado

    def reclamar(self, slot: str, identificador: str) -> dict:
        """Reclama una misión cumplida (`claimQ` del JS).

        Aplica la recompensa: piedras (`s`), materiales (`h/n/p`),
        Talismán de Escape (`tes`), carta aleatoria de rareza (`card`),
        receta (`recipe`). Diseños (`design`) no aplican (Horno no
        portado).

        Returns:
            Dict con ``mensaje``, ``tes``/``carta``/``receta`` según lo
            obtenido, y el snapshot nuevo.

        Raises:
            ValidationError: si ya está reclamada o no está lista.
        """
        self._asegurar_partida(slot)
        partida = self._store.get_or_create(slot)
        mision = buscar_mision(partida.secta, identificador)
        if mision is None:
            raise ValidationError(
                f"No existe la misión '{identificador}'",
                code="mision_inexistente",
            )
        if partida.misiones_reclamadas.get(identificador):
            raise ValidationError(
                "La misión ya fue reclamada",
                code="mision_reclamada",
            )
        progreso = valor_mision(mision, partida.misiones)
        if progreso < mision.meta:
            raise ValidationError(
                "La misión aún no está completa",
                code="mision_incompleta",
            )
        rw = mision.recompensa
        obtenidos: list[str] = []

        def mutador(p: Partida) -> dict:
            if rw.get("s"):
                p.piedras_espirituales += rw["s"]
                obtenidos.append(f"+{rw['s']} piedras espirituales")
            for clave in ("h", "n", "p"):
                if rw.get(clave):
                    p.materiales[clave] = p.materiales.get(clave, 0) + rw[clave]
                    etiqueta = NOMBRE_MATERIAL[clave]
                    obtenidos.append(f"+{rw[clave]} {etiqueta}")
            tes = False
            if rw.get("tes"):
                p.pildoras["tes"] = p.pildoras.get("tes", 0) + 1
                tes = True
                obtenidos.append("Talismán de Escape")
            carta = None
            if rw.get("card") is not None:
                candidatas = rules.cartas_de_rareza(rw["card"])
                azar = self._sembrar_rng().random
                elegida = candidatas[int(azar() * len(candidatas))]
                resultado_carta = rules.agregar_carta_coleccion(
                    p.coleccion, p.materiales, elegida, p.misiones
                )
                carta = resultado_carta.nombre
                obtenidos.append(carta)
            receta = None
            if rw.get("recipe"):
                p.recetas[rw["recipe"]] = 1
                receta = PILDORAS[rw["recipe"]].nombre
                obtenidos.append(f"Receta: {receta}")
            p.misiones_reclamadas[identificador] = 1
            return {
                "tes": tes,
                "carta": carta,
                "receta": receta,
                "snapshot": p.a_dict(),
            }

        resumen = self._store.mutate(slot, mutador)
        mensaje = f"Misión cumplida: {mision.nombre}. Recibes: " + ", ".join(
            obtenidos
        )
        return {"mensaje": mensaje, **resumen}

    def seguir(self, slot: str, identificador: str) -> dict:
        """Activa/desactiva el seguimiento de una misión (`missionTrack`).

        El estado vive en ``qs.track`` (vacío = ninguna).

        Returns:
            Dict con ``track`` (id activo, posiblemente vacío) y el
            snapshot nuevo.
        """
        self._asegurar_partida(slot)
        partida = self._store.get_or_create(slot)
        if identificador and buscar_mision(
            partida.secta, identificador
        ) is None:
            raise ValidationError(
                f"No existe la misión '{identificador}'",
                code="mision_inexistente",
            )

        def mutador(p: Partida) -> dict:
            actual = p.misiones.get("track", "")
            p.misiones["track"] = (
                "" if actual == identificador else identificador
            )
            return {"track": p.misiones["track"], "snapshot": p.a_dict()}

        return self._store.mutate(slot, mutador)

    def tracker(self, slot: str) -> dict | None:
        """Misión seguida (`qs.track`) con progreso, o None si no hay."""
        self._asegurar_partida(slot)
        partida = self._store.get_or_create(slot)
        track = partida.misiones.get("track", "")
        if not track:
            return None
        mision = buscar_mision(partida.secta, track)
        if mision is None:
            return None
        return {
            "identificador": mision.identificador,
            "nombre": mision.nombre,
            "descripcion": mision.descripcion,
            "meta": mision.meta,
            "progreso": min(
                valor_mision(mision, partida.misiones), mision.meta
            ),
        }
