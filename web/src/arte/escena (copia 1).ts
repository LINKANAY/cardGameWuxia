/** Escena de fondo de la intro de combate (`scene(li)` de js/05-arte.js:189).

Paisaje SVG con cielo en degradado, sol, montañas, islas y bambú; el
color del cielo y el parámetro de nivel vienen de `LV[li].sky` (el
backend los expone en `narrativa.gradientes_nivel`). Los ids de los
gradientes son fijos (solo hay una escena visible por pantalla), como
en el monolito.
*/

/** `[oscuro, claro]` — `sky` de `LV[li]`. */
export type GradienteCielo = readonly [string, string]

/** `mixc` de js/05-arte.js:30 (oscurece o aclara un color hex). */
export function mezclarColor(hex: string, t: number): string {
  const n = parseInt(hex.slice(1), 16)
  const c = [n >> 16, (n >> 8) & 255, n & 255].map((v) =>
    Math.round(t > 0 ? v + (255 - v) * t : v * (1 + t)),
  )
  return (
    '#' +
    c
      .map((v) => v.toString(16).padStart(2, '0'))
      .join('')
  )
}

export function escenaFondo(sky: GradienteCielo, li: number): string {
  const [a, c] = sky
  const d1 = mezclarColor(c, -0.5)
  const d2 = mezclarColor(c, -0.75)
  const cx = 60 + ((li * 83) % 280)
  const isl = [
    [90, 120],
    [310, 90],
  ]
    .map(
      ([x, y]) =>
        `<ellipse cx="${x}" cy="${y}" rx="34" ry="7" fill="#4a7a5a"/>` +
        `<ellipse cx="${x}" cy="${y - 1}" rx="26" ry="4" fill="#78a886"/>` +
        `<path d="M${x - 32} ${y + 2}Q${x} ${y + 46} ${x + 32} ${y + 2}Z" fill="#2a2f2a"/>`,
    )
    .join('')
  const bam = [14, 36, 372, 390]
    .map((x, i) => {
      const sg = x < 200 ? 1 : -1
      return (
        `<rect x="${x}" y="0" width="6" height="300" fill="url(#bb)"/>` +
        [50, 110, 170, 230]
          .map((y) => `<path d="M${x - 1} ${y + i * 7}h8" stroke="#0c1c15" stroke-width="2"/>`)
          .join('') +
        `<path d="M${x + 3} ${70 + i * 30}q${22 * sg} -8 ${34 * sg} 6q${-20 * sg} 2 ${-34 * sg} -6Z" fill="#3f7a55"/>` +
        `<path d="M${x + 3} ${160 + i * 20}q${22 * sg} -8 ${34 * sg} 6q${-20 * sg} 2 ${-34 * sg} -6Z" fill="#2f6a47"/>`
      )
    })
    .join('')
  return (
    `<svg class="bg" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true">` +
    `<defs>` +
    `<linearGradient id="sk" x1="0" y1="0" x2="0" y2="1">` +
    `<stop offset="0" stop-color="${a}"/>` +
    `<stop offset="1" stop-color="${c}"/>` +
    `</linearGradient>` +
    `<radialGradient id="sun">` +
    `<stop offset="0" stop-color="#fff6d8"/>` +
    `<stop offset=".2" stop-color="#fff6d8" stop-opacity=".6"/>` +
    `<stop offset="1" stop-color="#fff6d8" stop-opacity="0"/>` +
    `</radialGradient>` +
    `<linearGradient id="m1" x1="0" y1="0" x2="0" y2="1">` +
    `<stop offset="0" stop-color="${d1}"/>` +
    `<stop offset="1" stop-color="${c}"/>` +
    `</linearGradient>` +
    `<linearGradient id="m2" x1="0" y1="0" x2="0" y2="1">` +
    `<stop offset="0" stop-color="${d2}"/>` +
    `<stop offset="1" stop-color="${d1}"/>` +
    `</linearGradient>` +
    `<radialGradient id="vg" cx=".5" cy=".5" r=".75">` +
    `<stop offset=".55" stop-color="#000" stop-opacity="0"/>` +
    `<stop offset="1" stop-color="#000" stop-opacity=".65"/>` +
    `</radialGradient>` +
    `<linearGradient id="bb" x1="0" x2="1" y1="0" y2="0">` +
    `<stop offset="0" stop-color="#16342a"/>` +
    `<stop offset=".4" stop-color="#4f8a64"/>` +
    `<stop offset="1" stop-color="#16342a"/>` +
    `</linearGradient>` +
    `<filter id="hz"><feGaussianBlur stdDeviation="7"/></filter>` +
    `</defs>` +
    `<rect width="400" height="300" fill="url(#sk)"/>` +
    `<circle cx="${cx}" cy="60" r="80" fill="url(#sun)"/>` +
    `<circle cx="${cx}" cy="60" r="16" fill="#fff6e0"/>` +
    `<path d="M0 200L60 110L110 170L180 80L250 180L320 120L400 190V300H0Z" fill="url(#m1)" opacity=".8"/>` +
    `<ellipse cx="120" cy="190" rx="130" ry="14" fill="#fff" opacity=".28" filter="url(#hz)"/>` +
    `<ellipse cx="300" cy="215" rx="120" ry="12" fill="#fff" opacity=".22" filter="url(#hz)"/>` +
    isl +
    `<path d="M0 250L70 180L130 230L210 160L290 235L360 190L400 240V300H0Z" fill="url(#m2)"/>` +
    `<ellipse cx="200" cy="250" rx="200" ry="16" fill="#fff" opacity=".18" filter="url(#hz)"/>` +
    bam +
    `<rect width="400" height="300" fill="url(#vg)"/>` +
    `</svg>`
  )
}
