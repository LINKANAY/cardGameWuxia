/** Tests de flujo del shell: splash → Campamento/Alquimia/Guía (slot fijo). */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { guardarPantalla, leerPantalla } from './persistencia'
import type {
  CartaResumen,
  EnemigoResumen,
  Narrativa,
  SectaResumen,
  SnapshotPartida,
} from './api/tipos'

const SNAPSHOT: SnapshotPartida = {
  realm: 0,
  hp: 24,
  wins: [0, 1],
  col: { cf: 3, ev: 1 },
  sect: 'esp',
  mat: { h: 10, n: 5, p: 2 },
  stn: 45,
  dk: [{ n: 'Mazo Sabio', c: { cf: 3, ev: 1 } }],
  ad: -1,
  pil: { vit: 1 },
  of: {},
  rec: { vit: 1, tes: 1 },
  be: null,
  gr: {},
  eq: {},
  sc: 'esp',
  du: {},
  dt: 1,
  bt: 3,
  qs: { track: '' },
  qd: {},
  gt: { ticket_common: 5, ticket_premium: 2 },
  gp: { standard_pity: 0, premium_pity: 0 },
}

const NARRATIVA: Narrativa = {
  prologo: 'En el principio, un cultivador ascenso.',
  final: 'Y el Dao quedó sellado.',
  reinos: ['Mortal', ...Array.from({ length: 14 }, (_, i) => `Reino ${i + 1}`)],
  textos_intro_nivel: Array.from({ length: 8 }, () => 'intro'),
  textos_fin_nivel: Array.from({ length: 8 }, () => 'fin'),
}

const SECTAS: SectaResumen[] = [
  {
    identificador: 'esp',
    nombre: 'Espada Celestial',
    descripcion: 'Daño rápido.',
    // las 5 cartas del mazo base (`S.esp.l` del monolito)
    cartas_iniciales: ['cf', 'ev', 'ld', 'ma', 'te'],
  },
  {
    identificador: 'lot',
    nombre: 'Loto Púrpura',
    descripcion: 'Control y veneno.',
    cartas_iniciales: ['lc', 'ej', 'gr', 'ml', 'ab'],
  },
  {
    identificador: 'mon',
    nombre: 'Montaña Inmortal',
    descripcion: 'Defensa total: Provocar y escudos.',
    // secta v47: sus 5 cartas base (`NS.mon`, primeras 5 en `S.mon.l`)
    cartas_iniciales: ['M01', 'M02', 'M03', 'M04', 'M05'],
  },
]

const CARTAS: CartaResumen[] = [
  {
    identificador: 'cf',
    nombre: 'Corte Veloz',
    tipo: 'T',
    coste_qi: 1,
    ataque: null,
    vida: null,
    rareza: 0,
    secta: 'esp',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: ['Daña 3 a una criatura rival (si no hay, al héroe)'],
  },
  {
    identificador: 'ev',
    nombre: 'Espectro de la Espada',
    tipo: 'C',
    coste_qi: 2,
    ataque: 3,
    vida: 1,
    rareza: 1,
    secta: 'esp',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: ['Provocar'],
  },
  {
    identificador: 'pq',
    nombre: 'Poción de Qi',
    tipo: 'P',
    coste_qi: 1,
    ataque: null,
    vida: null,
    rareza: 0,
    secta: null,
    es_neutral: true,
    reliquia: false,
    es_abismo: false,
    descripcion: ['+2 Qi'],
  },
  {
    identificador: 'ex',
    nombre: 'Filo Exilio',
    tipo: 'C',
    coste_qi: 3,
    ataque: 4,
    vida: 2,
    rareza: 3,
    secta: 'esp',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: ['⚔ Espada'],
  },
  {
    identificador: 'M01',
    nombre: 'Aprendiz de la Montaña',
    tipo: 'C',
    coste_qi: 1,
    ataque: 1,
    vida: 3,
    rareza: 0,
    secta: 'mon',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: ['Provocar'],
  },
  {
    identificador: 'M06',
    nombre: 'Avalancha',
    tipo: 'T',
    coste_qi: 3,
    ataque: null,
    vida: null,
    rareza: 2,
    secta: 'mon',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: ['Daña 4 a una criatura rival'],
  },
  {
    identificador: 'Y05',
    nombre: 'Formación de Sangre Hirviente',
    tipo: 'F',
    coste_qi: 3,
    ataque: null,
    vida: null,
    rareza: 3,
    secta: null,
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    disipa: false,
    descripcion: [
      'Tus criaturas: +2 ATK',
      'Cada turno: pierdes 1 de vida',
    ],
  },
]

const ENEMIGOS: EnemigoResumen[] = [
  {
    indice: 0,
    nombre_enemigo: 'Bandido de la Colina',
    secta: 'esp',
    nombre_nivel: 'Prueba inicial',
    vida: 30,
    dificultad: 0,
    origen: 'nivel',
    frase_inicio: '¡Ríndete!',
    historia: '',
    indice_nivel: 0,
    texto_habilidades: 'Sin habilidades.',
  },
]

