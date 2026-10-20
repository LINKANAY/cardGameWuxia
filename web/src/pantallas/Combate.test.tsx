/** Tests de la pantalla de Combate (mock de fetch, sin backend). */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Combate from './Combate'
import type {
  CartaCombate,
  EstadoCombate,
  EnemigoResumen,
  ResultadoCombate,
  SnapshotPartida,
} from '../api/tipos'

const SNAPSHOT: SnapshotPartida = {
  realm: 0,
  hp: 24,
  wins: [],
  col: { cf: 3 },
  sect: 'esp',
  mat: { h: 0, n: 0, p: 0 },
  stn: 0,
  dk: [],
  ad: -1,
  pil: { vit: 1, tes: 1, fue: 2 },
  of: {},
  rec: {},
  be: null,
  gr: {},
  eq: {},
  sc: null,
  du: {},
  dt: 0,
  bt: 0,
  qs: { track: '' },
  qd: {},
  gt: { ticket_common: 0, ticket_premium: 0 },
  gp: { standard_pity: 0, premium_pity: 0 },
}

const ENEMIGOS: EnemigoResumen[] = [
  {
    indice: 0,
    nombre_enemigo: 'Bandido de la Colina',
    secta: 'esp',
    nombre_nivel: 'La noche del despertar',
    vida: 26,
    dificultad: 0,
    origen: 'nivel',
    frase_inicio: '¡Ríndete!',
    historia: 'Una emboscada en el sendero.',
    indice_nivel: 0,
    texto_habilidades: 'Sin habilidades.',
  },
]

const PILDORAS = [
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
    nombre: 'Talismán de Escape',
    efecto: 'Huir del combate',
    coste: { h: 2 },
    es_combate: false,
    icono: 'tal',
  },
  {
    identificador: 'fue',
    nombre: 'Píldora de Fuego Interior',
    efecto: 'Daña 6 al enemigo',
    coste: { h: 1, n: 1 },
    es_combate: true,
    icono: 'dmg',
  },
]

const CARTAS = [
  {
    identificador: 'cf',
    nombre: 'Corte Fugaz',
    tipo: 'T',
    coste_qi: 1,
    ataque: null,
    vida: null,
    rareza: 0,
    secta: 'esp',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: [],
    texto: '',
    opciones: [],
  },
  {
    identificador: 'ld',
    nombre: 'Luz de Espada',
    tipo: 'T',
    coste_qi: 3,
    ataque: null,
    vida: null,
    rareza: 2,
    secta: 'esp',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: [],
    texto: '',
    opciones: [],
  },
  {
    identificador: 'ma',
    nombre: 'Maestro de la Espada',
    tipo: 'C',
    coste_qi: 4,
    ataque: 4,
    vida: 3,
    rareza: 1,
    secta: 'esp',
    es_neutral: false,
    reliquia: false,
    es_abismo: false,
    descripcion: [],
    texto: '',
    opciones: [],
  },
]

function carta(extra: Partial<CartaCombate> = {}): CartaCombate {
  return {
    id: 'cf',
    nombre: 'Corte Veloz',
    coste: 1,
    tipo: 'T',
    ataque: null,
    vida: null,
    lista: false,
    provocar: false,
    impetu: false,
    robar_vida: false,
    crece: null,
    usada: false,
    bestia: false,
    reliquia: false,
    dano_criatura: null,
    mejora_aliada: null,
    habilidad: null,
    descripcion: [],
    ...extra,
  }
}

