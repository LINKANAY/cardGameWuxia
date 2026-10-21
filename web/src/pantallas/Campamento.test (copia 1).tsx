/** Tests del mapa de campaña en el Campamento (desbloqueos y clic). */

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Campamento from './Campamento'
import type {
  EnemigoResumen,
  Narrativa,
  SectaResumen,
  SnapshotPartida,
} from '../api/tipos'

const SNAPSHOT: SnapshotPartida = {
  realm: 0,
  hp: 24,
  wins: [0, 1],
  col: { cf: 3 },
  sect: 'esp',
  mat: { h: 1, n: 0, p: 0 },
  stn: 0,
  dk: [],
  ad: -1,
  pil: {},
  of: {},
  rec: {},
  be: null,
  gr: {},
  eq: {},
  sc: null,
  du: {},
  dt: 0,
  bt: 2,
  qs: { track: '' },
  qd: {},
  gt: { ticket_common: 0, ticket_premium: 0 },
  gp: { standard_pity: 0, premium_pity: 0 },
}

const NARRATIVA: Narrativa = {
  prologo: 'x',
  final: 'y',
  reinos: ['Mortal'],
  textos_intro_nivel: Array.from({ length: 8 }, (_, i) => `Nivel ${i + 1}`),
  textos_fin_nivel: Array.from({ length: 8 }, () => 'fin'),
  gradientes_nivel: Array.from({ length: 8 }, () => ['#2b4a63', '#9fc7d8']),
}

const SECTAS: SectaResumen[] = [
  {
    identificador: 'esp',
    nombre: 'Espada Celestial',
    descripcion: '',
    cartas_iniciales: ['cf'],
  },
]

function enemigo(indice: number, dificultad: number): EnemigoResumen {
  return {
    indice,
    nombre_enemigo: `Enemigo ${indice}`,
    secta: 'esp',
    nombre_nivel: 'Nivel 1',
    vida: 30,
    dificultad,
    origen: 'nivel',
    frase_inicio: '¡Ríndete!',
    historia: '',
    indice_nivel: Math.floor(indice / 6),
    texto_habilidades: 'Sin habilidades.',
  }
}

function instalarFetch(enemigos: EnemigoResumen[]): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(async (entrada: RequestInfo | URL) => {
    const ruta = String(entrada)
    if (ruta.includes('/api/data/enemigos')) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, data: { enemigos } }),
      } as Response
    }
    throw new Error(`ruta sin mock: ${ruta}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Campamento (mapa de campaña)', () => {
  it('desbloquea nivel 0, bloquea el 1 y permite combatir al segundo enemigo', async () => {
    const enemigos = Array.from({ length: 12 }, (_, i) =>
      enemigo(i, i % 6 === 5 ? 5 : i % 6),
    )
    instalarFetch(enemigos)
    const onCombatir = vi.fn()

    render(
      <Campamento
        snapshot={SNAPSHOT}
        narrativa={NARRATIVA}
        sectas={SECTAS}
        onCombatir={onCombatir}
        onReiniciar={vi.fn()}
      />,
    )

    expect(await screen.findByText('Mapa de la campaña')).toBeTruthy()
    // nivel 0 abierto con 2/6; resto de niveles bloqueados (falta jefe anterior)
    expect(await screen.findByText(/2\/6/)).toBeTruthy()
    expect(
      screen.getAllByText(/Bloqueado: vence al jefe anterior/).length,
    ).toBeGreaterThanOrEqual(7)

    // enemigo 0 y 1 ya ganados → botones con ✔; enemigo 2 desbloqueado
    const botones = await screen.findAllByRole('button', { name: /Enemigo/ })
    expect(botones.length).toBe(6)
    expect((botones[0] as HTMLButtonElement).disabled).toBe(false)
    expect((botones[2] as HTMLButtonElement).disabled).toBe(false)
    expect((botones[3] as HTMLButtonElement).disabled).toBe(true)

    fireEvent.click(botones[2])
    expect(onCombatir).toHaveBeenCalledWith(2)
  })

  it('sin victorias previas solo abre el primer enemigo del nivel 0', async () => {
    const enemigos = Array.from({ length: 6 }, (_, i) => enemigo(i, i % 6))
    instalarFetch(enemigos)

    render(
      <Campamento
        snapshot={{ ...SNAPSHOT, wins: [] }}
        narrativa={NARRATIVA}
        sectas={SECTAS}
        onCombatir={vi.fn()}
        onReiniciar={vi.fn()}
      />,
    )

    await waitFor(() =>
      expect(screen.getAllByRole('button', { name: /Enemigo/ }).length).toBe(6),
    )
    const botones = screen.getAllByRole('button', { name: /Enemigo/ })
    expect((botones[0] as HTMLButtonElement).disabled).toBe(false)
    expect((botones[1] as HTMLButtonElement).disabled).toBe(true)
  })
})