const CATALOGO_ALQUIMIA = {
  pildoras: [
    {
      identificador: 'vit',
      nombre: 'Elixir de Vitalidad',
      efecto: 'Recupera 8 de vida',
      coste: { h: 3 },
      es_combate: false,
      icono: 'heal',
    },
    {
      identificador: 'tes',
      nombre: 'Elixir de la Tenacidad',
      efecto: '+2 de vida máxima durante el combate',
      coste: { h: 2, n: 1 },
      es_combate: false,
      icono: 'shield',
    },
    {
      identificador: 'cla',
      nombre: 'Clarity Pill',
      efecto: 'Aumenta el Qi',
      coste: { h: 1 },
      es_combate: true,
      icono: 'qi',
    },
  ],
  forja: [
    { rareza: 0, nombre: 'Común', color: '#a8b4c2', coste: { p: 2 } },
    { rareza: 1, nombre: 'Poco común', color: '#7be0b8', coste: { p: 4 } },
    { rareza: 2, nombre: 'Rara', color: '#e3bf6a', coste: { p: 7 } },
    { rareza: 3, nombre: 'Épica', color: '#c084fc', coste: { p: 10, n: 2 } },
    { rareza: 4, nombre: 'Legendaria', color: '#f0a868', coste: { p: 16, n: 4 } },
    { rareza: 5, nombre: 'Celestial', color: '#ff6b6b', coste: { p: 24, n: 8 } },
  ],
}

const MAZMORRAS = [
  {
    indice: 0,
    nombre: 'Cueva del Alquimista Olvidado',
    nivel: 1,
    indice_receta: 5,
    pista: 'Una cueva sin dueño.',
    historia: 'Tras la prueba…',
    pisos: [48, 49, 50],
    recetas: ['cla', 'esc', 'reg'],
  },
]

const BESTIAS = [
  { identificador: 'BS1', nombre: 'Lobo de la Aldea', ataque: 2, vida: 3, indice_nivel: 0 },
]

/** Huecos del panel de equipo (orden `SLOTS` del backend). */
const HUECOS_EQUIPO = [
  { clave: 'cabeza', nombre: 'Cabeza' },
  { clave: 'cuerpo', nombre: 'Cuerpo' },
  { clave: 'guantes', nombre: 'Guantes' },
  { clave: 'botas', nombre: 'Botas' },
  { clave: 'reliquia', nombre: 'Reliquia' },
  { clave: 'artefacto', nombre: 'Artefacto' },
]

const CATALOGO_EQUIPO = {
  piezas: [
    {
      identificador: 'G1',
      nombre: 'Diadema de Jade',
      slot: 'cabeza',
      ataque: 0,
      qi: 1,
      coste: { p: 3, h: 2 },
      desbloqueo: null,
      revive: null,
      usos: null,
      secta: 'lot',
    },
    {
      identificador: 'G2',
      nombre: 'Casco del Dragón',
      slot: 'cabeza',
      ataque: 1,
      qi: 1,
      coste: { p: 6, n: 2 },
      desbloqueo: 17,
      revive: null,
      usos: null,
      secta: 'dra',
    },
  ],
  huecos: HUECOS_EQUIPO,
}

/** Los 6 trajes de la secta espada (`OF.esp` + `TU`). */
const CATALOGO_TRAJES = [0, 1, 2, 3, 4, 5].map((indice) => ({
  secta: 'esp',
  indice,
  nombre: `Traje ${indice}`,
  umbral: [0, 3, 12, 30, 45, 60][indice],
  tipo: 'hp',
  valor: 2,
  efecto: 'Cuerpo de Jade',
  descripcion: '+2 de vida máxima',
}))

const MISIONES_LISTA = {
  misiones: [
    {
      identificador: 'g1',
      nombre: 'Primera sangre',
      descripcion: 'Gana tu primer combate',
      clave: 'w',
      meta: 1,
      recompensa: { h: 2, p: 2 },
      progreso: 1,
      reclamada: false,
      lista: true,
      grupo: 'Combate',
      es_general: true,
    },
    {
      identificador: 'g2',
      nombre: 'Veterano',
      descripcion: 'Gana 15 combates',
      clave: 'w',
      meta: 15,
      recompensa: { p: 10, n: 3, card: 3 },
      progreso: 1,
      reclamada: false,
      lista: false,
      grupo: 'Combate',
      es_general: true,
    },
  ],
  tracker: null,
}

const CATALOGO_MERCADO = {
  puestos: [
    {
      identificador: 'esp',
      vendedor: 'Herrero Qiu',
      frase: 'Un filo sin dueño solo es hierro.',
      lote: {
        nombre: 'Limaduras de Espada',
        material: 'p',
        cantidad: 3,
        costo: 14,
      },
    },
    {
      identificador: 'neu',
      vendedor: 'Pabellón de los Mil Caminos',
      frase: 'Todo cultivador necesita lo básico.',
      lote: null,
    },
  ],
  precios_venta: { h: 1, n: 8, p: 2 },
  pildoras_en_venta: [
    {
      identificador: 'vit',
      nombre: 'Elixir de Vitalidad',
      efecto: 'Recupera 8 de vida',
      tipo: 'Píldora de inicio',
      precio: 31,
      icono: 'heal',
      es_talisman: false,
      receta_aprendida: true,
    },
  ],
}

