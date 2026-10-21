"""Lecturas del catálogo estático para la UI (solo lectura, sin estado).

Equivalente HTTP de `app.data`: toma los dataclasses inmutables del
catálogo y los convierte en resúmenes pydantic (`schemas/data.py`) para
que la interfaz no tenga que conocer las claves internas del JS.
No toca partidas ni disco; por eso no hay auto-save ni `SessionStore`.
"""

from __future__ import annotations

from app.data import (
    CARTAS,
    CARTAS_NEUTRALES,
    COLOR_RAREZA,
    COSTE_FORJA,
    ENEMIGOS,
    FINAL,
    ICONO_PILDKIND,
    MAZMORRAS,
    NIVELES,
    PILDORAS,
    PROLOGO,
    RAREZAS,
    REINOS,
    SECTA_DE_CARTA,
    SECTAS,
    TEXTO_FIN_NIVEL,
    TEXTO_INTRO_NIVEL,
    EnemigoCatalogo,
    rareza_de,
)
from app.data.bestias import BESTIAS_DOMADAS
from app.data.equipo import SLOT_NOMBRE, SLOTS, piezas_por_slot
from app.data.gacha import POOLS, RAREZAS_GACHA, TICKETS
from app.data.mercado import (
    PILDORAS_BASICAS_MERCADO,
    PRECIO_VENTA_MATERIAL,
    PUESTOS_MERCADO,
)
from app.data.misiones import (
    MISIONES_GENERALES,
    grupo_mision,
    misiones_secta,
)
from app.data.trajes import TRAJES
from app.engine import rules
from app.schemas.data import (
    AlquimiaResumen,
    BestiaResumen,
    CartaResumen,
    DetalleCartaResumen,
    EnemigoResumen,
    EquipoResumen,
    ForjaResumen,
    GachaResumen,
    HuecoEquipoResumen,
    LoteMaterialResumen,
    MazmorraResumen,
    MercadoResumen,
    MisionResumen,
    Narrativa,
    PiedadGachaResumen,
    PiezaEquipoResumen,
    PildoraResumen,
    PildoraVentaResumen,
    PoolGachaResumen,
    ProbabilidadesGachaResumen,
    PuestoMercadoResumen,
    RarezaGachaResumen,
    SectaResumen,
    TicketGachaResumen,
    TrajeResumen,
)


