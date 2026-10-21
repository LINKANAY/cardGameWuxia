/** Tests de la pestaña Jardín: cuadrícula, siembra, riego y cosecha. */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Jardin from './Jardin'
import type {
  CatalogoJardin,
  CasillaJardin,
  EstadoJardin,
  SnapshotPartida,
} from '../api/tipos'

const SNAPSHOT: SnapshotPartida = {
  realm: 0,
  hp: 30,
  wins: [],
  col: {},
  sect: 'esp',
  mat: { h: 20, n: 10, p: 5 },
  stn: 100,
  dk: [],
  ad: -1,
  pil: {},
  of: {},
  rec: {},
  be: null,
  gr: {},
  eq: {},
  sc: 'esp',
  du: {},
  dt: 0,
  bt: 0,
  qs: { track: '' },
  qd: {},
  gt: { ticket_common: 0, ticket_premium: 0 },
  gp: { standard_pity: 0, premium_pity: 0 },
  jdn: { nivel: 0, casillas: [null, null, null, null], formacion: null },
  sd: { hs: 1, ff: 2 },
  fg: { fc1: 1 },
}

const CATALOGO: CatalogoJardin = {
  hierbas: [
    {
      identificador: 'hs',
      nombre: 'Hierba Espiritual',
      glifo: '灵',
      rareza: 0,
      duracion_ms: 120_000,
      rendimiento: 1,
      reino_min: 0,
    },
    {
      identificador: 'ff',
      nombre: 'Fruto de Escarcha',
      glifo: '霜',
      rareza: 1,
      duracion_ms: 360_000,
      rendimiento: 1,
      reino_min: 1,
    },
    {
      identificador: 'nf',
      nombre: 'Núcleo de Fénix',
      glifo: '凤',
      rareza: 4,
      duracion_ms: 2_700_000,
      rendimiento: 3,
      reino_min: 7,
    },
  ],
  formaciones: [
    {
      identificador: 'fc1',
      nombre: 'Círculo de Rocío',
      glifo: '露',
      rareza: 0,
      descuento: 0.05,
      descripcion: 'El rocío eterno moja las raíces mientras duermen.',
    },
    {
      identificador: 'fc3',
      nombre: 'Sello de Raíces',
      glifo: '根',
      rareza: 1,
      descuento: 0.1,
      descripcion: 'Las raíces beben del tiempo detenido.',
    },
  ],
  mejoras: [
    { nivel: 0, casillas: 4, coste: {}, reino_min: 0 },
    {
      nivel: 1,
      casillas: 6,
      coste: { h: 15, n: 5, p: 5 },
      reino_min: 2,
    },
    {
      nivel: 2,
      casillas: 9,
      coste: { h: 30, n: 15, p: 15 },
      reino_min: 5,
    },
    {
      nivel: 3,
      casillas: 12,
      coste: { h: 60, n: 30, p: 30 },
      reino_min: 8,
    },
  ],
}

function casilla(
  planta: string,
  extras: Partial<CasillaJardin> = {},
): CasillaJardin {
  return {
    planta,
    siembra: 1_760_000_000_000,
    reducido: 0,
    duracion_ms: 120_000,
    restante_ms: 0,
    progreso: 1,
    listo: true,
    coste_piedras: 0,
    ...extras,
  }
}

const ESTADO_BASE: EstadoJardin = {
  slot: 'viaje',
  nivel: 0,
  casillas: [
    casilla('hs'),
    casilla('ff', {
      duracion_ms: 360_000,
      restante_ms: 100_000,
      progreso: 0.72,
      listo: false,
      coste_piedras: 90,
    }),
    null,
    null,
  ],
  formacion: null,
  semillas: { hs: 1, ff: 2 },
  formaciones: { fc1: 1 },
  reino: 3,
  materiales: { h: 20, n: 10, p: 5 },
  piedras: 100,
  siguiente_mejora: {
    nivel: 1,
    casillas: 6,
    coste: { h: 15, n: 5, p: 5 },
    reino_min: 2,
  },
  ahora: 1_760_000_100_000,
}

const ESTADO_SIEMBRADO: EstadoJardin = {
  ...ESTADO_BASE,
  casillas: [
    ESTADO_BASE.casillas[0],
    ESTADO_BASE.casillas[1],
    casilla('hs', { restante_ms: 120_000, progreso: 0, listo: false, coste_piedras: 94 }),
    null,
  ],
  semillas: { ff: 2 },
}