const CATALOGO_GACHA = {
  tickets: [
    {
      identificador: 'ticket_common',
      nombre: 'Fragmento de Alma Antigua',
      descripcion: 'Residual de intención.',
      icono: '🧿',
    },
    {
      identificador: 'ticket_premium',
      nombre: 'Lágrima de Dragón Ancestral',
      descripcion: 'Reliquia de poder.',
      icono: '💎',
    },
  ],
  pools: [
    {
      clave: 'STANDARD',
      identificador: 'pool_standard',
      nombre: 'Ecos Ancestrales',
      descripcion: 'Invocación general.',
      tipo_ticket: 'ticket_common',
      coste_por_tirada: 1,
      probabilidades: { common: 70, rare: 25, epic: 4.5, legendary: 0.5 },
      piedad: {
        garantizado_raro_tras: 10,
        garantizado_epico_tras: 50,
        clave: 'standard_pity',
      },
    },
    {
      clave: 'PREMIUM',
      identificador: 'pool_premium',
      nombre: 'Velo del Destino',
      descripcion: 'Mejores probabilidades.',
      tipo_ticket: 'ticket_premium',
      coste_por_tirada: 1,
      probabilidades: { common: 50, rare: 35, epic: 12, legendary: 3 },
      piedad: {
        garantizado_raro_tras: 5,
        garantizado_epico_tras: 30,
        clave: 'premium_pity',
      },
    },
  ],
  rarezas: [
    { clave: 'common', nombre: 'Común', color: '#6B7280', rareza_rn: 0 },
    { clave: 'rare', nombre: 'Raro', color: '#3B82F6', rareza_rn: 1 },
    { clave: 'epic', nombre: 'Épico', color: '#8B5CF6', rareza_rn: 2 },
    {
      clave: 'legendary',
      nombre: 'Legendario',
      color: '#F59E0B',
      rareza_rn: 3,
    },
  ],
}

function respuestaJson(contenido: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: async () => contenido,
  } as Response
}

/** Grupo del menú desplegable que contiene cada pestaña (`MENUS` del JS). */
const GRUPOS_PESTANA: Record<string, string> = {
  Alquimia: 'Cultivo',
  Mazmorras: 'Cultivo',
  Misiones: 'Cultivo',
  Mercado: 'Cartas',
  Mazos: 'Cartas',
  Formaciones: 'Cartas',
  Equipo: 'Cultivador',
  Trajes: 'Cultivador',
  Bolsa: 'Cultivador',
}

/** Navega como el jugador real: abre el grupo y pulsa su pestaña. */
async function irAPestana(titulo: string): Promise<void> {
  const grupo = GRUPOS_PESTANA[titulo]
  if (grupo) fireEvent.click(await screen.findByRole('button', { name: grupo }))
  fireEvent.click(await screen.findByRole('button', { name: titulo }))
}

