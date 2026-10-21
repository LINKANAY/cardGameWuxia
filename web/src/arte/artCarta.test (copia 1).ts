/** Tests de `arteCarta` para las 129 cartas nuevas.

`MOT` (js/05-arte.js:202) + registro de NS/XC/XF/XR/XH/XV
(js/06-contenido.js:12,24,28,30,42,45). Sin @testing-library: solo SVG.
*/

import { describe, expect, it } from 'vitest'
import arteCarta, { MOTIVOS, SC_SECTAS } from './artCarta'

/** Silueta de montaña del fallback `artK`; no aparece en el marco real. */
const FALLBACK = 'M0 56L20 34L36 48L58 26L80 46L100 36V56Z'

function expectArtePropio(id: string): void {
  const svg = arteCarta(id)
  expect(svg).toContain('<svg class="art"')
  expect(svg).toContain('<defs>')
  expect(svg).toContain('id="gf-') // gradiente de rareza del marco
  expect(svg).not.toContain(FALLBACK)
}

describe('cobertura de las 129 cartas nuevas', () => {
  it('registra exactamente 129 ids', () => {
    expect(Object.keys(MOTIVOS)).toHaveLength(129)
  })

  it('asigna secta a 114 de ellas (las 15 restantes van a neu)', () => {
    expect(Object.keys(SC_SECTAS)).toHaveLength(114)
    expect(SC_SECTAS.M01).toBe('mon')
    expect(SC_SECTAS.H04).toBe('pil')
    expect(SC_SECTAS.Z31).toBeUndefined()
    expect(SC_SECTAS.V01).toBeUndefined()
  })

  it('el fallback sigue existiendo para ids desconocidos', () => {
    const svg = arteCarta('id-inexistente')
    expect(svg).toContain('<svg class="art"')
    expect(svg).toContain(FALLBACK)
    expect(svg).not.toContain('<defs>')
  })

  it('ninguno de los 129 ids cae al fallback artK', () => {
    for (const id of Object.keys(MOTIVOS)) expectArtePropio(id)
  })
})

describe('motivos de NS (M01-M13, P01-P13, T01-T13, B01-B13)', () => {
  it('pintan arte propio en las cuatro sectas nuevas', () => {
    for (const id of ['M01', 'P05', 'T13', 'B01']) expectArtePropio(id)
  })

  it('usan el glypho del motivo MOT con la paleta de su secta', () => {
    expect(arteCarta('M01')).toContain('M12 54L32 34L48 54Z') // monk
    expect(arteCarta('P05')).toContain('M70 20h8v10l8 18H62l8-18Z') // sage
    expect(arteCarta('T13')).toContain('M58 4L34 32H50L42 52L68 22H54Z') // bolt
    expect(arteCarta('B01')).toContain('M50 54V30') // sprout
    expect(arteCarta('M01')).toContain('id="gf-mon"')
    expect(arteCarta('P05')).toContain('id="gf-pil"')
    expect(arteCarta('T13')).toContain('id="gf-tru"')
    expect(arteCarta('B01')).toContain('id="gf-bam"')
  })

  it('respeta la firma (f, b) de los motivos que usan el color de secta', () => {
    // M07 → armor → ART.ar(f, b): costura con el fondo de la secta
    expect(arteCarta('M07')).toContain('stroke="#3b3a35"')
    // B04 → tiger → ART.ti(f, b)
    expect(arteCarta('B04')).toContain('stroke="#1f4a3a"')
    // B08 → fox → ART.zl(f, b) con el fondo de bam
    expect(arteCarta('B08')).toContain('M26 8L40 22H60L74 8L78 36L50 52L22 36Z')
    expect(arteCarta('B08')).toContain('stroke="#1f4a3a"')
  })
})

describe('cartas nuevas con motivo reutilizado (MOT[m] ausente → ART[m])', () => {
  it('Z01 pinta exactamente el arte de ld', () => {
    expect(arteCarta('Z01')).toBe(arteCarta('ld'))
  })

  it('Y01 pinta exactamente el arte de ma', () => {
    expect(arteCarta('Y01')).toBe(arteCarta('ma'))
  })

  it('X05 pinta exactamente el arte de tl', () => {
    expect(arteCarta('X05')).toBe(arteCarta('tl'))
  })

  it('Y15 pinta exactamente el arte de cd', () => {
    expect(arteCarta('Y15')).toBe(arteCarta('cd'))
  })
})

describe('cartas nuevas sin secta', () => {
  it('usan la paleta neutra neu y su motivo', () => {
    expect(arteCarta('V01')).toContain('id="gf-neu"') // cloud
    expect(arteCarta('Z31')).toContain('M12 54L32 34L48 54Z') // monk con neu
    expect(arteCarta('X01')).not.toContain(FALLBACK) // pearl → ART.pf
  })
})

describe('regresión del arte ya portado', () => {
  it('las bestias domables BS1-BS8 siguen pintando', () => {
    for (let i = 1; i <= 8; i++) expectArtePropio(`BS${i}`)
  })

  it('las cartas base siguen pintando su glypho', () => {
    expectArtePropio('cf')
    expect(arteCarta('cf')).toContain('M12 50Q46 -6 90 10Q52 12 12 50Z')
  })
})
