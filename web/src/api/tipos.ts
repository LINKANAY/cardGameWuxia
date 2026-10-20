/** Tipos compartidos entre la API (backend Python) y la interfaz.

Las claves del snapshot (`realm`, `hp`, `wins`…) son el **formato de
guardado xcg3**: se conservan tal cual porque así las escribe el
backend y así las leería el monolito. El resto de tipos usan nombres
descriptivos en español, como en el backend.
"""

/** Envelope uniforme: éxito `{"ok": true, data}` o error `{"ok": false, error}`. */
export type Exito<T> = { ok: true; data: T }
export type Fallo = { ok: false; error: { code: string; message: string } }
export type Envoltura<T> = Exito<T> | Fallo

/** Respuesta de GET /api/health. */
export interface EstadoServidor {
  version: string
  uptime: number
}

/** Mazo guardado (`dk[i]` del JS: `{n, c}`). */
export interface MazoGuardado {
  /** Nombre visible (`n`), máx. 22 caracteres. */
  n: string
  /** Cartas del mazo: id → nº de copias (`c`). */
  c: Record<string, number>
}

/** Snapshot de partida — dict `data` del guardado `xcg3` (23 claves). */
export interface SnapshotPartida {
  /** Índice en REINOS (0–14). */
  realm: number
  /** Vida del héroe entre combates; null si aún no hay partida en curso. */
  hp: number | null
  /** Índices globales de ENEMIGOS vencidos. */
  wins: number[]
  /** Cartas poseídas: id → nº de copias (máx. 3). */
  col: Record<string, number>
  /** Secta de la partida (clave de SECTAS). */
  sect: string
  /** Materiales: h=hierbas, n=núcleos, p=polvo de jade. */
  mat: { h: number; n: number; p: number }
  /** Piedras espirituales (moneda principal). */
  stn: number
  /** Mazos guardados (`mzs`; máx. 8). */
  dk: MazoGuardado[]
  /** Índice del mazo activo, -1 si el automático. */
  ad: number
  /** Píldoras: id → cantidad. */
  pil: Record<string, number>
  /** Atuendo: secta → variante de arte. */
  of: Record<string, number>
  /** Recetas aprendidas: id → 1. */
  rec: Record<string, number>
  /** Bestia equipada, si la hay. */
  be: string | null
  /** Equipo guardado (armaduras forjadas). */
  gr: Record<string, unknown>
  /** Equipo puesto. */
  eq: Record<string, unknown>
  /** Secta confirmada tras la primera victoria; null = sin confirmar. */
  sc: string | null
  /** Usos restantes de equipo con cargas. */
  du: Record<string, number>
  /** Muertes acumuladas. */
  dt: number
  /** Mejor racha de victorias seguidas. */
  bt: number
  /** Estado de misiones y contadores (dict heterogéneo, `newQs()`). */
  qs: Record<string, unknown>
  /** Misiones ya reclamadas: id → 1. */
  qd: Record<string, number>
  /** Tickets de gacha (`gt`: ticket_common/ticket_premium). */
  gt: Record<string, number>
  /** Contador de piedad del gacha (`gp`: standard_pity/premium_pity). */
  gp: Record<string, number>
}

/** Resumen de un slot guardado (GET /api/slots). */
export interface SlotResumen {
  slot: string
  nivel_reino: number
  secta: string
  victorias: number
}

/** Secta jugable (GET /api/data/sectas). */
export interface SectaResumen {
  identificador: string
  nombre: string
  descripcion: string
  cartas_iniciales: string[]
}

/** Ficha breve de carta (GET /api/data/cartas). */
export interface CartaResumen {
  identificador: string
  nombre: string
  tipo: string
  coste_qi: number
  ataque: number | null
  vida: number | null
  rareza: number
  /** Clave del mapa `SC` (`'neu'` = coleccionable sin secta); null si no. */
  secta: string | null
  /** En la lista `NEU`: usables hasta en 3 copias sin coleccionar. */
  es_neutral: boolean
  /** No aparece en el mercado ni en recompensas normales (`lk`). */
  reliquia: boolean
  /** Carta del Abismo (`vb`/`vs`): una vez obtenida sale del mercado. */
  es_abismo: boolean
  /** Disipa formaciones y runas rivales (`dsp`). */
  disipa?: boolean
  /** Líneas de efectos (`descH`, texto plano); vacía si no tiene. */
  descripcion: string[]
}

/** Ficha breve de enemigo (GET /api/data/enemigos). */
export interface EnemigoResumen {
  indice: number
  nombre_enemigo: string
  secta: string
  nombre_nivel: string
  vida: number
  dificultad: number
  origen: 'nivel' | 'mazmorra' | 'mision'
  frase_inicio: string
  /** Historia propia (`c.story`); vacía si usa la del nivel. */
  historia: string
  /** Índice de nivel (`li`), para narrativa y escalado. */
  indice_nivel: number
  /** Descripción de habilidades del oponente (`c.r`). */
  texto_habilidades: string
  /** Rareza de recompensa (`rw`); null si no suelta cartas. */
  rareza_recompensa?: number | null
}

