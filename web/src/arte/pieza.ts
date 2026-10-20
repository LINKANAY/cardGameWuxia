/** Arte de las piezas de la Herrería — port de `ART.G1..G17` (js/06-contenido.js:55-63).

Cada glypho dibuja con el color de su secta `f` (y `b` cuando hace
falta); el marco (defs/gradientes/montañas/chispas) es el mismo de las
cartas, reutilizado vía `svgEnmarcado` de `artCarta.ts`.
*/

import { paletaSecta, svgEnmarcado } from './artCarta'

/** Anillo alrededor del glypho (`ring` de js/05-arte.js:47). */
const ring = (f: string, r = 20): string =>
  `<circle cx="50" cy="28" r="${r}" fill="none" stroke="${f}" stroke-width="4"/>`

/** Talismán rectangular (`tz` de js/05-arte.js:46). */
const tz = (f: string, x = 38, rt = 0): string =>
  `<g transform="rotate(${rt} 50 54)"><rect x="${x}" y="6" width="24" height="44" fill="${f}"/><path d="M${x + 6} 14h12M${x + 12} 14v30M${x + 6} 26h12" stroke="#a3201a" stroke-width="2"/></g>`

/** Espejo ovalado (`ART.em` de js/05-arte.js:67). */
const em = (f: string): string =>
  `<ellipse cx="50" cy="24" rx="18" ry="21" fill="none" stroke="${f}" stroke-width="4"/><path d="M40 16L60 36M42 30L54 18" stroke="${f}" stroke-width="2"/><rect x="47" y="44" width="6" height="10" fill="${f}"/>`

/** Armadura con costuras (`ART.ar` de js/05-arte.js:87). */
const ar = (f: string, b: string): string =>
  `<path d="M30 10L40 6H60L70 10L66 26L62 50H38L34 26Z" fill="${f}"/><path d="M50 8V50" stroke="${b}" stroke-width="2"/>`

/** Secta de cada pieza (`Object.assign(SC, {G1…})` de js/06-contenido.js:54). */
const SC_PIEZA: Record<string, string> = {
  G1: 'lot',
  G2: 'dra',
  G3: 'dra',
  G4: 'mon',
  G5: 'dra',
  G6: 'neu',
  G7: 'pil',
  G8: 'tru',
  G9: 'lun',
  G10: 'lun',
  G11: 'lun',
  G12: 'esp',
  G13: 'dra',
  G14: 'dra',
  G15: 'lot',
  G16: 'lun',
  G17: 'neu',
}

/** Glyphos de las 17 piezas (`ART.G1..G17` de js/06-contenido.js:57-63). */
const GLIFOS: Record<string, (f: string, b: string) => string> = {
  G1: (f) =>
    `<path d="M22 30Q50 4 78 30L70 36Q50 18 30 36Z" fill="${f}"/><circle cx="50" cy="22" r="5" fill="#8fd9b6"/>`,
  G2: (f) =>
    `<path d="M26 36Q26 12 50 12Q74 12 74 36V44H26Z" fill="${f}"/><path d="M28 18L18 4L36 14M72 18L82 4L64 14" fill="${f}"/><path d="M40 30H60V44H40Z" fill="#000" opacity=".35"/>`,
  G3: (f) =>
    `<path d="M22 44L30 14L42 30L50 10L58 30L70 14L78 44Z" fill="#ffe066"/><circle cx="50" cy="26" r="4" fill="#e8604f"/>` +
    ring(f, 26),
  G4: (f) =>
    `<path d="M30 8H70L78 54H22Z" fill="${f}"/><path d="M50 8V54" stroke="#000" opacity=".3"/>`,
  G5: (f, b) =>
    ar(f, b) +
    `<path d="M34 24h32M34 34h32M36 44h28" stroke="#000" opacity=".3" stroke-width="2"/>`,
  G6: (f, b) => ar(f, b) + ring(f, 26),
  G7: (f) =>
    `<ellipse cx="50" cy="30" rx="26" ry="12" fill="none" stroke="${f}" stroke-width="7"/><circle cx="50" cy="18" r="5" fill="#8fd9b6"/>`,
  G8: (f) =>
    `<circle cx="50" cy="34" r="16" fill="none" stroke="${f}" stroke-width="6"/><path d="M50 4L44 16H50L47 24L56 12H51Z" fill="#ffe066"/>`,
  G9: (f) => tz(f) + ring(f, 24),
  G10: (f) =>
    `<path d="M34 40Q34 14 50 12Q66 14 66 40L72 46H28Z" fill="${f}"/><circle cx="50" cy="50" r="4" fill="#ffe066"/>`,
  G11: (f) => em(f) + ring(f, 26),
  G12: (f) =>
    `<path d="M32 50V30Q32 26 36 26Q40 26 40 30V16Q40 12 44 12Q48 12 48 16V14Q48 10 52 10Q56 10 56 14V18Q56 14 60 14Q64 14 64 18V32Q70 28 72 32Q74 36 66 46L62 52H36Z" fill="${f}"/><path d="M32 44H64" stroke="#000" opacity=".3" stroke-width="3"/>`,
  G13: (f) =>
    `<path d="M32 50V30Q32 26 36 26Q40 26 40 30V16Q40 12 44 12Q48 12 48 16V14Q48 10 52 10Q56 10 56 14V18Q56 14 60 14Q64 14 64 18V32Q70 28 72 32Q74 36 66 46L62 52H36Z" fill="${f}"/><path d="M32 44H64" stroke="#000" opacity=".3" stroke-width="3"/><path d="M40 22h18M40 30h18M38 38h22" stroke="#000" opacity=".3" stroke-width="2"/>`,
  G14: (f) =>
    `<path d="M32 50V30Q32 26 36 26Q40 26 40 30V16Q40 12 44 12Q48 12 48 16V14Q48 10 52 10Q56 10 56 14V18Q56 14 60 14Q64 14 64 18V32Q70 28 72 32Q74 36 66 46L62 52H36Z" fill="${f}"/><path d="M32 44H64" stroke="#000" opacity=".3" stroke-width="3"/><rect x="30" y="44" width="36" height="8" fill="#ffe066"/>` +
    ring(f, 26),
  G15: (f) =>
    `<path d="M34 6H56V32L74 38Q80 40 80 46V52H34Z" fill="${f}"/><path d="M34 46H80" stroke="#000" opacity=".3" stroke-width="3"/>`,
  G16: (f) =>
    `<path d="M34 6H56V32L74 38Q80 40 80 46V52H34Z" fill="${f}"/><path d="M34 46H80" stroke="#000" opacity=".3" stroke-width="3"/><path d="M34 16L20 6L24 22Z" fill="#cfe3dc"/>`,
  G17: (f) =>
    `<path d="M34 6H56V32L74 38Q80 40 80 46V52H34Z" fill="${f}"/><path d="M34 46H80" stroke="#000" opacity=".3" stroke-width="3"/><path d="M34 16L20 6L24 22Z" fill="#ffe066"/><circle cx="45" cy="20" r="4" fill="#8fd9b6"/>`,
}

/** SVG completo (`viewBox="0 0 100 56"`) de una pieza de la Herrería. */
export function artePieza(id: string): string {
  const k = SC_PIEZA[id] ?? 'neu'
  const [b, f] = paletaSecta(k)
  const g = GLIFOS[id]
  return svgEnmarcado(k, b, f, g ? g(f, b) : '')
}

export default artePieza