class DataService:
    """Casos de uso de solo lectura sobre los catálogos estáticos."""

    def sectas(self) -> list[SectaResumen]:
        """Las 10 sectas (6 jugables + 4 v47), en orden de `S` del JS."""
        return [
            SectaResumen(
                identificador=secta.identificador,
                nombre=secta.nombre,
                descripcion=secta.descripcion,
                cartas_iniciales=list(secta.cartas_iniciales),
            )
            for secta in SECTAS.values()
        ]

    def cartas(self) -> list[CartaResumen]:
        """Las 235 cartas del catálogo, en orden de definición (`C`)."""
        return [
            CartaResumen(
                identificador=carta.identificador,
                nombre=carta.nombre,
                tipo=carta.tipo.value,
                coste_qi=carta.coste_qi,
                ataque=carta.ataque,
                vida=carta.vida,
                rareza=rareza_de(carta),
                secta=SECTA_DE_CARTA.get(carta.identificador),
                es_neutral=carta.identificador in CARTAS_NEUTRALES,
                reliquia=carta.reliquia,
                es_abismo=rules.es_carta_abismo(carta),
                disipa=carta.disipa,
                descripcion=rules.descripcion_carta(carta),
            )
            for carta in CARTAS.values()
        ]

    def enemigos(self) -> list[EnemigoResumen]:
        """Los 90 enemigos aplanados, en orden (`CH` del JS)."""
        return [
            EnemigoResumen(
                indice=indice,
                nombre_enemigo=enemigo.nombre_enemigo,
                secta=enemigo.secta,
                nombre_nivel=enemigo.nombre_nivel,
                vida=enemigo.vida,
                dificultad=enemigo.dificultad,
                origen=origen_de(enemigo),
                frase_inicio=enemigo.frase_inicio,
                historia=enemigo.historia or "",
                indice_nivel=enemigo.indice_nivel,
                texto_habilidades=enemigo.texto_habilidades,
                rareza_recompensa=enemigo.rareza_recompensa,
            )
            for indice, enemigo in enumerate(ENEMIGOS)
        ]

    def mazmorras(self) -> list[MazmorraResumen]:
        """Las 6 mazmorras de recetas (`DG` del JS), en orden.

        Los pisos usan el offset 48 (tras los 48 enemigos de campaña).
        """
        offset = len(NIVELES) * 6
        return [
            MazmorraResumen(
                indice=indice,
                nombre=mazmorra.nombre,
                nivel=mazmorra.nivel,
                indice_receta=mazmorra.indice_receta,
                pista=mazmorra.pista,
                historia=mazmorra.historia,
                pisos=[offset + indice * 3 + fase for fase in range(3)],
                recetas=[
                    jefe.receta for jefe in mazmorra.jefes
                ],
            )
            for indice, mazmorra in enumerate(MAZMORRAS)
        ]

    def bestias(self) -> list[BestiaResumen]:
        """Las 8 bestias domables por jefe de nivel (`BEAST` del JS)."""
        return [
            BestiaResumen(
                identificador=bestia.identificador,
                nombre=bestia.nombre,
                ataque=bestia.ataque,
                vida=bestia.vida,
                indice_nivel=bestia.indice_nivel,
            )
            for bestia in BESTIAS_DOMADAS
        ]

    def equipo(self) -> EquipoResumen:
        """Catálogo de la pestaña `eqp`: huecos + piezas de la Herrería.

        El estado (forjado/equipado/usos) vive en el snapshot de la
        partida (`gr`/`eq`/`du`); esto es solo el catálogo.
        """
        piezas = [
            PiezaEquipoResumen(
                identificador=pieza.identificador,
                nombre=pieza.nombre,
                slot=pieza.slot,
                ataque=pieza.ataque,
                qi=pieza.qi,
                coste={
                    material.value: cantidad
                    for material, cantidad in pieza.coste.items()
                },
                desbloqueo=pieza.desbloqueo,
                revive=pieza.revive,
                usos=pieza.usos,
                secta=pieza.secta,
            )
            for pieza in piezas_por_slot()
        ]
        huecos = [
            HuecoEquipoResumen(clave=slot, nombre=SLOT_NOMBRE[slot])
            for slot in SLOTS
        ]
        return EquipoResumen(piezas=piezas, huecos=huecos)

    def trajes(self) -> list[TrajeResumen]:
        """Armario completo de los 10 trajes × 6 sectas (`OF` + `OAT`)."""
        return [
            TrajeResumen(
                secta=clave,
                indice=traje.indice,
                nombre=traje.nombre,
                umbral=traje.umbral,
                tipo=traje.tipo,
                valor=traje.valor,
                efecto=traje.efecto,
                descripcion=traje.descripcion,
            )
            for clave, lista in TRAJES.items()
            for traje in lista
        ]

    def misiones(self, clave_secta: str) -> list[MisionResumen]:
        """Misiones generales + de la secta (`[...GQ, ...missions]`).

        Args:
            clave_secta: secta del jugador (`sect`); determina las
                misiones propias y sus nombres de rival.
        """
        generales = [
            MisionResumen(
                identificador=mision.identificador,
                nombre=mision.nombre,
                descripcion=mision.descripcion,
                clave=mision.clave,
                meta=mision.meta,
                recompensa=mision.recompensa,
                grupo=grupo_mision(mision),
                es_general=True,
            )
            for mision in MISIONES_GENERALES
        ]
        propias = [
            MisionResumen(
                identificador=mision.identificador,
                nombre=mision.nombre,
                descripcion=mision.descripcion,
                clave=mision.clave,
                meta=mision.meta,
                recompensa=mision.recompensa,
                grupo=grupo_mision(mision),
                es_general=False,
            )
            for mision in misiones_secta(clave_secta)
        ]
        return generales + propias

    def narrativa(self) -> Narrativa:
        """Textos narrativos globales (prologo, reinos, niveles, final)."""
        return Narrativa(
            prologo=PROLOGO,
            final=FINAL,
            reinos=list(REINOS),
            textos_intro_nivel=list(TEXTO_INTRO_NIVEL),
            textos_fin_nivel=list(TEXTO_FIN_NIVEL),
            gradientes_nivel=[nivel.gradiente_color for nivel in NIVELES],
        )

    def alquimia(self) -> AlquimiaResumen:
        """Catálogo del tab de alquimia: píldoras + opciones de forja.

        Los costes se devuelven con las claves cortas del guardado
        (`'h'/'n'/'p'`), igual que `mat` en el snapshot, para que la UI
        los compare directamente con el inventario de la partida.
        """
        pildoras = [
            PildoraResumen(
                identificador=pildora.identificador,
                nombre=pildora.nombre,
                efecto=pildora.efecto,
                coste={
                    material.value: cantidad
                    for material, cantidad in pildora.coste.items()
                },
                es_combate=pildora.es_combate,
                icono=ICONO_PILDKIND.get(pildora.identificador, "gold"),
            )
            for pildora in PILDORAS.values()
        ]
        forja = [
            ForjaResumen(
                rareza=indice,
                nombre=RAREZAS[indice],
                color=COLOR_RAREZA[indice],
                coste={
                    material.value: cantidad
                    for material, cantidad in COSTE_FORJA[indice].items()
                },
            )
            for indice in range(len(RAREZAS))
        ]
        return AlquimiaResumen(pildoras=pildoras, forja=forja)

    def mercado(self) -> MercadoResumen:
        """Catálogo estático del tab de mercado (`MK`/`SELL`/`mkcList`).

        La vitrina de píldoras usa sólo las básicas (`mkcList` sin
        partida: `rec` vacío), porque las recetas aprendidas dependen
        de la partida y la UI filtra con el snapshot.
        """
        puestos = [
            PuestoMercadoResumen(
                identificador=puesto.identificador,
                vendedor=puesto.vendedor,
                frase=puesto.frase,
                lote=(
                    LoteMaterialResumen(
                        nombre=puesto.lote.nombre,
                        material=puesto.lote.material.value,
                        cantidad=puesto.lote.cantidad,
                        costo=puesto.lote.costo,
                    )
                    if puesto.lote
                    else None
                ),
            )
            for puesto in PUESTOS_MERCADO.values()
        ]
        precios_venta = {
            material.value: precio
            for material, precio in PRECIO_VENTA_MATERIAL.items()
        }
        vitrina = []
        for identificador in PILDORAS:
            if identificador in {"inm", "rar"}:
                continue
            if identificador not in PILDORAS_BASICAS_MERCADO:
                continue
            pildora = PILDORAS[identificador]
            vitrina.append(
                PildoraVentaResumen(
                    identificador=identificador,
                    nombre=pildora.nombre,
                    efecto=pildora.efecto,
                    tipo=rules.tipo_pildora_mercado(identificador),
                    precio=rules.precio_pildora_mercado(identificador),
                    icono=ICONO_PILDKIND.get(identificador, "gold"),
                    es_talisman=identificador == "tes",
                    receta_aprendida=False,
                )
            )
        return MercadoResumen(
            puestos=puestos,
            precios_venta=precios_venta,
            pildoras_en_venta=vitrina,
        )

    def detalle_carta(
        self, identificador: str, secta_elegida: str | None = None
    ) -> DetalleCartaResumen:
        """Detalle de carta para el modal del mercado (`mkDet`).

        Args:
            identificador: id de la carta en `C`.
            secta_elegida: secta del jugador (`schosen`); afecta a la
                línea de bloqueo de `obtencion`.

        Raises:
            KeyError: la carta no existe.
        """
        carta = CARTAS[identificador]
        secta = SECTA_DE_CARTA.get(identificador)
        secta_visible = (
            SECTAS[secta].nombre
            if secta and secta in SECTAS
            else "Neutral"
        )
        return DetalleCartaResumen(
            identificador=identificador,
            nombre=carta.nombre,
            tipo=carta.tipo.value,
            rareza=rareza_de(carta),
            secta_visible=secta_visible,
            coste_qi=carta.coste_qi,
            precio=rules.precio_compra(identificador),
            descripcion=rules.descripcion_carta(carta),
            estadisticas=rules.estadisticas_carta(carta),
            acumulacion=rules.tabla_acumulacion(carta),
            propiedades=[
                rules.PALABRAS_CLAVE[clave]
                for clave, atributo in rules.ATRIBUTO_PALABRA_CLAVE.items()
                if getattr(carta, atributo, None)
            ],
            obtencion=rules.obtencion_carta(identificador, secta_elegida),
            es_abismo=rules.es_carta_abismo(carta),
        )

    def gacha(self) -> GachaResumen:
        """Catálogo estático del gacha (`TICKET_TYPES`/`GACHA_POOLS`/
        `RARITY_INFO` de `js/14-gacha.js`)."""
        tickets = [
            TicketGachaResumen(
                identificador=ticket.identificador,
                nombre=ticket.nombre,
                descripcion=ticket.descripcion,
                icono=ticket.icono,
            )
            for ticket in TICKETS.values()
        ]
        pools = [
            PoolGachaResumen(
                clave=pool.clave,
                identificador=pool.identificador,
                nombre=pool.nombre,
                descripcion=pool.descripcion,
                tipo_ticket=pool.tipo_ticket,
                coste_por_tirada=pool.coste_por_tirada,
                probabilidades=ProbabilidadesGachaResumen(
                    common=pool.probabilidades.common,
                    rare=pool.probabilidades.rare,
                    epic=pool.probabilidades.epic,
                    legendary=pool.probabilidades.legendary,
                ),
                piedad=PiedadGachaResumen(
                    garantizado_raro_tras=pool.piedad.garantizado_raro_tras,
                    garantizado_epico_tras=pool.piedad.garantizado_epico_tras,
                    clave=pool.piedad.clave,
                ),
            )
            for pool in POOLS.values()
        ]
        rarezas = [
            RarezaGachaResumen(
                clave=rareza.clave,
                nombre=rareza.nombre,
                color=rareza.color,
                rareza_rn=rareza.rareza_rn,
            )
            for rareza in RAREZAS_GACHA.values()
        ]
        return GachaResumen(tickets=tickets, pools=pools, rarezas=rarezas)


def origen_de(enemigo: EnemigoCatalogo) -> str:
    """De dónde sale el combate: mazmorra > misión > nivel de campaña."""
    if enemigo.indice_mazmorra is not None:
        return "mazmorra"
    if enemigo.indice_mision is not None:
        return "mision"
    return "nivel"