/** Textos narrativos globales (GET /api/data/narrativa). */
export interface Narrativa {
  prologo: string
  final: string
  reinos: string[]
  textos_intro_nivel: string[]
  textos_fin_nivel: string[]
}

/** Datos devueltos por crear/cargar/borrar partida. */
export interface PartidaSlot {
  slot: string
  snapshot?: SnapshotPartida
}

/** Claves cortas de material en costes e inventario (`mat` del snapshot). */
export type Materiales = { h: number; n: number; p: number }

/** Píldora del catálogo (GET /api/data/alquimia; `PIL` del JS). */
export interface PildoraResumen {
  identificador: string
  nombre: string
  efecto: string
  /** Materiales para elaborarla, con claves cortas `'h'/'n'/'p'`. */
  coste: Partial<Materiales>
  es_combate: boolean
  /** Clase de icono del monolito (`PILK[k]`; `'tal'` = glifo 符). */
  icono: string
}

/** Opción de forja por rareza (GET /api/data/alquimia; `RN`/`RC`/`FC`). */
export interface ForjaResumen {
  rareza: number
  nombre: string
  color: string
  coste: Partial<Materiales>
}

/** Catálogo del taller de alquimia. */
export interface CatalogoAlquimia {
  pildoras: PildoraResumen[]
  forja: ForjaResumen[]
}

/** Respuesta de una acción de alquimia (elaborar/forjar/fusionar/…). */
export interface ResultadoAlquimia {
  slot: string
  mensaje: string
  snapshot: SnapshotPartida
  /** Id de la carta obtenida (forjar/fusionar). */
  carta?: string
  /** Polvo de jade ganado (desmantelar). */
  polvo?: number
}

/** Respuesta de una acción de mazos (crear/editar/usar/…). */
export interface ResultadoMazos {
  slot: string
  mensaje: string
  snapshot: SnapshotPartida
}

// ---- Mercado (tab `mkt`) ----

/** Lote de material de un puesto (`MK[k][2]`). */
export interface LoteMaterial {
  nombre: string
  material: string
  cantidad: number
  costo: number
}

/** Puesto del mercado (`MK[k]`). */
export interface PuestoMercado {
  identificador: string
  vendedor: string
  frase: string
  lote: LoteMaterial | null
}

/** Píldora de la vitrina del General (`mkcList`). */
export interface PildoraVenta {
  identificador: string
  nombre: string
  efecto: string
  tipo: string
  precio: number
  icono: string
  es_talisman: boolean
  receta_aprendida: boolean
}

/** Catálogo estático del mercado (GET /api/data/mercado). */
export interface CatalogoMercado {
  puestos: PuestoMercado[]
  precios_venta: Record<string, number>
  pildoras_en_venta: PildoraVenta[]
}

/** Detalle de carta para el modal (`mkDet`). */
export interface DetalleCarta {
  identificador: string
  nombre: string
  tipo: string
  rareza: number
  secta_visible: string
  coste_qi: number
  precio: number
  descripcion: string[]
  estadisticas: Array<[string, string]>
  acumulacion: Array<Record<string, unknown>> | null
  propiedades: string[]
  obtencion: string[]
  es_abismo: boolean
}

/** Respuesta de una acción del mercado. */
export interface ResultadoMercado {
  slot: string
  mensaje: string
  snapshot: SnapshotPartida
  /** True si el backend pide confirmar la compra de material. */
  confirmar?: boolean
  /** Lote ofrecido al pedir confirmación. */
  lote?: LoteMaterial
  /** Piedras ganadas al vender. */
  piedras?: number
}

// ---- Gacha (Ceremonia de Adivinación) ----

/** Reliquia resonante del gacha (`TICKET_TYPES`). */
export interface TicketGacha {
  identificador: string
  nombre: string
  descripcion: string
  icono: string
}

/** Distribución de rarezas de un pool. */
export interface ProbabilidadesGacha {
  common: number
  rare: number
  epic: number
  legendary: number
}

/** Garantías de un pool (`pitySystem`). */
export interface PiedadGacha {
  garantizado_raro_tras: number
  garantizado_epico_tras: number
  clave: string
}

/** Pool de invocación (`GACHA_POOLS`). */
export interface PoolGacha {
  clave: string
  identificador: string
  nombre: string
  descripcion: string
  tipo_ticket: string
  coste_por_tirada: number
  probabilidades: ProbabilidadesGacha
  piedad: PiedadGacha
}

