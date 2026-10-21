/** Tests del módulo de sonido (jsdom no tiene AudioContext). */

import { describe, expect, it } from 'vitest'
import { ding } from './sonidos'

describe('ding()', () => {
  it('no lanza aunque el navegador no tenga AudioContext', () => {
    expect(() => ding()).not.toThrow()
  })
})
