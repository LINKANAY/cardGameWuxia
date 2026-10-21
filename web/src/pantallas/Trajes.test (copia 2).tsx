/** Tests de la pestaña Trajes: armario, desbloqueos y vestir. */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Trajes from './Trajes'
import type { SnapshotPartida, TrajeResumen } from '../api/tipos'

const SNAPSHOT: SnapshotPartida = {
  realm: 0,
  hp: 30,
  wins: [],
  col: {},
  sect: 'esp',
  mat: { h: 0, n: 0, p: 0 },
  stn: 0,
  dk: [],
  ad: -1,
  pil: {},
  of: { esp: 0 },
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

const UMBRALES = [0, 3, 12, 30, 45, 60]

/** Los 6 trajes de la secta esp (`OF.esp` + `TU` del monolito). */
const TRAJES: TrajeResumen[] = UMBRALES.map((umbral, indice) => ({
  secta: 'esp',
  indice,
  nombre: `Traje ${indice}`,
  umbral,
  tipo: 'hp',
  valor: 2,
  efecto: 'Cuerpo de Jade',
  descripcion: '+2 de vida máxima',
}))

/** Un traje de otra secta: no debe aparecer en el armario. */
const TRAJE_AJENO: TrajeResumen = {
  secta: 'lot',
  indice: 0,
  nombre: 'Túnica de Loto',
  umbral: 0,
  tipo: 'hp',
  valor: 2,
  efecto: 'Cuerpo de Jade',
  descripcion: '+2 de vida máxima',
}

function instalarFetch(vestido?: SnapshotPartida): ReturnType<typeof vi.fn> {
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
      if (ruta.includes('/api/data/trajes')) {
        return exito({ trajes: [...TRAJES, TRAJE_AJENO] })
      }
      if (ruta.includes('/traje/vestir')) {
        return exito({
          slot: 'viaje',
          mensaje: 'Vestiste: Traje 0',
          snapshot: vestido ?? SNAPSHOT,
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

describe('Trajes (armario del cultivador)', () => {
  it('pinta los 6 trajes de la secta, bloquea el 1 y marca el 0 como equipado', async () => {
    instalarFetch()
    render(<Trajes slot="viaje" snapshot={SNAPSHOT} onSnapshot={vi.fn()} />)

    expect(
      await screen.findByRole('heading', { name: 'Armario del cultivador' }),
    ).toBeTruthy()

    // solo la secta del jugador: el traje ajeno no aparece
    const botones = await screen.findAllByRole('button', { name: /Traje/ })
    expect(botones.length).toBe(6)
    expect(screen.queryByText('Túnica de Loto')).toBeNull()

    // traje 1 (umbral 3) con 0 victorias → deshabilitado con el contador
    const bloqueado = screen.getByRole('button', { name: /Traje 1/ })
    expect((bloqueado as HTMLButtonElement).disabled).toBe(true)
    expect(bloqueado.textContent).toContain(
      'Se desbloquea con 3 victorias (0/3)',
    )
    expect(bloqueado.textContent).toContain('Cuerpo de Jade')

    // traje 0 (umbral 0) es el que lleva puesto
    const puesto = screen.getByRole('button', { name: /Traje 0/ })
    expect((puesto as HTMLButtonElement).disabled).toBe(false)
    expect(puesto.className).toContain('eqd')
    expect(puesto.textContent).toContain('Equipado')
  })

  it('al vestir llama a POST …/traje/vestir y aplica el snapshot', async () => {
    const vestido: SnapshotPartida = {
      ...SNAPSHOT,
      of: { esp: 2 },
    }
    const fetchMock = instalarFetch(vestido)
    const onSnapshot = vi.fn()
    render(<Trajes slot="viaje" snapshot={SNAPSHOT} onSnapshot={onSnapshot} />)

    // con 0 victorias solo el traje 0 (umbral 0) está desbloqueado
    const desbloqueado = await screen.findByRole('button', {
      name: /Traje 0/,
    })
    fireEvent.click(desbloqueado)

    expect(await screen.findByText('Vestiste: Traje 0')).toBeTruthy()
    await waitFor(() => expect(onSnapshot).toHaveBeenCalledTimes(1))
    expect(onSnapshot).toHaveBeenCalledWith(vestido)

    const llamadas = fetchMock.mock.calls.filter(
      (c) =>
        String(c[0]).includes('/api/game/viaje/traje/vestir') &&
        c[1]?.method === 'POST',
    )
    expect(llamadas.length).toBe(1)
    expect(String(llamadas[0][1]?.body ?? '')).toContain(
      '{"secta":"esp","indice":0}',
    )
  })
})