/** Metadatos de rareza de gacha (`RARITY_INFO`). */
export interface RarezaGacha {
  clave: string
  nombre: string
  color: string
  rareza_rn: number
}

/** Catálogo estático del gacha (GET /api/data/gacha). */
export interface CatalogoGacha {
  tickets: TicketGacha[]
  pools: PoolGacha[]
  rarezas: RarezaGacha[]
}

/** Recompensa de una tirada (`generateReward`). */
export interface RecompensaGacha {
  tipo: 'carta' | 'recurso'
  carta: string | null
  nombre: string
  rareza: string
  descripcion: string
}

/** Respuesta de una tirada del gacha. */
export interface ResultadoGacha {
  slot: string
  mensaje: string
  resultados: RecompensaGacha[]
  tickets_restantes: number
  piedad: number
  snapshot: SnapshotPartida
}

// ---- Combate (Fase 2/3) ----

/** Carta en combate (snapshot de `CartaJuego`). */
export interface CartaCombate {
  id: string
  nombre: string
  coste: number
  tipo: string
  ataque: number | null
  vida: number | null
  lista: boolean
  provocar: boolean
  impetu: boolean
  robar_vida: boolean
  crece: number | null
  usada: boolean
  bestia: boolean
  reliquia: boolean
  /** Daño a criatura rival (`td`); null si no aplica. */
  dano_criatura: number | null
  /** Mejora a criatura aliada (`bf`); null si no aplica. */
  mejora_aliada: { ataque: number; vida: number } | null
  /** Habilidad activa (`ab`), si la tiene. */
  habilidad: {
    coste: number
    efecto: string
    valor: number
    descripcion: string
  } | null
  /** Ficha de formación/runa (`bdg` F/R); null para el resto. */
  formacion?: {
    /** `pa`: +ATK por criatura mientras esté activa. */
    pa: number
    /** `ph`: +vida al entrar en tablero. */
    ph: number
    /** `[clave, valor]` de `efecto_inicio_turno` (`ts`). */
    ts: [string, number] | null
  } | null
  /** Líneas de efectos (`descH`), texto plano. */
  descripcion: string[]
}

/** Formación trazada en combate (`fm` de `fmPut`). */
export interface FormacionActiva {
  id: string
  nombre: string
  /** `pa`: +ATK de todas las criaturas al atacar/defender. */
  pa: number
  /** `ph`: +vida al entrar en tablero. */
  ph: number
  /** Descripción de la carta (`descH`), para el tooltip. */
  desc: string[]
}

/** Runa grabada en combate (`rn` de `fmPut`, máx. 2). */
export interface RunaActiva {
  id: string
  nombre: string
  /** Turnos restantes (`du`); al llegar a 0 se va al Agujero Negro. */
  du: number
  /** Descripción de la carta (`descH`), para el tooltip. */
  desc: string[]
}

/** Lado del combate (héroe + tablero + mazos). */
export interface LadoCombate {
  nombre: string
  hp: number
  mx: number
  qi: number
  mq: number
  cap: number
  sh: number
  mazo: number
  /** Cartas del mazo sorteado (para «Ver mazo»). */
  cartas_mazo: CartaCombate[]
  mano: CartaCombate[]
  tablero: CartaCombate[]
  vacio: CartaCombate[]
  turnos: number
  /** Píldoras de la bolsa de combate (`P.pouch` de `eqpB`). */
  pouch: string[]
  /** Usos de bolsa consumidos (`P.pu`), máx. 2. */
  usos: number
  /** Formación activa del lado (`fm`); null si no hay. */
  fm: FormacionActiva | null
  /** Runas grabadas (`rn`), máximo 2. */
  rn: RunaActiva[]
  /** Bonus de ataque del equipo/efectos (`atkb`), visible ⚔+N. */
  atkb: number
  /** Intención de Espada armada (`bo`). */
  bo: boolean
  /** Bonus de formación ya aplicados a las criaturas en tablero. */
  opa: number
  oph: number
  /** Puede salvarte de la muerte: talismán/píldora/artefacto. */
  salvavidas: boolean
}

/** Evento de mapa activo (`EV` de js/06-contenido.js:213). */
export interface EventoMapaActivo {
  nombre: string
  texto: string
  opciones: string[]
}

/** Evento de campaña emitido por el motor (`chk`). */
export interface EventoCampana {
  tipo: string
  [clave: string]: unknown
}

/** Acción de la IA enemiga para la UI. */
export interface AccionEnemiga {
  tipo: string
  carta: string | null
  nombre: string | null
  objetivo_nombre: string | null
  habla: string | null
  datos: Record<string, unknown>
}