/** Router de mocks por URL — imita todos los endpoints del flujo.

`instantanea` sustituye al snapshot por defecto en la carga de la
partida (`GET/POST /api/game/viaje…`); sirve para forzar casos como
una partida sin secta confirmada (`sc: null`).
*/
function instalarFetch(
  instantanea: SnapshotPartida = SNAPSHOT,
): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(
    async (entrada: RequestInfo | URL, opciones?: RequestInit) => {
      const ruta = String(entrada)
      const metodo = opciones?.method ?? 'GET'
      const exito = (datos: unknown) => respuestaJson({ ok: true, data: datos })
      if (ruta.includes('/api/health')) {
        return exito({ version: '0.2.0', uptime: 1.5 })
      }
      if (ruta.includes('/api/data/narrativa')) {
        return exito({ narrativa: NARRATIVA })
      }
      if (ruta.includes('/api/data/sectas')) {
        return exito({ sectas: SECTAS })
      }
      if (ruta.includes('/api/data/cartas/ex/detalle')) {
        return exito({
          carta: {
            identificador: 'ex',
            nombre: 'Filo Exilio',
            tipo: 'C',
            rareza: 3,
            secta_visible: 'Espada Celestial',
            coste_qi: 3,
            precio: 45,
            descripcion: ['Daña al entrar.'],
            estadisticas: [
              ['Ataque', '4'],
              ['Vida', '2'],
            ],
            acumulacion: null,
            propiedades: [],
            obtencion: ['Mercado de la secta'],
            es_abismo: false,
          },
        })
      }
      if (ruta.includes('/api/data/cartas')) {
        return exito({ cartas: CARTAS })
      }
      if (ruta.includes('/api/data/enemigos')) {
        return exito({ enemigos: ENEMIGOS })
      }
      if (ruta.includes('/api/data/alquimia')) {
        return exito(CATALOGO_ALQUIMIA)
      }
      if (ruta.includes('/api/data/mercado')) {
        return exito(CATALOGO_MERCADO)
      }
      if (ruta.includes('/api/data/gacha')) {
        return exito(CATALOGO_GACHA)
      }
      if (ruta.includes('/api/data/mazmorras')) {
        return exito({ mazmorras: MAZMORRAS })
      }
      if (ruta.includes('/api/data/bestias')) {
        return exito({ bestias: BESTIAS })
      }
      if (ruta.includes('/api/data/equipo')) {
        return exito({ equipo: CATALOGO_EQUIPO })
      }
      if (ruta.includes('/api/data/trajes')) {
        return exito({ trajes: CATALOGO_TRAJES })
      }
      if (ruta.includes('/api/game/viaje/misiones/reclamar')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Misión cumplida: Primera sangre. Recibes: +2 hierbas, +2 polvo de jade',
          tes: false,
          carta: null,
          receta: null,
          snapshot: { ...SNAPSHOT, qd: { g1: 1 } },
        })
      }
      if (ruta.includes('/api/game/viaje/misiones/seguir')) {
        return exito({
          slot: 'viaje',
          track: 'g1',
          snapshot: { ...SNAPSHOT, qs: { ...SNAPSHOT.qs, track: 'g1' } },
        })
      }
      if (ruta.includes('/api/game/viaje/misiones')) {
        return exito(MISIONES_LISTA)
      }
      if (ruta.includes('/api/game/viaje/mercado/comprar-material')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Compraste 3 polvo de jade (Limaduras de Espada).',
          snapshot: { ...SNAPSHOT, stn: SNAPSHOT.stn - 14 },
        })
      }
      if (ruta.includes('/api/game/viaje/mercado/comprar')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Compraste «Filo Exilio» por 45 piedras espirituales.',
          snapshot: {
            ...SNAPSHOT,
            stn: 0,
            col: { ...SNAPSHOT.col, ex: 1 },
          },
        })
      }
      if (ruta.includes('/api/game/viaje/mercado/vender')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Vendiste 1 de hierbas por 1 piedras espirituales.',
          piedras: 1,
          snapshot: {
            ...SNAPSHOT,
            stn: SNAPSHOT.stn + 1,
            mat: { ...SNAPSHOT.mat, h: SNAPSHOT.mat.h - 1 },
          },
        })
      }
      if (ruta.includes('/api/game/viaje/gacha/tirar')) {
        return exito({
          slot: 'viaje',
          mensaje: '✨ Ceremonia Completada — Has obtenido 1 Ecos del Sendero.',
          resultados: [
            {
              tipo: 'carta',
              carta: 'ev',
              nombre: 'Espectro de la Espada',
              rareza: 'rare',
              descripcion: 'Técnica o Artefacto del Sendero',
            },
          ],
          tickets_restantes: 4,
          piedad: 1,
          snapshot: {
            ...SNAPSHOT,
            gt: { ...SNAPSHOT.gt, ticket_common: 4 },
            gp: { ...SNAPSHOT.gp, standard_pity: 1 },
          },
        })
      }
      if (ruta.includes('/api/game/viaje/alquimia/elaborar')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Elaboraste: Elixir de Vitalidad',
          snapshot: { ...SNAPSHOT, pil: { vit: 2 } },
        })
      }
      if (ruta.includes('/api/game/viaje/alquimia/fusionar')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Fusión: obtuviste Espada Menor (Poco común)',
          carta: 'ev',
          snapshot: { ...SNAPSHOT, col: { cf: 0, ev: 2 } },
        })
      }
      if (ruta.includes('/api/game/viaje/mazos/0/anadir')) {
        return exito({
          slot: 'viaje',
          mensaje: '',
          snapshot: {
            ...SNAPSHOT,
            dk: [{ n: 'Mazo Sabio', c: { cf: 3, ev: 1, pq: 1 } }],
          },
        })
      }
      if (ruta.includes('/api/game/viaje/mazos')) {
        // crear y demás acciones de mazos
        return exito({
          slot: 'viaje',
          mensaje: '',
          snapshot: {
            ...SNAPSHOT,
            dk: [...SNAPSHOT.dk, { n: 'Mazo 2', c: {} }],
          },
        })
      }
      if (ruta.includes('/api/game/viaje/secta') && metodo === 'POST') {
        const cuerpo = JSON.parse(String(opciones?.body ?? '{}')) as {
          secta?: string
        }
        return exito({
          slot: 'viaje',
          snapshot: {
            ...instantanea,
            sect: cuerpo.secta ?? instantanea.sect,
            sc: cuerpo.secta ?? instantanea.sc,
            pil: { ...instantanea.pil, tes: (instantanea.pil.tes ?? 0) + 1 },
          },
        })
      }
      if (ruta.includes('/api/game/new') && metodo === 'POST') {
        return exito({ slot: 'viaje', snapshot: instantanea })
      }
      if (ruta.includes('/api/game/viaje') && metodo === 'GET') {
        return exito({ slot: 'viaje', snapshot: instantanea })
      }
      throw new Error(`ruta sin mock: ${metodo} ${ruta}`)
    },
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  localStorage.clear()
})

// El combate se prueba aquí sólo como contrato: el shell le pasa
// `onMorir` y éste vuelve a la bienvenida (`reborn()` del monolito).
vi.mock('./pantallas/Combate', async (importOriginal) => {
  await importOriginal<typeof import('./pantallas/Combate')>()
  return {
    default: function CombateDePrueba(props: { onMorir?: () => void }) {
      return (
        <div>
          <span>Combate de prueba</span>
          <button type="button" onClick={() => props.onMorir?.()}>
            Simular muerte
          </button>
        </div>
      )
    },
  }
})

