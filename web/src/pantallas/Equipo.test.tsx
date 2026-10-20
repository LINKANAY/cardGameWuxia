/** Tests de la pestaña Equipo: huecos, Herrería y bestias de ayuda. */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Equipo from './Equipo'
import type {
  BestiaResumen,
  PiezaEquipoResumen,
  SnapshotPartida,
} from '../api/tipos'

const SNAPSHOT: SnapshotPartida = {
  realm: 0,
  hp: 30,
  wins: [],
  col: {},
  sect: 'esp',
  mat: { h: 2, n: 0, p: 3 },
  stn: 0,
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
}

/** Orden del backend (`SLOTS` de python/app/data/equipo.py). */
const HUECOS = [
  { clave: 'cabeza', nombre: 'Cabeza' },
  { clave: 'cuerpo', nombre: 'Cuerpo' },
  { clave: 'guantes', nombre: 'Guantes' },
  { clave: 'botas', nombre: 'Botas' },
  { clave: 'reliquia', nombre: 'Reliquia' },
  { clave: 'artefacto', nombre: 'Artefacto' },
]

function pieza(
  identificador: string,
  nombre: string,
  slot: string,
  extras: Partial<
    Pick<
      PiezaEquipoResumen,
      'ataque' | 'qi' | 'coste' | 'desbloqueo' | 'revive' | 'usos'
    >
  > = {},
): PiezaEquipoResumen {
  return {
    identificador,
    nombre,
    slot,
    ataque: 0,
    qi: 0,
    coste: {},
    desbloqueo: null,
    revive: null,
    usos: null,
    secta: 'neu',
    ...extras,
  }
}

/** Catálogo reducido, ordenado por hueco como el backend. */
const PIEZAS: PiezaEquipoResumen[] = [
  pieza('G1', 'Diadema de Jade', 'cabeza', { qi: 1, coste: { p: 3, h: 2 } }),
  pieza('G2', 'Casco del Dragón', 'cabeza', {
    ataque: 1,
    qi: 1,
    coste: { p: 6, n: 2 },
    desbloqueo: 17,
  }),
  pieza('G4', 'Túnica Reforzada', 'cuerpo', {
    ataque: 1,
    coste: { p: 3, h: 2 },
  }),
  pieza('G12', 'Guantes de Cuero', 'guantes', {
    ataque: 1,
    coste: { h: 3, p: 2 },
  }),
  pieza('G15', 'Botas de Tela', 'botas', { qi: 1, coste: { h: 3, p: 2 } }),
  pieza('G7', 'Brazalete de Qi', 'reliquia', { qi: 1, coste: { h: 3, p: 2 } }),
  pieza('G10', 'Campana del Alma', 'artefacto', {
    coste: { p: 14, n: 6 },
    desbloqueo: 23,
    revive: 10,
    usos: 3,
  }),
]

const BESTIAS: BestiaResumen[] = [
  { identificador: 'BS1', nombre: 'Lobo de la Aldea', ataque: 2, vida: 3, indice_nivel: 0 },
  { identificador: 'BS2', nombre: 'Zorro Espectral', ataque: 3, vida: 4, indice_nivel: 1 },
]

function instalarFetch(
  forjada?: SnapshotPartida,
): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(
    async (entrada: RequestInfo | URL, opciones?: RequestInit) => {
      const ruta = String(entrada)
      const metodo = opciones?.method ?? 'GET'
      const exito = (datos: unknown) =>
        ({
          ok: true,
          status: 200,
          json: async () => ({ ok: true, data: datos }),
        }) as Response
      if (ruta.includes('/api/data/equipo')) {
        return exito({ equipo: { piezas: PIEZAS, huecos: HUECOS } })
      }
      if (ruta.includes('/api/data/bestias')) {
        return exito({ bestias: BESTIAS })
      }
      if (ruta.includes('/equipo/forjar')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Forjaste: Diadema de Jade',
          snapshot: forjada ?? SNAPSHOT,
        })
      }
      if (ruta.includes('/equipo/equipar')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Equipaste: Diadema de Jade',
          snapshot: SNAPSHOT,
        })
      }
      if (ruta.includes('/equipo/bestia')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Domaste: Lobo de la Aldea',
          snapshot: SNAPSHOT,
        })
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
})