/** Snapshot del combate activo (GET/POST …/combate). */
export interface EstadoCombate {
  activo: boolean
  fin: string
  lock: boolean
  logs: string[]
  jugador: LadoCombate
  enemigo: LadoCombate
  indice_enemigo: number | null
  pd: CartaCombate[]
  vp_n: number
  ed: number
  ec: boolean
  sel: number
  tg: number | null
  /** Evento de mapa pendiente de elegir opción (`ev`), si lo hay. */
  ev: EventoMapaActivo | null
  eventos: Array<{ tipo: string; datos: Record<string, unknown> }>
  /** Stock real de píldoras en el inventario (`pil`). */
  pildoras_stock: Record<string, number>
}

/** Respuesta de una acción de combate. */
export interface ResultadoCombate {
  slot: string
  combate: EstadoCombate
  campaña: EventoCampana[]
  acciones?: AccionEnemiga[]
}

/** Respuesta de POST …/combate/reclamar (`claim`). */
export interface ResultadoReclamar {
  slot: string
  carta: string
  copias: number
  recompensas: string[]
}

/** Mazmorra de recetas (GET /api/data/mazmorras). */
export interface MazmorraResumen {
  indice: number
  nombre: string
  nivel: number
  indice_receta: number
  pista: string
  historia: string
  pisos: number[]
  /** Receta que revela cada piso (null si no revela). */
  recetas: Array<string | null>
}

/** Bestia domable por jefe de nivel (GET /api/data/bestias). */
export interface BestiaResumen {
  identificador: string
  nombre: string
  ataque: number
  vida: number
  indice_nivel: number
}

/** Misión con progreso (GET …/misiones, por entrada). */
export interface MisionResumen {
  identificador: string
  nombre: string
  descripcion: string
  clave: string
  meta: number
  recompensa: Record<string, number>
  progreso: number
  reclamada: boolean
  lista: boolean
  /** Grupo de la UI (Combate/Exploración/Fabricación/Progreso). */
  grupo: string
  /** True si es de `GQ` (compartida entre sectas). */
  es_general: boolean
}

/** Tracker de misión seguida (null si no hay). */
export interface TrackerMision {
  identificador: string
  nombre: string
  descripcion: string
  meta: number
  progreso: number
}

/** Respuesta de GET …/misiones. */
export interface ResultadoMisiones {
  misiones: MisionResumen[]
  tracker: TrackerMision | null
}

/** Respuesta de POST …/misiones/reclamar (`claimQ`). */
export interface ResultadoReclamarMision {
  slot: string
  mensaje: string
  tes: boolean
  carta: string | null
  receta: string | null
  snapshot: SnapshotPartida
}

/** Respuesta de POST …/misiones/seguir (`missionTrack`). */
export interface ResultadoSeguirMision {
  slot: string
  track: string
  snapshot: SnapshotPartida
}

// ---- Equipo (tab `eqp`) y Trajes (tab `trj`) ----

/** Pieza de la Herrería (GET /api/data/equipo; `GEAR` de js/06-contenido.js:47). */
export interface PiezaEquipoResumen {
  /** `'G1'`…`'G17'`. */
  identificador: string
  nombre: string
  /** Hueco donde se equipa (clave de `SLOTS`). */
  slot: string
  ataque: number
  qi: number
  /** Materiales para forjarla, con claves cortas `'h'/'n'/'p'`. */
  coste: Partial<Materiales>
  /** Enemigo que hay que vencer para desbloquearla; null = siempre disponible. */
  desbloqueo: number | null
  /** Si revive, vida con la que resucita (null = no revive). */
  revive: number | null
  /** Cargas que otorga al forjarla (null = sin cargas). */
  usos: number | null
  /** Secta cuyo color lleva el arte (`SC` del monolito). */
  secta: string
}

/** Hueco de equipo (`SLOT_NOMBRE`; orden fijo `SLOTS`). */
export interface HuecoEquipoResumen {
  clave: string
  nombre: string
}

/** Catálogo de la pestaña Equipo: piezas + huecos (el estado va en el snapshot). */
export interface CatalogoEquipo {
  piezas: PiezaEquipoResumen[]
  huecos: HuecoEquipoResumen[]
}

/** Traje del armario (GET /api/data/trajes; `OF[k]` + `OA` del monolito). */
export interface TrajeResumen {
  secta: string
  /** Índice dentro de la secta (0–5). */
  indice: number
  nombre: string
  /** Victorias totales mínimas para desbloquearlo (`TU`). */
  umbral: number
  /** Clave del efecto en combate (`k` de `OA`). */
  tipo: string
  valor: number
  /** Nombre visible del efecto (`a.n` de `OA`). */
  efecto: string
  /** Texto del efecto (`a.d` de `OA`). */
  descripcion: string
}

/** Respuesta de una acción de equipo o de trajes. */
export interface ResultadoEquipo {
  slot: string
  mensaje: string
  snapshot: SnapshotPartida
}