describe('flujo del shell (slot fijo «viaje»)', () => {
  it('entra directo al Campamento sin gestionar slots', async () => {
    instalarFetch()
    render(<App />)

    expect(await screen.findByText('Sendero del Inmortal')).toBeTruthy()
    expect(await screen.findByText(/En el principio/)).toBeTruthy()
    expect(screen.getByText(/Backend v0\.2\.0/)).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: '▶ Jugar' }))

    // entra directo a la pestaña Campamento (sin pantalla de partidas)
    expect(
      await screen.findByRole('heading', { name: 'Campamento' }),
    ).toBeTruthy()
    expect(screen.queryByText('Tus partidas')).toBeNull()
    expect(await screen.findByText('Reino:')).toBeTruthy()
    expect(screen.getByText('Mortal')).toBeTruthy()
    expect(screen.getByText('24/30')).toBeTruthy() // vida del héroe
    expect(
      await screen.findByRole('heading', {
        name: /Cultivador de Espada Celestial/,
      }),
    ).toBeTruthy()
  })

  it('al recargar vuelve a la pestaña guardada sin pasar por la bienvenida', async () => {
    instalarFetch()
    // simula la persistencia de una sesión previa en el Mercado
    localStorage.setItem(
      'sdi_pantalla',
      JSON.stringify({ pestana: 'mkt', combate: null }),
    )
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Mercado del Sendero' }),
    ).toBeTruthy()
    expect(screen.queryByText('Sendero del Inmortal')).toBeNull()
  })

  it('elabora una píldora en la pestaña Alquimia', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    await irAPestana('Alquimia')
    expect(
      await screen.findByRole('heading', { name: 'Taller de alquimia' }),
    ).toBeTruthy()

    // recetario abierto por defecto: 2 aprendidas de 3 en el catálogo
    expect(await screen.findByText(/Recetario secreto \(2\/3\)/)).toBeTruthy()
    // la receta no aprendida no revela su nombre, como en el monolito
    expect(screen.getAllByText('🔒 Receta secreta').length).toBe(1)

    // elaborar el elixir aprendido y asequible
    const botonElaborar = await screen.findByRole('button', {
      name: /Elixir de Vitalidad/,
    })
    expect((botonElaborar as HTMLButtonElement).disabled).toBe(false)
    fireEvent.click(botonElaborar)

    expect(await screen.findByText('Elaboraste: Elixir de Vitalidad')).toBeTruthy()
    expect(screen.getByText('(tienes 2)')).toBeTruthy() // pil vit 1 → 2
  })

  it('fusiona 3 copias con confirmación', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    await irAPestana('Alquimia')

    fireEvent.click(await screen.findByRole('button', { name: /Fusión y refinado/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Fusionar x3' }))

    const dialogo = await screen.findByRole('dialog', { name: 'Fusión' })
    expect(dialogo.textContent).toContain('Fusionar «Corte Veloz»')
    fireEvent.click(screen.getByRole('button', { name: 'Fusionar' }))

    expect(
      await screen.findByText('Fusión: obtuviste Espada Menor (Poco común)'),
    ).toBeTruthy()
  })

  it('muestra sectas y bestiario en la pestaña Guía', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    fireEvent.click(await screen.findByRole('button', { name: 'Guía' }))
    expect(
      await screen.findByRole('heading', { name: /Guía del Sendero/ }),
    ).toBeTruthy()
    // sección Introducción por defecto (GB.int)
    expect(await screen.findByRole('heading', { name: 'Objetivo' })).toBeTruthy()
    // cambiar a la sección Cartas (glosario)
    fireEvent.click(screen.getByRole('tab', { name: /Cartas/ }))
    expect(
      await screen.findByRole('heading', { name: /Glosario de efectos/ }),
    ).toBeTruthy()
    expect(screen.getByText(/Provocar:/)).toBeTruthy()
    expect(await screen.findByText('Espada Celestial')).toBeTruthy()
    expect(await screen.findByText(/Corte Veloz/)).toBeTruthy() // mazo base
    expect(await screen.findByText(/Bestiario \(1 enemigos\)/)).toBeTruthy()
  })

  it('gestiona mazos: crear vacío y editar con + de cartas', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    await irAPestana('Mazos')
    expect(await screen.findByRole('heading', { name: 'Mazos' })).toBeTruthy()
    expect(await screen.findByText('Mazo automático')).toBeTruthy()
    expect(await screen.findByText('Mazo Sabio')).toBeTruthy()
    expect(
      await screen.findByText('4/40 cartas · incompleto'),
    ).toBeTruthy()

    // crear un mazo vacío
    fireEvent.click(screen.getByRole('button', { name: '＋ Mazo vacío' }))
    expect(await screen.findByText('Mazo 2')).toBeTruthy()

    // editar el primero: cabecera con nombre y curva de coste
    const botonesEditar = await screen.findAllByRole('button', {
      name: 'Editar',
    })
    fireEvent.click(botonesEditar[0])
    expect(
      await screen.findByRole('button', { name: '‹ Mazos' }),
    ).toBeTruthy()
    expect(screen.getByLabelText('Nombre del mazo')).toBeTruthy()
    expect(screen.getByLabelText('Curva de coste')).toBeTruthy()

    // añadir una carta neutral usable a 3 sin coleccionar
    const botonMas = await screen.findByRole('button', {
      name: 'Añadir Poción de Qi',
    })
    expect((botonMas as HTMLButtonElement).disabled).toBe(false)
    fireEvent.click(botonMas)
    expect(await screen.findByText('5/40')).toBeTruthy()

    // las filas muestran la descripción de efectos (`descH`/`FRd`)
    expect(
      await screen.findByText('+2 Qi'),
    ).toBeTruthy()
    expect(screen.getByText('Provocar')).toBeTruthy()
  })

  it('gestiona el mercado: pestaña, compra de lote con confirmación', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    await irAPestana('Mercado')
    expect(await screen.findByRole('heading', { name: 'Mercado del Sendero' })).toBeTruthy()
    expect(await screen.findByText(/Herrero Qiu/)).toBeTruthy()
    expect(screen.getByText(/Un filo sin dueño/)).toBeTruthy()

    // cartas del puesto esp (ex no es inicial)
    expect(await screen.findByText('Filo Exilio')).toBeTruthy()
    // cf es carta inicial: no se lista
    expect(screen.queryByText('Corte Veloz')).toBeNull()
    // arte ilustrado de cada producto (`art()` del monolito)
    expect(document.querySelectorAll('.arte-carta svg.art').length).toBeGreaterThan(0)

    // comprar lote con confirmación
    fireEvent.click(screen.getByRole('button', { name: '💎 14' }))
    const dialogo = await screen.findByRole('dialog', { name: 'Compra' })
    expect(dialogo.textContent).toContain('Limaduras de Espada')
    fireEvent.click(screen.getByRole('button', { name: 'Comprar' }))
    expect(
      await screen.findByText(
        'Compraste 3 polvo de jade (Limaduras de Espada).',
      ),
    ).toBeTruthy()
  })

  it('vende materiales en el puesto General', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    await irAPestana('Mercado')

    fireEvent.click(await screen.findByRole('tab', { name: 'General' }))
    expect(await screen.findByText('Vender materiales')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Vender 💎 1/ }))
    expect(
      await screen.findByText(
        'Vendiste 1 de hierbas por 1 piedras espirituales.',
      ),
    ).toBeTruthy()
  })

  it('abre el detalle de carta y compra con confirmación', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    await irAPestana('Mercado')

    fireEvent.click(
      await screen.findByRole('button', {
        name: 'Ver detalles de Filo Exilio',
      }),
    )
    const detalle = await screen.findByRole('dialog', {
      name: 'Detalle de Filo Exilio',
    })
    expect(detalle.textContent).toContain('Daña al entrar.')
    fireEvent.click(screen.getByRole('button', { name: /Comprar por/ }))

    const dialogo = await screen.findByRole('dialog', { name: 'Compra' })
    expect(dialogo.textContent).toContain('Filo Exilio')
    fireEvent.click(screen.getByRole('button', { name: 'Comprar' }))
    expect(
      await screen.findByText(
        'Compraste «Filo Exilio» por 45 piedras espirituales.',
      ),
    ).toBeTruthy()
  })

  it('invoca en el gacha y muestra resultados', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    fireEvent.click(await screen.findByRole('button', { name: 'Gacha' }))
    expect(
      await screen.findByRole('heading', {
        name: 'Ceremonia de Adivinación',
      }),
    ).toBeTruthy()
    expect(screen.getAllByText(/Ecos Ancestrales/).length).toBeGreaterThan(0)
    expect(screen.getByText(/Tienes: 5/)).toBeTruthy()
    expect(screen.getByText(/0 \/ 50/)).toBeTruthy()

    fireEvent.click(
      await screen.findByRole('button', { name: /Escuchar un Eco/ }),
    )
    expect(
      await screen.findByText(
        '✨ Ceremonia Completada — Has obtenido 1 Ecos del Sendero.',
      ),
    ).toBeTruthy()
    expect(await screen.findByText('Espectro de la Espada')).toBeTruthy()
    expect(screen.getAllByText('Raro').length).toBeGreaterThan(0)
    expect(screen.getByText(/Tienes: 4/)).toBeTruthy()
  })

  it('muestra error y permite reintentar si el backend no responde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    render(<App />)

    const aviso = await screen.findByRole('alert')
    expect(aviso.textContent).toContain('Sin conexión con el backend.')
    expect(aviso.textContent).toContain('No se pudo contactar con el backend')

    // el backend vuelve: reintentar carga el splash completo
    instalarFetch()
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText(/En el principio/)).toBeTruthy()
    expect(screen.getByRole('button', { name: '▶ Jugar' })).toBeTruthy()
  })
})