describe('Equipo (huecos, Herrería y bestias)', () => {
  it('pinta los 6 huecos vacíos, el coste de G1 y el plano bloqueado de G2', async () => {
    instalarFetch()
    render(<Equipo slot="viaje" snapshot={SNAPSHOT} onSnapshot={vi.fn()} />)

    expect(
      await screen.findByRole('heading', { name: 'Equipo del cultivador' }),
    ).toBeTruthy()
    expect(await screen.findByRole('heading', { name: 'Herrería' })).toBeTruthy()

    expect(screen.getAllByText('Vacío').length).toBe(6)
    expect(screen.getAllByText('Aún no has forjado ninguno').length).toBe(6)

    // G1 asequible con el inventario (p:3 h:2) → botón activo con su coste
    const g1 = screen.getByRole('button', { name: /Diadema de Jade/ })
    expect((g1 as HTMLButtonElement).disabled).toBe(false)
    expect(g1.textContent).toContain('Forjar: 3 polvo de jade, 2 hierbas')

    // G2 requiere vencer al enemigo 17 (Nivel 3) → deshabilitada
    const g2 = screen.getByRole('button', { name: /Casco del Dragón/ })
    expect((g2 as HTMLButtonElement).disabled).toBe(true)
    expect(g2.textContent).toContain(
      'Plano bloqueado: vence al jefe del Nivel 3',
    )

    // sin victorias la bestia del Nivel 1 sigue domada
    expect(
      await screen.findByRole('button', { name: /Lobo de la Aldea/ }),
    ).toBeTruthy()
    expect(
      screen.getByText(/Vence al jefe del Nivel 1 para domarla/),
    ).toBeTruthy()
  })

  it('la pieza forjada y puesta ocupa su hueco y se marca EQUIPADA', async () => {
    instalarFetch()
    render(
      <Equipo
        slot="viaje"
        snapshot={{ ...SNAPSHOT, gr: { G1: 1 }, eq: { cabeza: 'G1' } }}
        onSnapshot={vi.fn()}
      />,
    )

    await screen.findByRole('heading', { name: 'Herrería' })

    // el hueco «cabeza» pasa a full con arte, nombre y stats
    const llenos = document.querySelectorAll('.eqs-sl.full')
    expect(llenos.length).toBe(1)
    expect(llenos[0].textContent).toContain('Diadema de Jade')
    expect(llenos[0].textContent).toContain('Qi +1')
    expect((llenos[0] as HTMLButtonElement).disabled).toBe(false)
    expect(screen.getAllByText('Vacío').length).toBe(5)

    // su tarjeta de la Herrería se marca equipada y sin badge «Equipar»
    const tarjeta = document.querySelector('.opt.tj.eqd')
    expect(tarjeta).toBeTruthy()
    expect(tarjeta?.textContent).toContain('Diadema de Jade')
    expect(tarjeta?.querySelector('.eqb')).toBeNull()

    // resumen: Qi base 6 + 1 del equipo
    expect(screen.getByText(/Ataque: base 0/)).toBeTruthy()
    expect(screen.getByText(/Qi máximo en combate: base 6/)).toBeTruthy()
  })

  it('al forjar llama a POST …/equipo/forjar y aplica el snapshot', async () => {
    const forjada: SnapshotPartida = {
      ...SNAPSHOT,
      gr: { G1: 1 },
      eq: { cabeza: 'G1' },
      mat: { h: 0, n: 0, p: 0 },
    }
    const fetchMock = instalarFetch(forjada)
    const onSnapshot = vi.fn()
    render(<Equipo slot="viaje" snapshot={SNAPSHOT} onSnapshot={onSnapshot} />)

    const g1 = await screen.findByRole('button', { name: /Diadema de Jade/ })
    fireEvent.click(g1)

    expect(await screen.findByText('Forjaste: Diadema de Jade')).toBeTruthy()
    await waitFor(() => expect(onSnapshot).toHaveBeenCalledTimes(1))
    expect(onSnapshot).toHaveBeenCalledWith(forjada)

    const llamadas = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/api/game/viaje/equipo/forjar') &&
        c[1]?.method === 'POST',
    )
    expect(llamadas.length).toBe(1)
    expect(String(llamadas[0][1]?.body ?? '')).toContain('{"pieza":"G1"}')
  })
})