const ESTADO_RIEGADO: EstadoJardin = {
  ...ESTADO_BASE,
  casillas: [
    ESTADO_BASE.casillas[0],
    casilla('ff', { duracion_ms: 360_000 }),
    null,
    null,
  ],
  piedras: 10,
}

const ESTADO_COSECHADO: EstadoJardin = {
  ...ESTADO_BASE,
  casillas: [null, ESTADO_BASE.casillas[1], null, null],
  materiales: { h: 21, n: 10, p: 5 },
}

const ESTADO_MEJORADO: EstadoJardin = {
  ...ESTADO_BASE,
  nivel: 1,
  casillas: [...ESTADO_BASE.casillas, null, null],
  materiales: { h: 5, n: 5, p: 0 },
  siguiente_mejora: {
    nivel: 2,
    casillas: 9,
    coste: { h: 30, n: 15, p: 15 },
    reino_min: 5,
  },
}

const ESTADO_CON_FORMACION: EstadoJardin = {
  ...ESTADO_BASE,
  formacion: 'fc1',
}

type FirmaFetch = (ruta: string, opciones?: RequestInit) => Promise<Response>

function instalarFetch(
  opciones: { estado?: EstadoJardin; errorCosechar?: boolean } = {},
): ReturnType<typeof vi.fn> {
  const estado = opciones.estado ?? ESTADO_BASE
  const exito = (datos: unknown) =>
    ({
      ok: true,
      status: 200,
      json: async () => ({ ok: true, data: datos }),
    }) as Response
  const fallo = (code: string, mensaje: string) =>
    ({
      ok: false,
      status: 400,
      json: async () => ({ ok: false, error: { code, message: mensaje } }),
    }) as Response

  const funcion = vi.fn<FirmaFetch>(async (entrada, opcionesDeLlamada) => {
    const ruta = String(entrada)
    const cuerpo = String(opcionesDeLlamada?.body ?? '{}')

    if (ruta.includes('/api/data/jardin')) return exito(CATALOGO)
    if (ruta.includes('/jardin/sembrar')) {
      return exito({
        ...ESTADO_SIEMBRADO,
        resultado: { indice: 2, planta: 'hs' },
        snapshot: { ...SNAPSHOT, sd: { ff: 2 } },
      })
    }
    if (ruta.includes('/jardin/acelerar')) {
      return exito({
        ...ESTADO_RIEGADO,
        resultado: {
          indice: 1,
          reducido: 260_000,
          restante_ms: 0,
          gastadas: 90,
        },
        snapshot: { ...SNAPSHOT, stn: 10 },
      })
    }
    if (ruta.includes('/jardin/cosechar')) {
      if (opciones.errorCosechar) {
        return fallo('planta_pendiente', 'La planta aún está creciendo')
      }
      return exito({
        ...ESTADO_COSECHADO,
        resultado: { indice: 0, planta: 'hs', hierbas: 1 },
        snapshot: { ...SNAPSHOT, mat: { h: 21, n: 10, p: 5 } },
      })
    }
    if (ruta.includes('/jardin/mejorar')) {
      return exito({
        ...ESTADO_MEJORADO,
        resultado: {
          nivel: 1,
          casillas: 6,
          coste: { h: 15, n: 5, p: 5 },
        },
        snapshot: { ...SNAPSHOT, mat: { h: 5, n: 5, p: 0 } },
      })
    }
    if (ruta.includes('/jardin/formacion')) {
      const identificador = (JSON.parse(cuerpo) as { identificador: string | null })
        .identificador
      return exito({
        ...(identificador ? ESTADO_CON_FORMACION : ESTADO_BASE),
        snapshot: { ...SNAPSHOT, jdn: { ...SNAPSHOT.jdn, formacion: identificador } },
      })
    }
    if (ruta.includes('/jardin/estado')) return exito(estado)
    throw new Error(`ruta sin mock: ${ruta}`)
  })
  vi.stubGlobal('fetch', funcion)
  return funcion
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Jardín (cuadrícula, siembra, riego y cosecha)', () => {
  it('pinta la cuadrícula, la planta lista y la mejora asequible', async () => {
    instalarFetch()
    render(<Jardin slot="viaje" onSnapshot={vi.fn()} />)

    expect(
      await screen.findByRole('heading', { name: 'Jardín Medicinal' }),
    ).toBeTruthy()

    // 4 casillas: 2 sembradas y 2 vacías con su botón «Sembrar»
    expect(
      await screen.findByRole('list', { name: /Cuadrícula con 4 casillas/ }),
    ).toBeTruthy()
    expect(screen.getAllByRole('button', { name: 'Sembrar' })).toHaveLength(2)

    // casilla 0 lista (restante 0) y casilla 1 creciendo con su recuento
    expect(screen.getByText('Listo para cosechar')).toBeTruthy()
    expect(screen.getByText(/Quedan 1 min/)).toBeTruthy()

    // riego: coste 90 con 100 piedras → habilitado
    const riego = screen.getByRole('button', { name: /Riego \(90/ })
    expect((riego as HTMLButtonElement).disabled).toBe(false)

    // cabecera: semillas hs+ff, piedras, materiales
    expect(screen.getByText('🌱 3 semillas')).toBeTruthy()
    expect(screen.getByText('💎 100 piedras')).toBeTruthy()
    expect(screen.getByText('🌿 20 hierbas')).toBeTruthy()

    // sin formación equipada, con 1 copia en el inventario
    expect(screen.getByText(/Sin formación equipada/)).toBeTruthy()
    expect(
      screen.getByRole('button', { name: /Elegir formación \(1 poseídas\)/ }),
    ).toBeTruthy()

    // mejora nivel 1: asequible (reino 3 ≥ 2 y materiales suficientes)
    expect(screen.getByRole('heading', { name: /Ampliar cuadrícula/ })).toBeTruthy()
    expect(
      screen.getByText(/Cuesta 15 hierbas, 5 núcleos, 5 polvo de jade/),
    ).toBeTruthy()
    expect(
      (screen.getByRole('button', { name: 'Ampliar' }) as HTMLButtonElement)
        .disabled,
    ).toBe(false)
  })

  it('siembra desde el modal y aplica el snapshot del servidor', async () => {
    const fetchMock = instalarFetch()
    const onSnapshot = vi.fn()
    render(<Jardin slot="viaje" onSnapshot={onSnapshot} />)

    fireEvent.click(
      (await screen.findAllByRole('button', { name: 'Sembrar' }))[0],
    )

    const dialogo = await screen.findByRole('dialog', { name: 'Sembrar' })
    expect(dialogo.textContent).toContain('Sembrar en la casilla 3')

    // la especie de reino 7 sigue bloqueada en reino 3
    const fénix = screen.getByRole('button', { name: /Núcleo de Fénix/ })
    expect((fénix as HTMLButtonElement).disabled).toBe(true)
    expect(fénix.textContent).toContain('Requiere reino 7')

    fireEvent.click(screen.getByRole('button', { name: /Hierba Espiritual/ }))

    expect(
      await screen.findByText('Sembraste Hierba Espiritual en la casilla 3.'),
    ).toBeTruthy()
    expect(screen.getByText('🌱 2 semillas')).toBeTruthy()
    await waitFor(() => expect(onSnapshot).toHaveBeenCalledTimes(1))
    expect(onSnapshot).toHaveBeenCalledWith(
      expect.objectContaining({ sd: { ff: 2 } }),
    )

    const llamadas = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/jardin/sembrar') && c[1]?.method === 'POST',
    )
    expect(llamadas).toHaveLength(1)
    expect(String(llamadas[0][1]?.body ?? '')).toBe(
      JSON.stringify({ indice: 2, planta: 'hs' }),
    )
  })

  it('riega con el coste mostrado y la planta queda lista', async () => {
    const fetchMock = instalarFetch()
    const onSnapshot = vi.fn()
    render(<Jardin slot="viaje" onSnapshot={onSnapshot} />)

    const riego = await screen.findByRole('button', { name: /Riego \(90/ })
    fireEvent.click(riego)

    expect(await screen.findByText('Planta lista para cosechar.')).toBeTruthy()
    // ahora hay dos casillas listas
    expect(screen.getAllByText('Listo para cosechar')).toHaveLength(2)
    await waitFor(() => expect(onSnapshot).toHaveBeenCalledTimes(1))
    expect(onSnapshot).toHaveBeenCalledWith(
      expect.objectContaining({ stn: 10 }),
    )

    const llamadas = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/jardin/acelerar') && c[1]?.method === 'POST',
    )
    expect(String(llamadas[0][1]?.body ?? '')).toBe(
      JSON.stringify({ indice: 1, piedras: 90 }),
    )
  })

  it('cosecha una planta lista y las hierbas van al Horno', async () => {
    const fetchMock = instalarFetch()
    const onSnapshot = vi.fn()
    render(<Jardin slot="viaje" onSnapshot={onSnapshot} />)

    const cosechar = (await screen.findAllByRole('button', {
      name: 'Cosechar',
    }))[0]
    expect((cosechar as HTMLButtonElement).disabled).toBe(false)
    fireEvent.click(cosechar)

    expect(
      await screen.findByText('Cosechaste 1 de Hierba Espiritual (al Horno).'),
    ).toBeTruthy()
    await waitFor(() => expect(onSnapshot).toHaveBeenCalledTimes(1))
    expect(onSnapshot).toHaveBeenCalledWith(
      expect.objectContaining({ mat: expect.objectContaining({ h: 21 }) }),
    )

    const llamadas = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/jardin/cosechar') && c[1]?.method === 'POST',
    )
    expect(String(llamadas[0][1]?.body ?? '')).toBe(JSON.stringify({ indice: 0 }))
  })

  it('muestra el error del servidor y relee el estado (reloj desfasado)', async () => {
    const fetchMock = instalarFetch({ errorCosechar: true })
    render(<Jardin slot="viaje" onSnapshot={vi.fn()} />)

    const cosechar = (await screen.findAllByRole('button', {
      name: 'Cosechar',
    }))[0]
    fireEvent.click(cosechar)

    const alerta = await screen.findByRole('alert')
    expect(alerta.textContent).toContain('La planta aún está creciendo')
    // la recarga tras el error vuelve a pedir el estado
    await waitFor(() => {
      const estados = fetchMock.mock.calls.filter(
        (c) =>
          String(c[0]).includes('/jardin/estado') && c[1]?.method === 'GET',
      )
      expect(estados.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('amplía la cuadrícula con la mejora de nivel 1', async () => {
    const onSnapshot = vi.fn()
    const fetchMock = instalarFetch()
    render(<Jardin slot="viaje" onSnapshot={onSnapshot} />)

    fireEvent.click(await screen.findByRole('button', { name: 'Ampliar' }))

    expect(
      await screen.findByText('Cuadrícula ampliada: ya tienes 6 casillas.'),
    ).toBeTruthy()
    const llamadas = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/jardin/mejorar') && c[1]?.method === 'POST',
    )
    expect(String(llamadas[0][1]?.body ?? '')).toBe('{}')
    await waitFor(() => expect(onSnapshot).toHaveBeenCalledTimes(1))
    expect(
      screen.getByRole('list', { name: /Cuadrícula con 6 casillas/ }),
    ).toBeTruthy()
    // tras la mejora, el coste siguiente ya no es asequible
    expect(
      (screen.getByRole('button', { name: 'Ampliar' }) as HTMLButtonElement)
        .disabled,
    ).toBe(true)
  })

  it('equipa y quita la formación de crecimiento', async () => {
    instalarFetch()
    render(<Jardin slot="viaje" onSnapshot={vi.fn()} />)

    fireEvent.click(
      await screen.findByRole('button', { name: /Elegir formación/ }),
    )
    const dialogo = await screen.findByRole('dialog', {
      name: 'Formaciones de crecimiento',
    })
    expect(dialogo.textContent).toContain('Círculo de Rocío')

    // sin copias de fc3: opción deshabilitada
    const sinCopias = screen.getByRole('button', { name: /Sello de Raíces/ })
    expect((sinCopias as HTMLButtonElement).disabled).toBe(true)
    expect(sinCopias.textContent).toContain('tienes 0 copia(s)')

    fireEvent.click(screen.getByRole('button', { name: /Círculo de Rocío/ }))
    expect(await screen.findByText('Equipaste Círculo de Rocío.')).toBeTruthy()
    expect(screen.getByText(/Círculo de Rocío equipada/)).toBeTruthy()

    // reabrir: la equipada se marca y aparece «Quitar formación»
    fireEvent.click(
      await screen.findByRole('button', { name: /Elegir formación/ }),
    )
    const equipada = screen.getByRole('button', { name: /Círculo de Rocío/ })
    expect((equipada as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Quitar formación' }))

    expect(
      await screen.findByText('Formación de crecimiento retirada.'),
    ).toBeTruthy()
    expect(screen.getByText(/Sin formación equipada/)).toBeTruthy()
  })
})
