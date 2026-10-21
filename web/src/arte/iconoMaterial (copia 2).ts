/** Icono SVG de material/píldora — port verbatim de ico() de js/06-contenido.js:152.

Glyphos de 40×40 para herb/core/dust/pill/tal/scroll; se usa en los
lotes del Mercado (antes emojis) y puede reutilizarse en otros sitios.
*/

const COLOR: Record<string, string> = {
  herb: '#6cc4a1',
  core: '#e8a23a',
  dust: '#cfeaff',
  pill: '#e8908a',
  tal: '#f0d37a',
  scroll: '#d9b55b',
}

const GLIFO: Record<string, (c: string) => string> = {
  herb: (c) =>
    `<path d="M20 36V14" stroke="${c}" stroke-width="3"/><ellipse cx="12" cy="16" rx="8" ry="4" fill="${c}"/><ellipse cx="28" cy="12" rx="8" ry="4" fill="${c}"/>`,
  core: (c) =>
    `<path d="M20 4L34 14V28L20 38L6 28V14Z" fill="${c}"/><path d="M20 4V38M6 14L34 28M34 14L6 28" stroke="#000" opacity=".25"/>`,
  dust: (c) =>
    `<path d="M20 4L24 16L36 20L24 24L20 36L16 24L4 20L16 16Z" fill="${c}"/>`,
  pill: (c) =>
    `<circle cx="20" cy="22" r="13" fill="${c}"/><circle cx="15" cy="17" r="4" fill="#fff" opacity=".6"/>`,
  tal: (c) =>
    `<rect x="11" y="4" width="18" height="32" fill="${c}"/><path d="M16 12h8M20 10v22" stroke="#a3201a" stroke-width="2"/>`,
  scroll: (c) =>
    `<rect x="8" y="8" width="24" height="26" fill="${c}"/><path d="M12 16h16M12 22h16M12 28h10" stroke="#000" opacity=".35"/>`,
}

/** SVG 40×40 del material/píldora k (fallback: genérico gris). */
export function iconoMaterial(k: string): string {
  const c = COLOR[k] || '#ccc'
  const g = GLIFO[k]
  return `<svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">${g ? g(c) : ''}</svg>`
}

export default iconoMaterial