describe('pestañas nuevas (Bolsa, Mazmorras, Misiones) y reinicio', () => {
  afterEach(cleanup)

  it('Bolsa muestra materiales, píldoras y recetas', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    await irAPestana('Bolsa')
    expect(await screen.findByText('Bolsa Qiankun')).toBeTruthy()
    expect(screen.getByText('Piedras espirituales')).toBeTruthy()
    expect(screen.getByText('Hierbas espirituales')).toBeTruthy()
    // «Elixir de Vitalidad» aparece en píldoras y en recetas → getAll
    expect(screen.getAllByText(/Elixir de Vitalidad/).length).toBeGreaterThan(0)
    expect(screen.getByText('Recetas aprendidas')).toBeTruthy()
    expect(screen.getByText('Armaduras y artefactos')).toBeTruthy()
  })

  it('Equipo y Trajes se abren desde el menú Cultivador', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    // el grupo Cultivador ahora contiene Equipo, Trajes y Bolsa
    fireEvent.click(await screen.findByRole('button', { name: 'Cultivador' }))
    expect(await screen.findByRole('button', { name: 'Equipo' })).toBeTruthy()
    expect(await screen.findByRole('button', { name: 'Trajes' })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Equipo' }))
    expect(
      await screen.findByRole('heading', { name: 'Equipo del cultivador' }),
    ).toBeTruthy()
    expect(screen.getAllByText('Vacío').length).toBe(6)
    expect(screen.getByText(/Diadema de Jade/)).toBeTruthy()

    fireEvent.click(await screen.findByRole('button', { name: 'Cultivador' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Trajes' }))
    expect(
      await screen.findByRole('heading', { name: 'Armario del cultivador' }),
    ).toBeTruthy()
    expect(screen.getAllByRole('button', { name: /Traje/ }).length).toBe(6)
  })

  it('Misiones lista objetivos y permite reclamar la lista', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    await irAPestana('Misiones')
    // el <h1> es el único texto exacto «Misiones» (la pestaña es un botón)
    expect(await screen.findByRole('heading', { name: 'Misiones' })).toBeTruthy()
    expect(await screen.findByText('Primera sangre')).toBeTruthy()
    expect(screen.getByText('Veterano')).toBeTruthy()

    // g1 está lista (progreso 1/1) → botón reclamar
    const reclamar = await screen.findByRole('button', {
      name: /Lista · Reclamar/,
    })
    fireEvent.click(reclamar)
    expect(
      await screen.findByText(/Misión cumplida: Primera sangre/),
    ).toBeTruthy()
  })

  it('Mazmorras muestra la cueva y su pista', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    await irAPestana('Mazmorras')
    expect(await screen.findByRole('heading', { name: 'Mazmorras secretas' })).toBeTruthy()
    expect(
      await screen.findByText((_, nodo) => {
        const esB = nodo?.tagName === 'B'
        return (
          esB &&
          (nodo.textContent ?? '').includes('Cueva del Alquimista Olvidado')
        )
      }),
    ).toBeTruthy()
  })

  it('Reiniciar partida pide confirmación y vuelve a la bienvenida', async () => {
    const fetchMock = instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    expect(await screen.findByText('Campamento')).toBeTruthy()

    const boton = await screen.findByRole('button', {
      name: 'Reiniciar partida',
    })
    fireEvent.click(boton)
    // primer clic → cambia a confirmación (no borra aún)
    expect(
      await screen.findByRole('button', {
        name: /¿Seguro\? Se borra TODO el progreso/,
      }),
    ).toBeTruthy()

    // segundo clic → llama a POST /new y vuelve al splash
    fireEvent.click(
      screen.getByRole('button', {
        name: /¿Seguro\? Se borra TODO el progreso/,
      }),
    )
    await screen.findByText(/En el principio/)
    const llamadasNew = fetchMock.mock.calls.filter(
      (c) => String(c[0]).includes('/api/game/new') && c[1]?.method === 'POST',
    )
    expect(llamadasNew.length).toBeGreaterThanOrEqual(1)
  })
})