function combateActivo(): EstadoCombate {
  return {
    activo: true,
    fin: '',
    lock: false,
    logs: ['<b>Héroe</b> roba 1 carta.'],
    jugador: {
      nombre: 'Cultivador',
      hp: 24,
      mx: 30,
      qi: 3,
      mq: 3,
      cap: 5,
      sh: 0,
      mazo: 20,
      cartas_mazo: [],
      mano: [carta()],
      tablero: [],
      vacio: [],
      turnos: 1,
      pouch: [],
      usos: 0,
      fm: null,
      rn: [],
      atkb: 0,
      bo: false,
      opa: 0,
      oph: 0,
      salvavidas: false,
    },
    enemigo: {
      nombre: 'Bandido de la Colina',
      hp: 26,
      mx: 30,
      qi: 2,
      mq: 3,
      cap: 5,
      sh: 0,
      mazo: 20,
      cartas_mazo: [],
      mano: [],
      tablero: [],
      vacio: [],
      turnos: 1,
      pouch: [],
      usos: 0,
      fm: null,
      rn: [],
      atkb: 0,
      bo: false,
      opa: 0,
      oph: 0,
      salvavidas: false,
    },
    indice_enemigo: 0,
    pd: [],
    vp_n: 0,
    ed: 0,
    ec: false,
    sel: -1,
    tg: null,
    ev: null,
    eventos: [],
    pildoras_stock: { vit: 1, tes: 1, fue: 2 },
  }
}

function resultado(
  combate: EstadoCombate,
  campaña: unknown[] = [],
): ResultadoCombate {
  return {
    slot: 'viaje',
    combate,
    campaña: campaña as ResultadoCombate['campaña'],
  }
}

