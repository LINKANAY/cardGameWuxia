/** Tests de la escena de fondo de la intro de combate (`scene`). */

import { describe, expect, it } from 'vitest'
import { escenaFondo, mezclarColor } from './escena'

describe('mezclarColor', () => {
  it('oscurece un hex como `mixc` del monolito', () => {
    // mixc('#9fc7d8', -0.5) → cada canal × 0.5 redondeado
    expect(mezclarColor('#9fc7d8', -0.5)).toBe('#50646c')
  })
})

describe('escenaFondo', () => {
  it('pinta el cielo del gradiente y el sol según el nivel', () => {
    const svg = escenaFondo(['#2b4a63', '#9fc7d8'], 0)
    expect(svg).toContain('viewBox="0 0 400 300"')
    expect(svg).toContain('stop-color="#2b4a63"')
    expect(svg).toContain('stop-color="#9fc7d8"')
    // cx = 60 + (0 * 83) % 280
    expect(svg).toContain('<circle cx="60" cy="60" r="80"')
    expect(svg).toContain('<circle cx="60" cy="60" r="16"')
  })

  it('desplaza el sol con el índice de nivel', () => {
    // cx = 60 + (2 * 83) % 280 = 226
    expect(escenaFondo(['#2b4a63', '#9fc7d8'], 2)).toContain(
      '<circle cx="226" cy="60" r="80"',
    )
  })
})