describe('menú desplegable y puerta de sectas', () => {
  it('agrupa las pestañas en desplegables con aria-expanded', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    const cultivo = await screen.findByRole('button', { name: 'Cultivo' })
    expect(cultivo.getAttribute('aria-expanded')).toBe('false')
    expect(cultivo.getAttribute('aria-haspopup')).toBe('true')
    // los ítems del grupo aún no existen
    expect(screen.queryByRole('button', { name: 'Alquimia' })).toBeNull()

    fireEvent.click(cultivo)
    expect(
      (await screen.findByRole('button', { name: 'Cultivo' })).getAttribute(
        'aria-expanded',
      ),
    ).toBe('true')
    expect(await screen.findByRole('button', { name: 'Alquimia' })).toBeTruthy()
    expect(await screen.findByRole('button', { name: 'Mazmorras' })).toBeTruthy()

    // elegirlo navega y cierra el desplegable
    fireEvent.click(await screen.findByRole('button', { name: 'Misiones' }))
    expect(
      await screen.findByRole('heading', { name: 'Misiones' }),
    ).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Mazmorras' })).toBeNull()

    // pulsar fuera cierra el menú abierto
    fireEvent.click(await screen.findByRole('button', { name: 'Cultivo' }))
    expect(
      (await screen.findByRole('button', { name: 'Cultivo' })).getAttribute(
        'aria-expanded',
      ),
    ).toBe('true')
    fireEvent.click(document.body)
    expect(screen.queryByRole('button', { name: 'Alquimia' })).toBeNull()
  })

  it('sin secta confirmada muestra la puerta y confirma por POST', async () => {
    const fetchMock = instalarFetch({ ...SNAPSHOT, sc: null })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    // gate en la pestaña Campaña (como `gate()` del monolito)
    expect(
      await screen.findByRole('heading', { name: 'Elige tu secta' }),
    ).toBeTruthy()
    expect(screen.queryByRole('heading', { name: 'Campamento' })).toBeNull()

    // elegir la secta abre el panel de confirmación
    fireEvent.click(await screen.findByRole('button', { name: /Espada Celestial/ }))
    const confirmar = await screen.findByRole('button', {
      name: 'Unirme para siempre',
    })
    fireEvent.click(confirmar)

    // POST …/secta y al campamento con la secta fijada
    expect(
      await screen.findByRole('heading', { name: 'Campamento' }),
    ).toBeTruthy()
    const llamadasSecta = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/api/game/viaje/secta') &&
        c[1]?.method === 'POST' &&
        String(c[1]?.body ?? '').includes('esp'),
    )
    expect(llamadasSecta.length).toBe(1)
  })

  it('la puerta cancela la selección sin enviar nada', async () => {
    const fetchMock = instalarFetch({ ...SNAPSHOT, sc: null })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    expect(
      await screen.findByRole('heading', { name: 'Elige tu secta' }),
    ).toBeTruthy()

    fireEvent.click(await screen.findByRole('button', { name: /Loto Púrpura/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('button', { name: 'Unirme para siempre' })).toBeNull()
    expect(
      fetchMock.mock.calls.filter(
        (c) =>
          String(c[0]).includes('/api/game/viaje/secta') &&
          c[1]?.method === 'POST',
      ).length,
    ).toBe(0)
    // sigue en la puerta
    expect(
      await screen.findByRole('heading', { name: 'Elige tu secta' }),
    ).toBeTruthy()
  })
})

