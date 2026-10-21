"""Schemas de catálogo para la UI (solo lectura).

Son resúmenes legibles para pintar la nueva interfaz; NO son el formato
de guardado. Las claves identificadoras (`'esp'`, `'cf'`…) se
conservan como en todo el proyecto.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SectaResumen(BaseModel):
    """Secta jugable para la puerta de selección (`S[id]` del JS).

    Atributos:
        identificador: clave corta (`'esp'`, `'lot'`…).
        nombre: nombre visible.
        descripcion: descripción de estilo (`i`).
        cartas_iniciales: las 5 cartas base del mazo (`l`).
    """

    identificador: str
    nombre: str
    descripcion: str
    cartas_iniciales: list[str]


class CartaResumen(BaseModel):
    """Ficha breve de carta para la UI (`C[id]` del JS, resumida).

    Atributos:
        identificador: clave corta del catálogo.
        nombre: nombre visible.
        tipo: código de `TipoCarta` (`t`: C/T/P/F/R).
        coste_qi: coste para jugarla (`c`).
        ataque: ataque inicial de criatura (`A`), si lo tiene.
        vida: vida inicial de criatura (`H`), si la tiene.
        rareza: rareza calculada (`rareza_de`, tabla por coste).
        secta: clave del mapa `SC` (incluye `'neu'` para los
            coleccionables sin secta); None si no aparece en `SC`.
        es_neutral: True si está en la lista `NEU` (siempre usables
            hasta en 3 copias, como las cartas base de la secta).
        reliquia: no aparece en el mercado ni en recompensas
            normales (`lk`).
        es_abismo: carta del Abismo (`vb`/`vs`); una vez obtenida
            desaparece del mercado (`vzOk`).
        descripcion: líneas de efectos (`descH`, texto plano); vacía
            si la carta no tiene efectos que mostrar.
    """

    identificador: str
    nombre: str
    tipo: str
    coste_qi: int
    ataque: int | None
    vida: int | None
    rareza: int
    secta: str | None
    es_neutral: bool = False
    reliquia: bool = False
    es_abismo: bool = False
    #: Disipa formaciones y runas rivales (`dsp`).
    disipa: bool = False
    descripcion: list[str] = Field(default_factory=list)


class EnemigoResumen(BaseModel):
    """Ficha breve de enemigo (`CH[k]` del JS, resumida).

    Atributos:
        indice: posición global en ENEMIGOS (clave de `wins`).
        nombre_enemigo: nombre del oponente.
        secta: secta/estilo del oponente.
        nombre_nivel: título del nivel o misión donde aparece.
        vida: vida calculada.
        dificultad: índice de dificultad 0–5.
        origen: de dónde sale el combate (`nivel` | `mazmorra` | `mision`).
        frase_inicio: frase al presentarse.
        historia: historia propia (`c.story`), vacía si usa la del nivel.
        indice_nivel: índice de nivel (`li`).
        texto_habilidades: descripción de habilidades (`c.r`).
        rareza_recompensa: rareza de recompensa (`rw`), si la tiene;
            el catálogo de la Formaciones la usa en «Premio de combate».
    """

    indice: int
    nombre_enemigo: str
    secta: str
    nombre_nivel: str
    vida: int
    dificultad: int
    origen: str
    frase_inicio: str
    #: Historia propia del enemigo (`c.story`); vacía si no tiene.
    historia: str = ""
    #: Índice de nivel (`li`), para escalar daño y narrativa.
    indice_nivel: int
    #: Descripción de habilidades del oponente (`c.r`).
    texto_habilidades: str
    #: Rareza de recompensa (`rw`); None si el enemigo no suelta cartas.
    rareza_recompensa: int | None = None


class Narrativa(BaseModel):
    """Textos narrativos globales (splash, campaña y final).

    Atributos:
        prologo: texto de introducción (`PROLOGO`).
        final: texto de victoria final (`FINAL`).
        reinos: nombres de los 15 reinos (`REINOS`).
        textos_intro_nivel: texto al entrar a cada nivel (`st`).
        textos_fin_nivel: texto al terminar cada nivel (`en`).
        gradientes_nivel: par `[oscuro, claro]` de cielo por nivel
            (`LV[i].sky`), para la escena de la intro de combate.
    """

    prologo: str
    final: str
    reinos: list[str]
    textos_intro_nivel: list[str]
    textos_fin_nivel: list[str]
    gradientes_nivel: list[tuple[str, str]]


class PildoraResumen(BaseModel):
    """Píldora del catálogo para pintar el tab de alquimia (`PIL`).

    Atributos:
        identificador: clave corta (`'vit'`, `'cur'`…).
        nombre: nombre visible (`n`).
        efecto: descripción del efecto (`t`).
        coste: materiales para elaborarla, con las claves cortas del
            guardado `'h'/'n'/'p'` (`c`; los 0 se omiten, como en JS).
        es_combate: True si es de bolsa de combate (flag `b`).
        icono: clase de icono del monolito (`PILK[k]`; `'tal'` dibuja
            el glifo 符 en vez de la poción).
    """

    identificador: str
    nombre: str
    efecto: str
    coste: dict[str, int]
    es_combate: bool
    icono: str


class ForjaResumen(BaseModel):
    """Opción de forja por rareza (`RN[r]`/`RC[r]`/`FC[r]` del JS).

    Atributos:
        rareza: índice 0–5.
        nombre: nombre de la rareza (`RN`).
        color: color hex de la rareza (`RC`).
        coste: materiales para forjar una carta de esa rareza, con
            claves cortas `'h'/'n'/'p'` (`FC[r]`).
    """

    rareza: int
    nombre: str
    color: str
    coste: dict[str, int]


class AlquimiaResumen(BaseModel):
    """Catálogo completo del tab de alquimia.

    Atributos:
        pildoras: las 27 píldoras, en orden del `PIL` del JS.
        forja: las 6 opciones de forja (una por rareza).
    """

    pildoras: list[PildoraResumen]
    forja: list[ForjaResumen]


class LoteMaterialResumen(BaseModel):
    """Lote de material de un puesto del mercado (`MK[k][2]`).

    Atributos:
        nombre: nombre del lote (`n`).
        material: clave corta del material (`m`: `'h'/'n'/'p'`).
        cantidad: unidades del lote (`q`).
        costo: precio en piedras espirituales (`c`).
    """

    nombre: str
    material: str
    cantidad: int
    costo: int


class PuestoMercadoResumen(BaseModel):
    """Puesto del mercado (`MK[k]` del JS, resumido).

    Atributos:
        identificador: clave del puesto (`'esp'`, `'neu'`…).
        vendedor: nombre del NPC (`M[0]`).
        frase: frase del puesto (`M[1]`).
        lote: lote de materiales (`M[2]`; None en el General).
    """

    identificador: str
    vendedor: str
    frase: str
    lote: LoteMaterialResumen | None = None


class PildoraVentaResumen(BaseModel):
    """Píldora/talismán de la vitrina del puesto General (`mkcList`).

    Atributos:
        identificador: clave en `PILDORAS`.
        nombre: nombre visible.
        efecto: descripción del efecto.
        tipo: etiqueta de tipo (`pillKind`).
        precio: precio de compra (`mkcPrice`).
        icono: clase de icono del monolito.
        es_talisman: True si es el talismán de escape (`'tes'`).
        receta_aprendida: True si la receta ya se conoce (`rec`).
    """

    identificador: str
    nombre: str
    efecto: str
    tipo: str
    precio: int
    icono: str
    es_talisman: bool = False
    receta_aprendida: bool = False


class MercadoResumen(BaseModel):
    """Catálogo estático del tab de mercado.

    Atributos:
        puestos: los 11 puestos, en orden del `MK` del JS.
        precios_venta: precio de venta de 1 unidad por material
            (`SELL`), con claves cortas `'h'/'n'/'p'`.
        pildoras_en_venta: vitrina del puesto General (depende de las
            recetas conocidas; aquí se calcula sin partida: básicas).
    """

    puestos: list[PuestoMercadoResumen]
    precios_venta: dict[str, int]
    pildoras_en_venta: list[PildoraVentaResumen]


class DetalleCartaResumen(BaseModel):
    """Detalle de carta para el modal del mercado (`mkDet`).

    Atributos:
        identificador: id de la carta.
        nombre: nombre visible.
        tipo: código de tipo (`t`).
        rareza: rareza calculada.
        secta_visible: nombre de la secta visible (`S[SX(id)].n`) o
            `'Neutral'`.
        coste_qi: coste para jugarla.
        precio: precio de compra (`PR(id)`).
        descripcion: líneas de efectos (`descH`, texto plano).
        estadisticas: filas «Estadísticas» (`PROP` + extras).
        acumulacion: filas de la tabla de acumulación (`stkUp`); None
            si no se acumula (no-criatura o bestia).
        propiedades: etiquetas de palabras clave presentes (`KI`).
        obtencion: líneas de obtención (`howGet`).
        es_abismo: True si es carta del Abismo (`vb`/`vs`).
    """

    identificador: str
    nombre: str
    tipo: str
    rareza: int
    secta_visible: str
    coste_qi: int
    precio: int
    descripcion: list[str]
    estadisticas: list[tuple[str, str]]
    acumulacion: list[dict] | None = None
    propiedades: list[str]
    obtencion: list[str]
    es_abismo: bool = False


class TicketGachaResumen(BaseModel):
    """Reliquia resonante del gacha (`TICKET_TYPES` del JS).

    Atributos:
        identificador: clave de inventario (`ticket_common`/
            `ticket_premium`).
        nombre: nombre visible.
        descripcion: lore de la reliquia.
        icono: emoji del monolito.
    """

    identificador: str
    nombre: str
    descripcion: str
    icono: str


class ProbabilidadesGachaResumen(BaseModel):
    """Distribución de rarezas de un pool (`probabilities` del JS).

    Atributos:
        common: % de Común.
        rare: % de Raro.
        epic: % de Épico.
        legendary: % de Legendario.
    """

    common: float
    rare: float
    epic: float
    legendary: float


class PiedadGachaResumen(BaseModel):
    """Garantías de un pool (`pitySystem` del JS).

    Atributos:
        garantizado_raro_tras: declarado pero no usado por `draw`.
        garantizado_epico_tras: tiradas sin épico tras las que el
            siguiente es Épico garantizado.
        clave: clave del contador en `gp`.
    """

    garantizado_raro_tras: int
    garantizado_epico_tras: int
    clave: str


class PoolGachaResumen(BaseModel):
    """Pool de invocación (`GACHA_POOLS[poolKey]` del JS).

    Atributos:
        clave: clave del pool en la API (`'STANDARD'`/`'PREMIUM'`).
        identificador: id largo (`pool_standard`/`pool_premium`).
        nombre: nombre visible del pool.
        descripcion: lore del pool.
        tipo_ticket: id del ticket que consume.
        coste_por_tirada: tickets por invocación.
        probabilidades: distribución por rareza.
        piedad: garantías del pool.
    """

    clave: str
    identificador: str
    nombre: str
    descripcion: str
    tipo_ticket: str
    coste_por_tirada: int
    probabilidades: ProbabilidadesGachaResumen
    piedad: PiedadGachaResumen


class RarezaGachaResumen(BaseModel):
    """Metadatos visuales de una rareza de gacha (`RARITY_INFO`).

    Atributos:
        clave: `'common'`/`'rare'`/`'epic'`/`'legendary'`.
        nombre: nombre visible.
        color: color hex del monolito.
        rareza_rn: rareza del catálogo de cartas equivalente.
    """

    clave: str
    nombre: str
    color: str
    rareza_rn: int


class GachaResumen(BaseModel):
    """Catálogo estático del gacha para pintar el modal.

    Atributos:
        tickets: las 2 reliquias resonantes.
        pools: los 2 pools de invocación.
        rarezas: metadatos de las 4 rarezas de gacha.
    """

    tickets: list[TicketGachaResumen]
    pools: list[PoolGachaResumen]
    rarezas: list[RarezaGachaResumen]


class MazmorraResumen(BaseModel):
    """Mazmorra de recetas para el tab `dgn` (`DG` del JS).

    Atributos:
        indice: posición en `MAZMORRAS` (0-based).
        nombre: título (`n`).
        nivel: índice del nivel del que cuelga (`li`); el jefe del
            nivel `(li)` la desbloquea (`u = li*6-1`).
        indice_receta: índice de la receta que enseña (`u` del JS —
            aquí se conserva el nombre del campo portado).
        pista: texto de pista (`hint`).
        historia: narrativa (`st`).
        pisos: índices globales de los 3 combates (`48 + i*3 + f`).
        recetas: id de la receta que revela cada piso (`rcp` de cada
            jefe; None si no revela receta).
    """

    indice: int
    nombre: str
    nivel: int
    indice_receta: int
    pista: str
    historia: str
    pisos: list[int]
    recetas: list[str | None]


class BestiaResumen(BaseModel):
    """Bestia espiritual domable (entrada de `EBEAST`).

    Atributos:
        identificador: clave corta (`'EB1'`…).
        nombre: nombre visible.
        ataque: ataque base (`A`).
        vida: vida base (`H`).
        indice_nivel: índice de nivel cuyo jefe la doma (0–7).
    """

    identificador: str
    nombre: str
    ataque: int
    vida: int
    indice_nivel: int


class MisionResumen(BaseModel):
    """Misión para el tab `mis` (entrada de `GQ`/`missions`).

    Atributos:
        identificador: id estable (`'g1'`, `'esp3'`…).
        nombre: título (`n`).
        descripcion: descripción corta (`d`).
        clave: contador de progreso en `qs` (`k`; `'ek.val'` usa
            `qs.ek['val']`).
        meta: valor objetivo (`g`).
        recompensa: objeto `rw` (claves `s/h/n/p/tes/card/recipe`).
        grupo: grupo de la UI (Combate/Exploración/Fabricación/
            Progreso; `missionGroup`).
        es_general: True si es de `GQ` (compartida entre sectas).
    """

    identificador: str
    nombre: str
    descripcion: str
    clave: str
    meta: int
    recompensa: dict[str, int]
    grupo: str
    es_general: bool


class PiezaEquipoResumen(BaseModel):
    """Pieza de la Herrería (entrada de `GEAR` para la pestaña `eqp`).

    Atributos:
        identificador: clave corta (`'G1'`…`'G17'`; también clave de
            guardado en `gr`/`eq`/`du`).
        nombre: nombre visible (`n`).
        slot: hueco que ocupa (`s`), clave de `SLOTS`.
        ataque: bono `a` (tope +4 en equipo).
        qi: bono `q` (tope +4 en equipo).
        coste: precio de forja en materiales (`c`; claves `h/n/p`).
        desbloqueo: índice de victoria que lo desbloquea (`u`);
            `None` = sin bloqueo.
        revive: vida con la que revive si es artefacto (`rv`).
        usos: cargas iniciales del artefacto (`du`).
        secta: secta con la que se identifica (`SC`).
    """

    identificador: str
    nombre: str
    slot: str
    ataque: int
    qi: int
    coste: dict[str, int]
    desbloqueo: int | None
    revive: int | None
    usos: int | None
    secta: str


class TrajeResumen(BaseModel):
    """Traje del armario (entrada de `OF[k]` con su efecto `OA`).

    Atributos:
        secta: secta dueña del traje (clave de `SECTAS`).
        indice: posición en el armario (0–5).
        nombre: nombre del traje (`OF[k][i][0]`).
        umbral: victorias totales para desbloquearlo (`TU[i]`).
        tipo: código de efecto (`OAT`): `hp/sh/q/rg/at/pa/ph/fd`.
        valor: magnitud del efecto.
        efecto: nombre del efecto (`OA(k, i).n`).
        descripcion: texto del efecto (`oaD(t, v)`).
    """

    secta: str
    indice: int
    nombre: str
    umbral: int
    tipo: str
    valor: int
    efecto: str
    descripcion: str


class HuecoEquipoResumen(BaseModel):
    """Hueco del panel de equipo (entrada de `SLOTS`/`SLN`).

    Atributos:
        clave: clave del hueco (clave de guardado en `eq`).
        nombre: nombre visible (`SLN`).
    """

    clave: str
    nombre: str


class EquipoResumen(BaseModel):
    """Catálogo de la pestaña `eqp` (Herrería + huecos del panel).

    Atributos:
        piezas: las 17 piezas, ordenadas por hueco (la Herrería).
        huecos: los 6 huecos del panel de equipo en orden de UI.
    """

    piezas: list[PiezaEquipoResumen]
    huecos: list[HuecoEquipoResumen]
