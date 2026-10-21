/** Cliente HTTP del envelope uniforme `{ok, data | error}`.

Todas las llamadas a la API pasan por `pedir`, que:
- traduce el envelope a los datos (éxito) o lanza `ErrorApi` (error);
- envuelve fallos de red en `ErrorApi('sin_backend', …)` para que las
  pantallas puedan mostrar "backend no disponible" sin crashear.

En desarrollo la petición va en relativo (`/api/...`) y Vite la proxea
al backend (:8765); `VITE_API_BASE` permite apuntar a otra URL si hace
falta (p. ej. backend remoto).
*/

import type {
  AcelerarJardin,
  BestiaResumen,
  CatalogoAlquimia,
  CatalogoEquipo,
  CatalogoGacha,
  CatalogoJardin,
  CatalogoMercado,
  CartaResumen,
  CosecharJardin,
  DetalleCarta,
  EnemigoResumen,
  Envoltura,
  EstadoCombate,
  EstadoJardin,
  EstadoServidor,
  MejorarJardin,
  MazmorraResumen,
  Narrativa,
  PartidaSlot,
  ResultadoAlquimia,
  ResultadoCombate,
  ResultadoEquipo,
  ResultadoGacha,
  ResultadoJardin,
  ResultadoMazos,
  ResultadoMercado,
  ResultadoReclamar,
  ResultadoReclamarMision,
  ResultadoSeguirMision,
  ResultadoMisiones,
  SectaResumen,
  SlotResumen,
  TrajeResumen,
} from './tipos'

const BASE = import.meta.env.VITE_API_BASE ?? ''

/** Error de API: red caída, envelope de error o respuesta inválida. */
export class ErrorApi extends Error {
  readonly codigo: string
  readonly estado: number

  constructor(codigo: string, mensaje: string, estado: number) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.codigo = codigo
    this.estado = estado
  }
}