describe('muerte en combate → bienvenida', () => {
  it('renacer vuelve al splash y limpia la pantalla guardada', async () => {
    guardarPantalla({ pestana: 'camp', combate: 0 })
    instalarFetch()
    render(<App />)

    // con pantalla guardada el shell abre el combate directo
    expect(await screen.findByText('Combate de prueba')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Simular muerte' }))

    // vuelve a la bienvenida («▶ Jugar») y sin destino persistido
    expect(await screen.findByText('Sendero del Inmortal')).toBeTruthy()
    expect(screen.getByRole('button', { name: '▶ Jugar' })).toBeTruthy()
    expect(screen.queryByText('Combate de prueba')).toBeNull()
    expect(leerPantalla()).toBeNull()
  })
})

describe('sectas v47 (imagen y mercado)', () => {
  it('la puerta ilustra las sectas v47 con el arte de su quinta carta', async () => {
    instalarFetch({ ...SNAPSHOT, sc: null })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    expect(
      await screen.findByRole('heading', { name: 'Elige tu secta' }),
    ).toBeTruthy()

    // v47 con mazo propio → arte de la 5ª carta (`art(S[k].l[4])`)
    const v47 = await screen.findByRole('button', {
      name: /Montaña Inmortal/,
    })
    expect(v47.querySelector('svg.art')).toBeTruthy()

    // la de carta base conserva su quinta carta
    const espada = screen.getByRole('button', { name: /Espada Celestial/ })
    expect(espada.querySelector('svg.art')).toBeTruthy()
  })

  it('el puesto de secta v47 vende las cartas de su secta, no las neutrales', async () => {
    instalarFetch({ ...SNAPSHOT, sc: 'mon' })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    await irAPestana('Mercado')
    expect(
      await screen.findByRole('heading', { name: 'Mercado del Sendero' }),
    ).toBeTruthy()

    // puesto de la secta v47 → una carta suya (que no es starter)
    expect(await screen.findByText('Avalancha')).toBeTruthy()
    // la 5ª carta base no se vende (ya viene en tu mazo)
    expect(screen.queryByText('Aprendiz de la Montaña')).toBeNull()
    // las neutrales no aparecen en un puesto de secta
    expect(screen.queryByText('Poción de Qi')).toBeNull()
    // las cartas de otra secta tampoco
    expect(screen.queryByText('Corte Veloz')).toBeNull()
  })
})

describe('catálogo de Formaciones (fr)', () => {
  it('abre desde el menú Cartas con reglas, lista y compra', async () => {
    instalarFetch({ ...SNAPSHOT })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))
    await irAPestana('Formaciones')

    expect(
      await screen.findByRole('heading', { name: 'Formaciones y Runas' }),
    ).toBeTruthy()
    expect(screen.getByText(/阵 Formación/)).toBeTruthy()
    expect(screen.getByText(/符 Runa/)).toBeTruthy()

    // contador y carta F del catálogo (con su compra en piedras)
    expect(await screen.findByText(/Tienes 0 de 1/)).toBeTruthy()
    expect(
      screen.getByText('Formación de Sangre Hirviente'),
    ).toBeTruthy()
    expect(
      screen.getByRole('button', { name: /Comprar 💎 45/ }),
    ).toBeTruthy()

    // filtros del monolito: «Las que tengo» deja la lista vacía
    fireEvent.click(screen.getByRole('button', { name: 'Las que tengo' }))
    expect(await screen.findByText(/No tienes cartas en esta categoría/)).toBeTruthy()
  })
})

describe('badge «!» de misiones listas', () => {
  it('aparece en el grupo Cultivo y en la pestaña Misiones', async () => {
    instalarFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '▶ Jugar' }))

    // el grupo que contiene Misiones lleva el «!» (`misReady`)
    const cultivo = await screen.findByRole('button', { name: 'Cultivo' })
    const badge = await within(cultivo).findByRole('status', {
      name: 'Misión lista para reclamar',
    })
    expect(badge.textContent).toBe('!')
    expect(cultivo.querySelector('.bang')).toBeTruthy()

    // y también el sub-botón Misiones con el menú abierto
    fireEvent.click(cultivo)
    const botonMisiones = await screen.findByRole('button', {
      name: /Misiones/,
    })
    expect(botonMisiones.querySelector('.bang')).toBeTruthy()
  })
})