function instalarFetch(rutas: Record<string, unknown>): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(async (entrada: RequestInfo | URL) => {
    const ruta = String(entrada)
    for (const [clave, datos] of Object.entries(rutas)) {
      if (ruta.includes(clave)) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, data: datos }),
        } as Response
      }
    }
    throw new Error(`ruta sin mock: ${ruta}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

/** Intro → Combatir → combate en marcha. */
async function abrirCombate(
  extra: Record<string, unknown> = {},
  propiedades: { onSalir?: () => void; onMorir?: () => void } = {},
) {
  const fetchMock = instalarFetch({
    '/api/data/enemigos': { enemigos: ENEMIGOS },
    '/api/data/alquimia': { pildoras: PILDORAS, forja: [] },
    '/api/data/cartas': { cartas: CARTAS },
    '/combate/iniciar': resultado(combateActivo()),
    ...extra,
    // al final: no debe tapar las rutas /combate/* más específicas
    '/api/game/viaje/combate': { combate: { activo: false } },
    '/api/game/viaje': { slot: 'viaje', snapshot: SNAPSHOT },
  })
  render(
    <Combate
      slot="viaje"
      indiceEnemigo={0}
      snapshot={SNAPSHOT}
      narrativa={null}
      onSnapshot={vi.fn()}
      onSalir={propiedades.onSalir ?? vi.fn()}
      onMorir={propiedades.onMorir}
    />,
  )
  fireEvent.click(await screen.findByRole('button', { name: 'Combatir' }))
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Combate', () => {
  it('muestra la intro con ficha del enemigo y píldoras antes de combatir', async () => {
    const fetchMock = instalarFetch({
      '/api/data/enemigos': { enemigos: ENEMIGOS },
      '/api/data/alquimia': { pildoras: PILDORAS, forja: [] },
      '/api/data/cartas': { cartas: CARTAS },
    })
    render(
      <Combate
        slot="viaje"
        indiceEnemigo={0}
        snapshot={SNAPSHOT}
        narrativa={null}
        onSnapshot={vi.fn()}
        onSalir={vi.fn()}
      />,
    )

    expect(
      await screen.findByRole('heading', { name: 'La noche del despertar' }),
    ).toBeTruthy()
    expect(screen.getByText('Bandido de la Colina')).toBeTruthy()
    expect(screen.getByText(/Una emboscada en el sendero/)).toBeTruthy()
    // vida escalada: base 26 + 2 por reino 0 → 26; daño ×1.0
    expect(screen.getByText(/26 vida\. Daño ×1\.0\./)).toBeTruthy()
    expect(screen.getByText(/Muerte permanente/)).toBeTruthy()
    // píldoras de inicio (vit, tes) y bolsa (fue)
    expect(screen.getByText(/Píldoras de inicio/)).toBeTruthy()
    expect(screen.getByText(/Bolsa de combate/)).toBeTruthy()
    // sin iniciar el combate todavía
    expect(
      fetchMock.mock.calls.some(([ruta]) =>
        String(ruta).includes('/combate/iniciar'),
      ),
    ).toBe(false)
  })

  it('inicia el combate y pinta barras, mano, slots y log', async () => {
    await abrirCombate()

    expect(await screen.findByText('Cultivador')).toBeTruthy()
    expect(screen.getByText('Bandido de la Colina')).toBeTruthy()
    expect(screen.getByRole('button', { name: /Corte Veloz/ })).toBeTruthy()
    // el log de combate está plegado tras un botón en la esquina
    const logToggle = screen.getByRole('button', { name: /Registro \(\d+\)/ })
    expect(logToggle).toBeTruthy()
    expect(screen.queryByText(/roba 1 carta/)).toBeNull()
    fireEvent.click(logToggle)
    expect(screen.getByText(/roba 1 carta/)).toBeTruthy()
    // casillas huecas del tablero (5 por lado, vacío)
    expect(document.querySelectorAll('.slot-celda').length).toBe(10)
  })

  it('reanuda un combate activo tras recargar, sin pasar por la intro', async () => {
    instalarFetch({
      '/api/data/enemigos': { enemigos: ENEMIGOS },
      '/api/data/alquimia': { pildoras: PILDORAS, forja: [] },
      '/api/data/cartas': { cartas: CARTAS },
      '/api/game/viaje/combate': { combate: combateActivo() },
      '/api/game/viaje': { slot: 'viaje', snapshot: SNAPSHOT },
    })
    render(
      <Combate
        slot="viaje"
        indiceEnemigo={0}
        snapshot={SNAPSHOT}
        narrativa={null}
        onSnapshot={vi.fn()}
        onSalir={vi.fn()}
      />,
    )

    // fase de combate directa: tablero visible y sin intro/Combatir
    expect(await screen.findByLabelText('Tablero enemigo')).toBeTruthy()
    expect(screen.getByText('Cultivador')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Combatir' })).toBeNull()
  })

  it('marca como «no» las cartas inasequibles', async () => {
    const estado = combateActivo()
    estado.jugador.qi = 0
    estado.jugador.mano = [carta({ nombre: 'Golpe Pesado', coste: 3 })]
    await abrirCombate({ '/combate/iniciar': resultado(estado) })

    const cartaBoton = await screen.findByRole('button', {
      name: /Golpe Pesado/,
    })
    expect(cartaBoton.className).toContain('no')
  })

  it('permite abrir el visor de mazo y del Agujero Negro (descartes)', async () => {
    const estado = combateActivo()
    estado.jugador.cartas_mazo = [
      carta({ id: 'mz1', nombre: 'Carta en Mazo' }),
    ]
    estado.jugador.vacio = [carta({ id: 'vd1', nombre: 'Carta Descartada' })]
    await abrirCombate({ '/combate/iniciar': resultado(estado) })

    expect(await screen.findByLabelText('Tablero enemigo')).toBeTruthy()

    // mazo
    fireEvent.click(screen.getByRole('button', { name: /mazo 20/ }))
    expect(await screen.findByText(/Carta en Mazo/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))

    // Agujero Negro (descartes)
    fireEvent.click(screen.getByRole('button', { name: /vacío 1/ }))
    expect(await screen.findByText(/Carta Descartada/)).toBeTruthy()
    expect(screen.getByText(/Agujero Negro \(descartes\)/)).toBeTruthy()
  })

  it('ofrece el botón de Bolsa en combate con los elementos cargados', async () => {
    const estado = combateActivo()
    estado.jugador.pouch = ['fue']
    estado.pildoras_stock = { fue: 2 }
    await abrirCombate({ '/combate/iniciar': resultado(estado) })

    expect(await screen.findByLabelText('Tablero enemigo')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /🎒 Bolsa \(1\)/ }))
    const dialogo = await screen.findByRole('dialog', {
      name: 'Bolsa de combate',
    })
    expect(
      within(dialogo).getByText(/Píldora de Fuego Interior/),
    ).toBeTruthy()
    expect(within(dialogo).getByText(/Daña 6 al enemigo/)).toBeTruthy()
    expect(within(dialogo).getByText(/Usos de bolsa: 0\/2/)).toBeTruthy()
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Cerrar' }))
    expect(screen.queryByRole('dialog', { name: 'Bolsa de combate' })).toBeNull()
  })

  it('pinta formación, runas, bonus de ataque y salvavidas (fmH/bdg)', async () => {
    const estado = combateActivo()
    estado.jugador.fm = {
      id: 'Y05',
      nombre: 'Formación de Sangre Hirviente',
      pa: 2,
      ph: 0,
      desc: ['Formación', 'Tus criaturas: +2 ATK'],
    }
    estado.jugador.rn = [
      {
        id: 'Y14',
        nombre: 'Runa del Eclipse',
        du: 2,
        desc: ['Runa · 2 turnos'],
      },
    ]
    estado.jugador.atkb = 3
    estado.jugador.salvavidas = true
    estado.jugador.mano = [
      carta({
        id: 'Y05',
        nombre: 'Formación de Sangre Hirviente',
        tipo: 'F',
        formacion: { pa: 2, ph: 0, ts: ['x', 1] },
      }),
    ]
    estado.jugador.tablero = [
      carta({
        id: 'cf',
        nombre: 'Corte Veloz',
        tipo: 'C',
        ataque: 3,
        vida: 1,
      }),
    ]
    await abrirCombate({ '/combate/iniciar': resultado(estado) })

    // fmH: 阵 con la formación y 符 con los turnos restantes de la runa
    expect(
      await screen.findByText('阵 Formación de Sangre Hirviente'),
    ).toBeTruthy()
    expect(screen.getByText('符 Runa del Eclipse · 2 t.')).toBeTruthy()
    // barra del héroe: bonus de ataque y salvavidas
    expect(screen.getByText('⚔+3')).toBeTruthy()
    expect(screen.getByText('☠ salvavidas')).toBeTruthy()

    // bdg de F en mano: badge de pa con su tooltip
    const botonF = screen.getByRole('button', {
      name: /Formación de Sangre Hirviente/,
    })
    const badgeF = botonF.querySelector('.badge-stat.batq')
    expect(badgeF?.textContent).toBe('+2')
    expect(badgeF?.getAttribute('title')).toBe(
      'Tus criaturas ganan +2 de ataque',
    )

    // bdg de criatura en tablero: ataque con el pa de la formación
    const criatura = screen.getByRole('button', { name: /Corte Veloz/ })
    const badgeA = criatura.querySelector('.badge-stat.batq')
    expect(badgeA?.textContent).toBe('5')
    expect(badgeA?.className).toContain('up')
    expect(badgeA?.getAttribute('title')).toContain(
      'incluye +2 de la formación',
    )
  })

  it('pide objetivo aliado para cartas con mejora_aliada (bf)', async () => {
    const estado = combateActivo()
    estado.jugador.mano = [
      carta({
        nombre: 'Bendición Menor',
        mejora_aliada: { ataque: 1, vida: 1 },
      }),
    ]
    estado.jugador.tablero = [
      carta({
        id: 'ev',
        nombre: 'Espectro de la Espada',
        tipo: 'C',
        ataque: 2,
        vida: 1,
        lista: true,
      }),
    ]
    await abrirCombate({ '/combate/iniciar': resultado(estado) })

    fireEvent.click(await screen.findByRole('button', { name: /Bendición/ }))
    expect(await screen.findByText(/criatura aliada/)).toBeTruthy()
  })

  it('muestra el modal de evento de mapa y permite resolverlo', async () => {
    const estado = combateActivo()
    estado.ev = {
      nombre: 'Cueva ancestral',
      texto: 'Una cueva sellada late con Qi antiguo.',
      opciones: ['Entrar: +3 Qi, pierdes 3 de vida', 'Ignorarla'],
    }
    const fetchMock = await abrirCombate({
      '/combate/iniciar': resultado(estado),
      '/combate/evento': resultado({ ...estado, ev: null, lock: false }),
    })

    expect(await screen.findByText('Cueva ancestral')).toBeTruthy()
    fireEvent.click(
      screen.getByRole('button', { name: /Entrar: \+3 Qi/ }),
    )
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([ruta]) =>
          String(ruta).includes('/combate/evento'),
        ),
      ).toBe(true),
    )
  })

  it('ofrece la bolsa de píldoras con usos 0/2', async () => {
    const estado = combateActivo()
    estado.jugador.pouch = ['fue']
    const fetchMock = await abrirCombate({
      '/combate/iniciar': resultado(estado),
      '/combate/usar-pildora': resultado({ ...estado, jugador: { ...estado.jugador, usos: 1 } }),
    })

    const bolsa = await screen.findByLabelText('Bolsa de píldoras')
    expect(bolsa.textContent).toContain('usos: 0/2')
    fireEvent.click(
      screen.getByRole('button', { name: /Píldora de Fuego Interior/ }),
    )
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([ruta]) =>
          String(ruta).includes('/combate/usar-pildora'),
        ),
      ).toBe(true),
    )
  })

  it('avisa con el modal EC si aún puede actuar antes de cerrar turno', async () => {
    const fetchMock = await abrirCombate()

    fireEvent.click(
      await screen.findByRole('button', { name: 'Terminar turno' }),
    )
    expect(await screen.findByText('¡Aún puedes jugar!')).toBeTruthy()
    // aún no se ha llamado al backend
    expect(
      fetchMock.mock.calls.some(([ruta]) =>
        String(ruta).includes('/combate/fin-turno'),
      ),
    ).toBe(false)

    fireEvent.click(screen.getByRole('button', { name: 'Sí, terminar turno' }))
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([ruta]) =>
          String(ruta).includes('/combate/fin-turno'),
        ),
      ).toBe(true),
    )
  })

  it('muestra el modal de exceso de mano y permite cancelarlo', async () => {
    const estado = combateActivo()
    estado.ed = 1
    const fetchMock = await abrirCombate({
      '/combate/iniciar': resultado(estado),
      '/combate/descartar-cancelar': resultado({ ...estado, ed: 0 }),
    })

    expect(await screen.findByText(/Descarta 1 carta/)).toBeTruthy()
    fireEvent.click(
      screen.getByRole('button', { name: 'Volver y jugar más cartas' }),
    )
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([ruta]) =>
          String(ruta).includes('/combate/descartar-cancelar'),
        ),
      ).toBe(true),
    )
  })

  it('al ganar muestra recompensas con nombre y permite reclamar una', async () => {
    const fin = combateActivo()
    fin.fin = 'w'
    const onSalir = vi.fn()
    const fetchMock = instalarFetch({
      '/api/data/enemigos': { enemigos: ENEMIGOS },
      '/api/data/alquimia': { pildoras: PILDORAS, forja: [] },
      '/api/data/cartas': { cartas: CARTAS },
      '/combate/iniciar': resultado(fin, [
        {
          tipo: 'victoria',
          recompensas: ['cf', 'ld', 'ma'],
          materiales: { h: 1, n: 0, p: 2, s: 5 },
        },
      ]),
      '/combate/reclamar': { carta: 'ld', copias: 1, recompensas: [] },
      '/combate/cerrar': { fin: 'w' },
    })
    render(
      <Combate
        slot="viaje"
        indiceEnemigo={0}
        snapshot={SNAPSHOT}
        narrativa={null}
        onSnapshot={vi.fn()}
        onSalir={onSalir}
      />,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Combatir' }))
    expect(await screen.findByText('¡Victoria!')).toBeTruthy()
    // recompensas por NOMBRE (catálogo), no ids crudos
    expect(screen.getByText('Corte Fugaz')).toBeTruthy()
    expect(screen.getByText('Luz de Espada')).toBeTruthy()
    expect(screen.getByText('Maestro de la Espada')).toBeTruthy()
    expect(screen.queryByText('cf, ld, ma')).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: /Luz de Espada/ }))
    expect(
      await screen.findByText(/Carta añadida a tu colección/),
    ).toBeTruthy()
    expect(screen.getByText('Luz de Espada')).toBeTruthy()
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([ruta]) =>
          String(ruta).includes('/combate/reclamar'),
        ),
      ).toBe(true),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    await waitFor(() => expect(onSalir).toHaveBeenCalled())
  })

  it('sin recompensas el modal de victoria permite continuar directo', async () => {
    const fin = combateActivo()
    fin.fin = 'w'
    const onSalir = vi.fn()
    instalarFetch({
      '/api/data/enemigos': { enemigos: ENEMIGOS },
      '/api/data/alquimia': { pildoras: PILDORAS, forja: [] },
      '/api/data/cartas': { cartas: CARTAS },
      '/combate/iniciar': resultado(fin),
      '/combate/cerrar': { fin: 'w' },
    })
    render(
      <Combate
        slot="viaje"
        indiceEnemigo={0}
        snapshot={SNAPSHOT}
        narrativa={null}
        onSnapshot={vi.fn()}
        onSalir={onSalir}
      />,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Combatir' }))
    expect(await screen.findByText('¡Victoria!')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    await waitFor(() => expect(onSalir).toHaveBeenCalled())
  })
})

describe('Combate · muerte y arte', () => {
  it('al morir ofrece renacer como nuevo cultivador', async () => {
    const fin = combateActivo()
    fin.fin = 'l'
    const onMorir = vi.fn()
    const onSalir = vi.fn()
    const fetchMock = await abrirCombate(
      { '/combate/iniciar': resultado(fin), '/combate/cerrar': { fin: 'l' } },
      { onMorir, onSalir },
    )

    expect(await screen.findByText('Has caído…')).toBeTruthy()
    const renacer = await screen.findByRole('button', {
      name: 'Renacer como nuevo cultivador',
    })
    fireEvent.click(renacer)

    await waitFor(() => expect(onMorir).toHaveBeenCalled())
    // cierra la sesión de combate antes de salir
    expect(
      fetchMock.mock.calls.some(([ruta]) =>
        String(ruta).includes('/combate/cerrar'),
      ),
    ).toBe(true)
    expect(onSalir).not.toHaveBeenCalled()
  })

  it('pinta el arte de las cartas en mano y en las recompensas', async () => {
    const fin = combateActivo()
    fin.fin = 'w'
    await abrirCombate({
      '/combate/iniciar': resultado(fin, [
        { tipo: 'victoria', recompensas: ['cf', 'ld'], materiales: {} },
      ]),
      '/combate/cerrar': { fin: 'w' },
    })

    // mano: cada carta lleva su ilustración (art() del monolito)
    const mano = await screen.findByRole('list', { name: 'Mano' })
    const conArte = mano.querySelectorAll('.cartacomate .carta-arte svg.art')
    expect(conArte.length).toBeGreaterThan(0)

    // recompensas de la victoria, también ilustradas
    expect(await screen.findByText('¡Victoria!')).toBeTruthy()
    const recompensas = document.querySelectorAll(
      '.recompensa-carta .recompensa-arte svg.art',
    )
    expect(recompensas.length).toBe(2)
  })
})

describe('Combate · cabecera de la carta', () => {
  it('muestra ataque y vida en círculos como el coste de Qi', async () => {
    const estado = combateActivo()
    estado.jugador.mano = [
      carta(),
      carta({
        id: 'ev',
        nombre: 'Espectro de la Espada',
        tipo: 'C',
        ataque: 3,
        vida: 1,
      }),
    ]
    await abrirCombate({ '/combate/iniciar': resultado(estado) })

    const mano = await screen.findByRole('list', { name: 'Mano' })
    const ataque = mano.querySelector('.badge-stat.batq')
    const vida = mano.querySelector('.badge-stat.bvid')
    expect(ataque?.textContent).toBe('3')
    expect(vida?.textContent).toBe('1')
    // el Qi sigue en su círculo y ya no hay texto a/v suelto
    expect(mano.querySelector('.coste')).toBeTruthy()
    expect(mano.querySelector('.stats')).toBeNull()
  })
})