async function pedir<T>(
  metodo: string,
  ruta: string,
  cuerpo?: unknown,
): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(`${BASE}${ruta}`, {
      method: metodo,
      headers:
        cuerpo === undefined
          ? undefined
          : { 'Content-Type': 'application/json' },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch {
    throw new ErrorApi('sin_backend', 'No se pudo contactar con el backend', 0)
  }

  let envoltura: Envoltura<T>
  try {
    envoltura = (await respuesta.json()) as Envoltura<T>
  } catch {
    throw new ErrorApi(
      'respuesta_invalida',
      `El backend no devolvió JSON en ${ruta}`,
      respuesta.status,
    )
  }

  if (
    typeof envoltura !== 'object' ||
    envoltura === null ||
    typeof envoltura.ok !== 'boolean'
  ) {
    throw new ErrorApi(
      'respuesta_invalida',
      `Respuesta fuera del envelope en ${ruta}`,
      respuesta.status,
    )
  }
  if (!envoltura.ok) {
    throw new ErrorApi(
      envoltura.error.code,
      envoltura.error.message,
      respuesta.status,
    )
  }
  return envoltura.data
}

function rutaSlot(slot: string): string {
  return `/api/game/${encodeURIComponent(slot)}`
}

export const api = {
  /** GET /api/health — versión y uptime del backend. */
  obtenerEstado: () => pedir<EstadoServidor>('GET', '/api/health'),

  /** GET /api/slots — resúmenes de las partidas guardadas. */
  listarPartidas: async () =>
    (await pedir<{ slots: SlotResumen[] }>('GET', '/api/slots')).slots,

  /** POST /api/game/new — crea (o reinicia) un slot y devuelve su snapshot. */
  crearPartida: (slot: string) =>
    pedir<PartidaSlot>('POST', '/api/game/new', { slot }),

  /** GET /api/game/{slot} — snapshot de una partida. */
  obtenerPartida: (slot: string) =>
    pedir<PartidaSlot>('GET', rutaSlot(slot)),

  /** POST /api/game/{slot}/secta — confirma la secta (`confirmS` del JS). */
  confirmarSecta: (slot: string, secta: string) =>
    pedir<PartidaSlot>('POST', `${rutaSlot(slot)}/secta`, { secta }),

  /** DELETE /api/game/{slot} — borra la partida. */
  borrarPartida: (slot: string) =>
    pedir<{ slot: string }>('DELETE', rutaSlot(slot)),

  /** GET /api/data/sectas — las 6 sectas jugables. */
  listarSectas: async () =>
    (await pedir<{ sectas: SectaResumen[] }>('GET', '/api/data/sectas')).sectas,

  /** GET /api/data/cartas — las 235 cartas (fichas resumidas). */
  listarCartas: async () =>
    (await pedir<{ cartas: CartaResumen[] }>('GET', '/api/data/cartas')).cartas,

  /** GET /api/data/enemigos — los 90 enemigos (fichas resumidas). */
  listarEnemigos: async () =>
    (
      await pedir<{ enemigos: EnemigoResumen[] }>('GET', '/api/data/enemigos')
    ).enemigos,

  /** GET /api/data/narrativa — prologo, reinos, niveles y final. */
  obtenerNarrativa: async () =>
    (await pedir<{ narrativa: Narrativa }>('GET', '/api/data/narrativa'))
      .narrativa,

  /** GET /api/data/mazmorras — las 6 mazmorras de recetas (`DG`). */
  listarMazmorras: async () =>
    (
      await pedir<{ mazmorras: MazmorraResumen[] }>(
        'GET',
        '/api/data/mazmorras',
      )
    ).mazmorras,

  /** GET /api/data/bestias — las 8 bestias domables (`BEAST`). */
  listarBestias: async () =>
    (await pedir<{ bestias: BestiaResumen[] }>('GET', '/api/data/bestias'))
      .bestias,

  // ---- Equipo (tab `eqp`) y Trajes (tab `trj`) ----

  /** GET /api/data/equipo — huecos y piezas de la Herrería (`GEAR`). */
  equipoCatalogo: async () =>
    (
      await pedir<{ equipo: CatalogoEquipo }>('GET', '/api/data/equipo')
    ).equipo,

  /** GET /api/data/trajes — los 60 trajes (10 sectas × 6). */
  trajesCatalogo: async () =>
    (await pedir<{ trajes: TrajeResumen[] }>('GET', '/api/data/trajes'))
      .trajes,

  /** POST …/equipo/forjar — forja una pieza con materiales (`forgeG`). */
  forjarEquipo: (slot: string, pieza: string) =>
    pedir<ResultadoEquipo>('POST', `${rutaSlot(slot)}/equipo/forjar`, {
      pieza,
    }),

  /** POST …/equipo/equipar — pone/retira una pieza (`wearG`). */
  equiparPieza: (slot: string, pieza: string) =>
    pedir<ResultadoEquipo>('POST', `${rutaSlot(slot)}/equipo/equipar`, {
      pieza,
    }),

  /** POST …/equipo/bestia — doma/retira la bestia de ayuda (`eqB`). */
  equiparBestia: (slot: string, bestia: string | null) =>
    pedir<ResultadoEquipo>('POST', `${rutaSlot(slot)}/equipo/bestia`, {
      bestia,
    }),

  /** POST …/traje/vestir — viste un traje de la secta (`wear`). */
  vestirTraje: (slot: string, secta: string, indice: number) =>
    pedir<ResultadoEquipo>('POST', `${rutaSlot(slot)}/traje/vestir`, {
      secta,
      indice,
    }),

  /** GET …/misiones — misiones del jugador con progreso (`GQ`+`missions`). */
  listarMisiones: (slot: string) =>
    pedir<ResultadoMisiones>('GET', `${rutaSlot(slot)}/misiones`),

  /** POST …/misiones/reclamar — `claimQ(id)`. */
  reclamarMision: (slot: string, mision: string) =>
    pedir<ResultadoReclamarMision>(
      'POST',
      `${rutaSlot(slot)}/misiones/reclamar`,
      { mision },
    ),

  /** POST …/misiones/seguir — `missionTrack(id)`. */
  seguirMision: (slot: string, mision: string) =>
    pedir<ResultadoSeguirMision>(
      'POST',
      `${rutaSlot(slot)}/misiones/seguir`,
      { mision },
    ),

  /** GET /api/data/alquimia — píldoras y opciones de forja. */
  obtenerAlquimia: () => pedir<CatalogoAlquimia>('GET', '/api/data/alquimia'),

  /** POST …/alquimia/elaborar — elabora una píldora (receta aprendida). */
  elaborarPildora: (slot: string, pildora: string) =>
    pedir<ResultadoAlquimia>(
      'POST',
      `${rutaSlot(slot)}/alquimia/elaborar`,
      { pildora },
    ),

  /** POST …/alquimia/forjar — forja una carta aleatoria de la rareza. */
  forjarCarta: (slot: string, rareza: number) =>
    pedir<ResultadoAlquimia>(
      'POST',
      `${rutaSlot(slot)}/alquimia/forjar`,
      { rareza },
    ),

  /** POST …/alquimia/fusionar — fusiona 3 copias en rareza superior. */
  fusionarCarta: (slot: string, carta: string) =>
    pedir<ResultadoAlquimia>(
      'POST',
      `${rutaSlot(slot)}/alquimia/fusionar`,
      { carta },
    ),

  /** POST …/alquimia/desmantelar — desmantela 1 copia en polvo de jade. */
  desmantelarCarta: (slot: string, carta: string) =>
    pedir<ResultadoAlquimia>(
      'POST',
      `${rutaSlot(slot)}/alquimia/desmantelar`,
      { carta },
    ),

  // ---- Mazos (tab `dk`) ----

  /** POST …/mazos — crea un mazo (vacío o copia del automático). */
  crearMazo: (slot: string, desdeAutomatico = false) =>
    pedir<ResultadoMazos>('POST', `${rutaSlot(slot)}/mazos`, {
      desde_automatico: desdeAutomatico,
    }),

  /** POST …/mazos/usar — activa un mazo (−1 = automático). */
  usarMazo: (slot: string, indice: number) =>
    pedir<ResultadoMazos>('POST', `${rutaSlot(slot)}/mazos/usar`, { indice }),

  /** POST …/mazos/duplicar — copia un mazo (sufijo « (copia)»). */
  duplicarMazo: (slot: string, indice: number) =>
    pedir<ResultadoMazos>('POST', `${rutaSlot(slot)}/mazos/duplicar`, {
      indice,
    }),

  /** POST …/mazos/eliminar — borra un mazo y reajusta el activo. */
  eliminarMazo: (slot: string, indice: number) =>
    pedir<ResultadoMazos>('POST', `${rutaSlot(slot)}/mazos/eliminar`, {
      indice,
    }),

  /** POST …/mazos/desequipar — quita 1 copia del mazo en uso. */
  desequiparCarta: (slot: string, carta: string) =>
    pedir<ResultadoMazos>('POST', `${rutaSlot(slot)}/mazos/desequipar`, {
      carta,
    }),

  /** POST …/mazos/{i}/renombrar — renombra (máx. 22 caracteres). */
  renombrarMazo: (slot: string, indice: number, nombre: string) =>
    pedir<ResultadoMazos>(
      'POST',
      `${rutaSlot(slot)}/mazos/${indice}/renombrar`,
      { nombre },
    ),

  /** POST …/mazos/{i}/anadir — añade 1 copia de una carta. */
  anadirCartaMazo: (slot: string, indice: number, carta: string) =>
    pedir<ResultadoMazos>(
      'POST',
      `${rutaSlot(slot)}/mazos/${indice}/anadir`,
      { carta },
    ),

  /** POST …/mazos/{i}/quitar — quita 1 copia de una carta. */
  quitarCartaMazo: (slot: string, indice: number, carta: string) =>
    pedir<ResultadoMazos>(
      'POST',
      `${rutaSlot(slot)}/mazos/${indice}/quitar`,
      { carta },
    ),

  /** POST …/mazos/{i}/vaciar — vacía el mazo. */
  vaciarMazo: (slot: string, indice: number) =>
    pedir<ResultadoMazos>('POST', `${rutaSlot(slot)}/mazos/${indice}/vaciar`),

  /** POST …/mazos/{i}/autocompletar — rellena con las mejores cartas. */
  autocompletarMazo: (slot: string, indice: number) =>
    pedir<ResultadoMazos>(
      'POST',
      `${rutaSlot(slot)}/mazos/${indice}/autocompletar`,
    ),

  // ---- Mercado (tab `mkt`) ----

  /** GET /api/data/mercado — puestos, precios de venta y vitrina. */
  obtenerMercado: () => pedir<CatalogoMercado>('GET', '/api/data/mercado'),

  /** GET /api/data/cartas/{id}/detalle — detalle para el modal (`mkDet`). */
  detalleCarta: (identificador: string, secta?: string) =>
    pedir<{ carta: DetalleCarta }>(
      'GET',
      `/api/data/cartas/${encodeURIComponent(identificador)}/detalle${
        secta ? `?secta=${encodeURIComponent(secta)}` : ''
      }`,
    ),

  /** POST …/mercado/comprar — compra una carta del puesto (`buy`). */
  comprarCarta: (slot: string, carta: string) =>
    pedir<ResultadoMercado>('POST', `${rutaSlot(slot)}/mercado/comprar`, {
      carta,
    }),

  /** POST …/mercado/comprar-material — lote del puesto (`buyM`). */
  comprarMaterial: (
    slot: string,
    puesto: string,
    confirmado = false,
  ) =>
    pedir<ResultadoMercado>(
      'POST',
      `${rutaSlot(slot)}/mercado/comprar-material`,
      { puesto, confirmado },
    ),

  /** POST …/mercado/vender — vende 1 unidad de material (`sellM`). */
  venderMaterial: (slot: string, material: string) =>
    pedir<ResultadoMercado>('POST', `${rutaSlot(slot)}/mercado/vender`, {
      material,
    }),

  /** POST …/mercado/comprar-pildora — vitrina del General (`buyC`). */
  comprarPildora: (slot: string, pildora: string) =>
    pedir<ResultadoMercado>(
      'POST',
      `${rutaSlot(slot)}/mercado/comprar-pildora`,
      { pildora },
    ),

  // ---- Gacha (Ceremonia de Adivinación) ----

  /** GET /api/data/gacha — tickets, pools y rarezas. */
  obtenerGacha: () => pedir<CatalogoGacha>('GET', '/api/data/gacha'),

  /** POST …/gacha/tirar — invoca 1 o 10 veces (`GachaSystem.draw`). */
  tirarGacha: (slot: string, pool: 'STANDARD' | 'PREMIUM', count: 1 | 10) =>
    pedir<ResultadoGacha>('POST', `${rutaSlot(slot)}/gacha/tirar`, {
      pool,
      count,
    }),

  // ---- Combate (Fase 2) ----

  /** GET …/combate — estado del combate activo (o `activo: false`). */
  obtenerCombate: (slot: string) =>
    pedir<{ combate: EstadoCombate }>('GET', `${rutaSlot(slot)}/combate`),

  /** POST …/combate/iniciar — `begin(k)`. */
  iniciarCombate: (
    slot: string,
    enemigo: number,
    pildoras: string[] = [],
    bolsa: string[] = [],
  ) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/iniciar`, {
      enemigo,
      pildoras,
      bolsa,
    }),

  /** POST …/combate/jugar — `play`. */
  jugarCartaCombate: (
    slot: string,
    indice: number,
    objetivo: number | null = null,
  ) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/jugar`, {
      indice,
      objetivo,
    }),

  /** POST …/combate/atacar — `hit` (objetivo −1 = héroe). */
  atacarCombate: (slot: string, atacante: number, objetivo: number) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/atacar`, {
      atacante,
      objetivo,
    }),

  /** POST …/combate/activar — `act` (habilidad de criatura). */
  activarHabilidad: (slot: string, indice: number) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/activar`, {
      indice,
    }),

  /** POST …/combate/fin-turno — `endT`. */
  terminarTurno: (slot: string, forzar = false) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/fin-turno`, {
      forzar,
    }),

  /** POST …/combate/descartar-exceso — `edisc`. */
  descartarExceso: (slot: string, indice: number) =>
    pedir<ResultadoCombate>(
      'POST',
      `${rutaSlot(slot)}/combate/descartar-exceso`,
      { indice },
    ),

  /** POST …/combate/descartar-cancelar — `ED = 0` (seguir jugando). */
  cancelarDescartarExceso: (slot: string) =>
    pedir<ResultadoCombate>(
      'POST',
      `${rutaSlot(slot)}/combate/descartar-cancelar`,
      {},
    ),

  /** POST …/combate/elegir-vacio — `vpick`. */
  elegirVacio: (slot: string, indice: number) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/elegir-vacio`, {
      indice,
    }),

  /** POST …/combate/cancelar-vacio — `vdone`. */
  cancelarVacio: (slot: string) =>
    pedir<ResultadoCombate>(
      'POST',
      `${rutaSlot(slot)}/combate/cancelar-vacio`,
      {},
    ),

  /** POST …/combate/evento — `evPick` (opción de evento de mapa). */
  resolverEventoCombate: (slot: string, opcion: number) =>
    pedir<ResultadoCombate>('POST', `${rutaSlot(slot)}/combate/evento`, {
      opcion,
    }),

  /** POST …/combate/usar-pildora — `usePill` (píldora de la bolsa). */
  usarPildoraCombate: (slot: string, pildora: string) =>
    pedir<ResultadoCombate>(
      'POST',
      `${rutaSlot(slot)}/combate/usar-pildora`,
      { pildora },
    ),

  /** POST …/combate/abandonar — huye sin recompensas. */
  abandonarCombate: (slot: string) =>
    pedir<ResultadoCombate>(
      'POST',
      `${rutaSlot(slot)}/combate/abandonar`,
      {},
    ),

  /** POST …/combate/cerrar — libera la sesión tras un fin ya aplicado. */
  cerrarCombate: (slot: string) =>
    pedir<{ fin: string }>('POST', `${rutaSlot(slot)}/combate/cerrar`, {}),

  /** POST …/combate/reclamar — elige UNA recompensa (`claim`). */
  reclamarRecompensa: (slot: string, indice: number) =>
    pedir<ResultadoReclamar>(
      'POST',
      `${rutaSlot(slot)}/combate/reclamar`,
      { indice },
    ),

  /** POST …/combate/emboscada/iniciar — combate contra `amb.o`. */
  iniciarEmboscada: (
    slot: string,
    pildoras: string[] = [],
    bolsa: string[] = [],
  ) =>
    pedir<ResultadoCombate>(
      'POST',
      `${rutaSlot(slot)}/combate/emboscada/iniciar`,
      { pildoras, bolsa },
    ),

  /** POST …/combate/emboscada/huir — descarta la emboscada (`amb=null`). */
  huirEmboscada: (slot: string) =>
    pedir<{ emboscada: null }>(
      'POST',
      `${rutaSlot(slot)}/combate/emboscada/huir`,
      {},
    ),

  // ---- Jardín Medicinal (tab `jar`; módulo nuevo, sin monolito) ----

  /** GET /api/data/jardin — especies, formaciones y mejoras. */
  jardinCatalogo: () => pedir<CatalogoJardin>('GET', '/api/data/jardin'),

  /** GET …/jardin/estado — casillas con los tiempos ya calculados. */
  jardinEstado: (slot: string) =>
    pedir<EstadoJardin>('GET', `${rutaSlot(slot)}/jardin/estado`),

  /** POST …/jardin/sembrar — gasta 1 semilla en una casilla vacía. */
  jardinSembrar: (slot: string, indice: number, planta: string) =>
    pedir<ResultadoJardin>('POST', `${rutaSlot(slot)}/jardin/sembrar`, {
      indice,
      planta,
    }),

  /** POST …/jardin/acelerar — cada piedra quita 5 % del tiempo restante. */
  jardinAcelerar: (slot: string, indice: number, piedras: number) =>
    pedir<AcelerarJardin>('POST', `${rutaSlot(slot)}/jardin/acelerar`, {
      indice,
      piedras,
    }),

  /** POST …/jardin/cosechar — hierbas al Horno y casilla libre. */
  jardinCosechar: (slot: string, indice: number) =>
    pedir<CosecharJardin>('POST', `${rutaSlot(slot)}/jardin/cosechar`, {
      indice,
    }),

  /** POST …/jardin/mejorar — amplía la cuadrícula (4→6→9→12). */
  jardinMejorar: (slot: string) =>
    pedir<MejorarJardin>('POST', `${rutaSlot(slot)}/jardin/mejorar`, {}),

  /** POST …/jardin/formacion — equipa (o con null, quita) la formación. */
  jardinFormacion: (slot: string, identificador: string | null) =>
    pedir<ResultadoJardin>('POST', `${rutaSlot(slot)}/jardin/formacion`, {
      identificador,
    }),
}
