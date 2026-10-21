/** Arte ilustrado de cartas — port verbatim de art() de js/05-arte.js:148-151.

Combina la paleta de secta (PAL/SC), el glypho por carta (ART), el
gradiente de rareza implícito (defs gf-) y decoración (montañas, niebla,
líneas de velocidad, chispas, ruido). Los IDs de gradiente son por
secta; se renderiza con dangerouslySetInnerHTML (Mercado, Mazos).

Nota: el init de SC del monolito recorre el mapa de sectas S (mazo base
por secta); aquí se fija explícitamente (mismas claves) para no depender
del scope global del JS.

Incluye además `MOT` (33 motivos de js/05-arte.js:202) y el registro
de las 129 cartas nuevas NS/XC/XF/XR/XH/XV de js/06-contenido.js.
*/

/* eslint-disable @typescript-eslint/no-explicit-any */

      const PAL: Record<string, string[]> = { esp: ['#2a4a6b', '#9fd0ff'], lot: ['#1f5a4a', '#f4b6c8'], tal: ['#6b3a1f', '#f0d37a'], lun: ['#2d2a5e', '#d8d8ff'], val: ['#4a1418', '#e8604f'], dra: ['#5a4410', '#f2c14e'], neu: ['#27403b', '#cfe3dc'] };
      const SC: Record<string, string> = {
  cf: 'esp', ev: 'esp', ld: 'esp', ma: 'esp', te: 'esp',
  lc: 'lot', ej: 'lot', gr: 'lot', ml: 'lot', ab: 'lot',
  tf: 'tal', tl: 'tal', fe: 'tal', mt: 'tal', gd: 'tal',
  il: 'lun', em: 'lun', zl: 'lun', vs: 'lun', pl: 'lun',
  sa: 'val', dm: 'val', co: 'val', cd: 'val', av: 'val',
  dc: 'dra', ad: 'dra', rd: 'dra', pf: 'dra', fn: 'dra',
}
      function artK(k: string, h: number) {
         const [b, f] = PAL[k], r = h % 3; let m = '';
         if (k == 'esp') m = `<g transform="rotate(${-50 + r * 25} 50 28)"><rect x="48" y="3" width="4" height="40" fill="${f}"/><rect x="40" y="42" width="20" height="3" fill="${f}"/><rect x="48" y="45" width="4" height="8" fill="${f}" opacity=".7"/></g>`;
         else if (k == 'lot') m = [0, 1, 2, 3, 4].map((i: any) => `<ellipse cx="50" cy="30" rx="6" ry="16" fill="${f}" opacity=".75" transform="rotate(${-60 + i * 30} 50 46)"/>`).join('');
         else if (k == 'tal') m = `<g transform="rotate(${(r - 1) * 8} 50 28)"><rect x="38" y="5" width="24" height="44" fill="${f}"/><path d="M44 14h12M50 14v30M44 24h12M44 34h12" stroke="#a3201a" stroke-width="2"/></g>`;
         else if (k == 'lun') m = `<circle cx="50" cy="28" r="18" fill="${f}"/><circle cx="${56 + r * 3}" cy="24" r="16" fill="${b}"/>`;
         else if (k == 'val') m = `<circle cx="50" cy="32" r="14" fill="${f}" opacity=".85"/><path d="M38 24L32 6L44 20M62 24L68 6L56 20" fill="${f}"/><circle cx="45" cy="31" r="2.5" fill="#000"/><circle cx="55" cy="31" r="2.5" fill="#000"/>`;
         else if (k == 'dra') m = `<path d="M10 44C30 ${4 + r * 6} 40 54 58 24S86 8 90 20" fill="none" stroke="${f}" stroke-width="5" stroke-linecap="round"/><circle cx="90" cy="20" r="4" fill="${f}"/>`;
         else m = `<circle cx="${40 + r * 10}" cy="24" r="10" fill="${f}" opacity=".85"/>`;
         return `<svg class="art" viewBox="0 0 100 56" aria-hidden="true"><rect width="100" height="56" fill="${b}"/><circle cx="82" cy="12" r="6" fill="${f}" opacity=".35"/><path d="M0 56L20 34L36 48L58 26L80 46L100 36V56Z" fill="#000" opacity=".35"/>${m}</svg>`
      }
      const mixc = (h: any, t: any) => { const n = parseInt(h.slice(1), 16), c = [n >> 16, n >> 8 & 255, n & 255].map((v: any) => Math.round(t > 0 ? v + (255 - v) * t : v * (1 + t))); return '#' + c.map((v: any) => v.toString(16).padStart(2, '0')).join('') };
      const defs = (k: any, b: any, f: any) => `<defs><linearGradient id="gf-${k}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${mixc(f, .6)}"/><stop offset=".5" stop-color="${f}"/><stop offset="1" stop-color="${mixc(f, -.5)}"/></linearGradient><linearGradient id="sy-${k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${mixc(b, -.35)}"/><stop offset="1" stop-color="${mixc(b, .35)}"/></linearGradient><radialGradient id="gl-${k}"><stop offset="0" stop-color="${f}" stop-opacity=".9"/><stop offset="1" stop-color="${f}" stop-opacity="0"/></radialGradient><linearGradient id="hz-${k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${b}" stop-opacity="0"/><stop offset="1" stop-color="${mixc(f, .3)}" stop-opacity=".5"/></linearGradient><filter id="bv" x="-25%" y="-25%" width="150%" height="150%"><feGaussianBlur in="SourceAlpha" stdDeviation="1.4" result="b"/><feSpecularLighting in="b" surfaceScale="4" specularConstant=".95" specularExponent="20" lighting-color="#fff" result="s"><fePointLight x="15" y="-8" z="45"/></feSpecularLighting><feComposite in="s" in2="SourceAlpha" operator="in" result="s2"/><feComposite in="SourceGraphic" in2="s2" operator="arithmetic" k1="0" k2="1" k3=".75" k4="0" result="l"/><feDropShadow in="l" dx="1.5" dy="3" stdDeviation="2" flood-color="#000" flood-opacity=".6"/></filter><filter id="mist" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3"/></filter><filter id="nz"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 .5 0"/></filter></defs>`;
      const sw = (f: any, x: any, y: any, r: any, L: any = 34) => `<g transform="translate(${x} ${y}) rotate(${r})"><path d="M-2 0V-${L}L0 -${L + 5}L2 -${L}V0ZM-9 0h18v3h-18ZM-1.5 3h3v7h-3Z" fill="${f}"/></g>`;
      const pe = (f: any) => `<circle cx="50" cy="16" r="7" fill="${f}"/><path d="M34 54Q36 26 50 26T66 54Z" fill="${f}"/>`;
      const fl = (f: any, t: any = '') => `<path ${t} d="M50 6C62 22 70 30 62 44C58 50 42 50 38 44C30 32 42 26 50 6Z" fill="${f}"/>`;
      const mn = (f: any, b: any) => `<circle cx="50" cy="28" r="18" fill="${f}"/><circle cx="58" cy="24" r="16" fill="${b}"/>`;
      const lt = (f: any, n: any = 5) => Array.from({ length: n }, (_: any, i: any) => `<ellipse cx="50" cy="30" rx="6" ry="16" fill="${f}" opacity=".75" transform="rotate(${(i - (n - 1) / 2) * 30} 50 46)"/>`).join('');
      const bd = (f: any) => `<path d="M50 38L10 12Q40 10 50 28Q60 10 90 12Z" fill="${f}"/><circle cx="50" cy="34" r="5" fill="${f}"/><path d="M50 38l-3 12h6Z" fill="${f}"/>`;
      const hf = (f: any) => `<circle cx="50" cy="32" r="14" fill="${f}" opacity=".9"/><path d="M38 24L32 6L44 20M62 24L68 6L56 20" fill="${f}"/><circle cx="45" cy="31" r="2.5" fill="#000"/><circle cx="55" cy="31" r="2.5" fill="#000"/>`;
      const dr = (f: any, w: any = 5) => `<path d="M10 44C30 6 40 54 58 24S86 8 90 18" fill="none" stroke="${f}" stroke-width="${w}" stroke-linecap="round"/><circle cx="90" cy="18" r="${w - 1}" fill="${f}"/>`;
      const lg = (f: any) => `<path d="M58 4L34 32H50L42 52L68 22H54Z" fill="${f}"/>`;
      const tz = (f: any, x: any = 38, rt: any = 0) => `<g transform="rotate(${rt} 50 54)"><rect x="${x}" y="6" width="24" height="44" fill="${f}"/><path d="M${x + 6} 14h12M${x + 12} 14v30M${x + 6} 26h12" stroke="#a3201a" stroke-width="2"/></g>`;
      const ring = (f: any, r: any = 20) => `<circle cx="50" cy="28" r="${r}" fill="none" stroke="${f}" stroke-width="4"/>`;
      const speedL = (k: any, _f: any) => { const q = (k.charCodeAt(0) * 7 + k.length) % 6; let t = ''; for (let i = 0; i < 26; i++) { const a = i * Math.PI / 13 + q, r = 24 + (i % 3) * 4; t += `<path d="M${50 + Math.cos(a) * r} ${28 + Math.sin(a) * r * .6}L${50 + Math.cos(a) * 70} ${28 + Math.sin(a) * 42}"/>` } return `<g stroke="#fff" stroke-width=".35" opacity=".26">${t}</g>` };
      const sparkF = (f: any) => [[16, 12, 2.4], [84, 40, 1.8], [26, 44, 1.4]].map(([x, y, z]: any) => `<path d="M${x} ${y - z * 2}Q${x} ${y} ${x + z * 2} ${y}Q${x} ${y} ${x} ${y + z * 2}Q${x} ${y} ${x - z * 2} ${y}Q${x} ${y} ${x} ${y - z * 2}Z" fill="#fff" opacity=".9"/>`).join('') + `<path d="M0 56V50Q50 44 100 50V56Z" fill="#000" opacity=".22"/><rect x=".6" y=".6" width="98.8" height="54.8" fill="none" stroke="${f}" stroke-width="1" opacity=".8"/>`;
      const ART: Record<string, (f: any, b?: any) => any> = {
         cf: (f: any) => `<path d="M12 50Q46 -6 90 10Q52 12 12 50Z" fill="${f}"/>`,
         ev: (f: any) => sw(f, 56, 52, 40, 36) + `<path d="M8 18h26M4 30h22M12 42h20" stroke="${f}" opacity=".5" stroke-width="2"/>`,
         ld: (f: any) => sw(f, 50, 50, 0, 40) + `<path d="M50 24L20 4M50 24L80 4M50 24L10 24M50 24L90 24" stroke="${f}" stroke-width="1.5" opacity=".6"/>`,
         ma: (f: any) => pe(f) + sw(f, 76, 52, 15, 34),
         te: (f: any) => sw(f, 30, 52, -30, 32) + sw(f, 50, 52, 0, 38) + sw(f, 70, 52, 30, 32),
         lc: (f: any) => lt(f) + `<circle cx="50" cy="16" r="4" fill="#fff" opacity=".85"/>`,
         ej: (f: any) => ring(f) + `<circle cx="50" cy="28" r="11" fill="${f}" opacity=".5"/>`,
         gr: bd,
         ml: (f: any) => [[20, 14], [44, 30], [70, 12], [80, 38], [30, 44], [58, 46]].map(([x, y], i: any) => `<ellipse cx="${x}" cy="${y}" rx="7" ry="3" fill="${f}" opacity=".8" transform="rotate(${i * 40} ${x} ${y})"/>`).join(''),
         ab: (f: any) => ring(f, 24) + lt(f, 3),
         tf: (f: any) => tz(f, 20) + fl('#ff7a3a', 'transform="translate(34 6) scale(.9)"'),
         tl: (f: any) => tz(f) + `<path d="M38 14L62 44M62 14L38 44" stroke="#a3201a" stroke-width="4"/>`,
         fe: (f: any) => ring(f, 22) + `<path d="M50 8L72 42H28ZM50 48L28 14H72Z" fill="none" stroke="${f}" stroke-width="2"/>`,
         mt: (f: any) => [-40, -20, 0, 20, 40].map((r: any) => tz(f, 38, r)).join(''),
         gd: (f: any) => `<rect x="40" y="14" width="20" height="34" fill="${f}"/><rect x="34" y="8" width="32" height="8" fill="${f}"/><rect x="30" y="46" width="40" height="6" fill="${f}"/><circle cx="45" cy="28" r="2" fill="#000"/><circle cx="55" cy="28" r="2" fill="#000"/>`,
         il: (f: any, b: any) => mn(f, b) + `<path d="M6 46q11-8 22 0t22 0t22 0t22 0" stroke="${f}" fill="none" stroke-width="2"/>`,
         em: (f: any) => `<ellipse cx="50" cy="24" rx="18" ry="21" fill="none" stroke="${f}" stroke-width="4"/><path d="M40 16L60 36M42 30L54 18" stroke="${f}" stroke-width="2"/><rect x="47" y="44" width="6" height="10" fill="${f}"/>`,
         zl: (f: any, b: any) => `<path d="M26 8L40 22H60L74 8L78 36L50 52L22 36Z" fill="${f}"/><path d="M38 30l6 4M62 30l-6 4" stroke="${b}" stroke-width="3"/>`,
         vs: (f: any) => `<path d="M20 6Q50 -2 80 6V48Q70 40 60 48Q50 40 40 48Q30 40 20 48Z" fill="${f}" opacity=".8"/>`,
         pl: (f: any, b: any) => pe(f) + `<circle cx="80" cy="14" r="9" fill="${f}"/><circle cx="84" cy="11" r="8" fill="${b}"/>`,
         sa: (f: any) => `<path d="M40 6C52 24 60 32 52 44C48 50 32 50 28 44C20 32 30 24 40 6Z" fill="#e8604f"/>` + sw(f, 70, 52, 25, 30),
         dm: hf,
         co: (f: any) => `<path d="M50 28a3 3 0 0 1 6 0a9 9 0 0 1-18 0a15 15 0 0 1 30 0a21 21 0 0 1-42 0" fill="none" stroke="${f}" stroke-width="3"/>`,
         cd: (f: any) => pe(f) + `<path d="M43 12L38 0L47 9M57 12L62 0L53 9" fill="${f}"/>`,
         av: (f: any) => `<g transform="translate(-15 -9) scale(1.3)">${hf(f)}</g>`,
         dc: (f: any) => dr(f, 3),
         ad: (f: any) => dr(f) + fl('#ff7a3a', 'transform="translate(20 4) scale(.7)"'),
         rd: (f: any) => dr(f, 9) + `<path d="M84 12l-4-10M94 12l4-10" stroke="${f}" stroke-width="2"/>`,
         pf: (f: any) => `<circle cx="50" cy="28" r="14" fill="#fff" opacity=".9"/>` + ring(f, 22),
         fn: (f: any) => bd(f) + `<path d="M50 40L44 54M50 40V56M50 40L56 54" stroke="#ff7a3a" stroke-width="3"/>`,
         pq: (f: any) => `<circle cx="50" cy="36" r="14" fill="${f}"/><circle cx="50" cy="18" r="9" fill="${f}"/><rect x="47" y="6" width="6" height="5" fill="${f}"/>`,
         ph: (f: any, b: any) => `<circle cx="50" cy="28" r="18" fill="${f}"/><path d="M50 18v20M40 28h20" stroke="${b}" stroke-width="5"/>`,
         gp: (f: any) => `<circle cx="50" cy="36" r="13" fill="${f}"/>` + [34, 42, 50, 58].map((x: any) => `<rect x="${x}" y="8" width="5" height="24" rx="2.5" fill="${f}"/>`).join(''),
         di: pe,
         ti: (f: any, b: any) => `<circle cx="50" cy="30" r="18" fill="${f}"/><path d="M34 16L30 4L44 12M66 16L70 4L56 12" fill="${f}"/><path d="M40 20l4 8M60 20l-4 8M50 14v8" stroke="${b}" stroke-width="2.5"/><circle cx="44" cy="32" r="2" fill="${b}"/><circle cx="56" cy="32" r="2" fill="${b}"/>`,
         es: (f: any) => sw(f, 16, 28, 90, 60) + `<path d="M60 14h30M64 42h26" stroke="${f}" opacity=".5" stroke-width="2"/>`,
         ar: (f: any, b: any) => `<path d="M30 10L40 6H60L70 10L66 26L62 50H38L34 26Z" fill="${f}"/><path d="M50 8V50" stroke="${b}" stroke-width="2"/>`,
         tc: (f: any) => `<ellipse cx="36" cy="12" rx="20" ry="9" fill="${f}" opacity=".7"/><ellipse cx="64" cy="12" rx="22" ry="10" fill="${f}" opacity=".7"/>` + lg('#ffe066'),
         mo: (f: any) => pe(f) + `<path d="M76 4V52" stroke="${f}" stroke-width="3"/><circle cx="76" cy="8" r="4" fill="none" stroke="${f}" stroke-width="2"/>`
      };
      Object.assign(SC, { se: 'esp', ex: 'esp', ta: 'tal', fr: 'dra', dt: 'dra', lm: 'lot', gh: 'lun', pi: 'neu', ca: 'neu', ac: 'neu', pr: 'val', mp: 'neu' });
      Object.assign(ART, {
         ta: (f: any) => tz(f) + lg('#ffe066'), mp: (f: any) => pe(f) + ring(f, 24),
         ca: (f: any) => `<rect x="22" y="14" width="56" height="6" fill="${f}"/><path d="M26 20h48v14Q74 50 50 50T26 34Z" fill="${f}"/><path d="M36 8q4-6 0-6M50 8q4-6 0-6M64 8q4-6 0-6" stroke="${f}" fill="none" stroke-width="2"/>`,
         ex: (f: any) => sw(f, 50, 52, 0, 44) + ring(f, 24), fr: (f: any) => bd(f) + fl('#ff7a3a', 'transform="translate(25 14) scale(.5)"'),
         lm: (f: any) => lt(f, 7) + ring(f, 24), pi: (f: any) => ART.pq(f) + `<circle cx="76" cy="12" r="3" fill="#fff"/><circle cx="24" cy="16" r="2" fill="#fff"/>`,
         se: (f: any) => sw(f, 28, 52, -25, 34) + sw(f, 50, 52, 0, 46) + sw(f, 72, 52, 25, 34) + `<circle cx="50" cy="10" r="4" fill="${f}"/>`,
         dt: (f: any) => dr(f, 10) + `<ellipse cx="30" cy="48" rx="20" ry="5" fill="${f}" opacity=".5"/><ellipse cx="70" cy="50" rx="22" ry="5" fill="${f}" opacity=".5"/>`,
         gh: (f: any, b: any) => pe(f) + mn(f, b).replace(/cx="50"/g, 'cx="80"').replace(/cx="58"/g, 'cx="86"').replace(/cy="28"/g, 'cy="14"').replace(/cy="24"/g, 'cy="10"').replace(/r="18"/, 'r="9"').replace(/r="16"/, 'r="8"') + `<path d="M30 54Q24 40 30 30M70 54Q76 40 70 30" stroke="${f}" fill="none" opacity=".5" stroke-width="3"/>`,
         ac: (f: any) => lg('#ffe066') + ring(f, 24) + `<path d="M50 2V0M10 28H4M96 28h-6" stroke="${f}" stroke-width="2"/>`,
         pr: (f: any, b: any) => `<g transform="translate(-10 -6) scale(1.2)">${ART.ti(f, b)}</g>`
      });
      Object.assign(SC, { qe: 'esp', dh: 'esp', ee: 'esp', cp: 'esp', bl: 'lot', mj: 'lot', ep: 'lot', dl: 'lot', th: 'tal', bt: 'tal', ft: 'tal', gc: 'tal', ra: 'lun', sl: 'lun', ec: 'lun', dg: 'lun', sd: 'val', pd: 'val', ba: 'val', sn: 'val', eg: 'dra', sf: 'dra', dy: 'dra', sb: 'dra' });
      Object.assign(ART, {
         qe: (f: any) => sw(f, 50, 50, -15, 30) + `<circle cx="30" cy="20" r="5" fill="${f}" opacity=".6"/><circle cx="72" cy="30" r="3" fill="${f}" opacity=".6"/>`,
         dh: (f: any) => [0, 1, 2, 3, 4, 5].map((i: any) => { const x = 50 + Math.cos(i) * 24, y = 28 + Math.sin(i) * 14; return `<ellipse cx="${x}" cy="${y}" rx="6" ry="2.5" fill="${f}" transform="rotate(${i * 60} ${x} ${y})"/>` }).join('') + sw(f, 50, 50, 0, 28),
         ee: (f: any) => pe(f) + sw(f, 22, 52, -20, 30),
         cp: (f: any) => sw(f, 50, 52, 0, 48) + `<path d="M0 10Q50 -4 100 10" stroke="${f}" stroke-width="2" fill="none"/><path d="M50 0L40 24L58 38" stroke="#fff" stroke-width="2" fill="none"/>`,
         bl: (f: any) => ART.ml(f), mj: (f: any) => pe(f) + lt(f, 3),
         ep: (f: any) => `<ellipse cx="50" cy="38" rx="38" ry="10" fill="none" stroke="${f}" stroke-width="2"/><ellipse cx="50" cy="38" rx="24" ry="6" fill="none" stroke="${f}" stroke-width="2"/>` + lt(f, 3),
         dl: (f: any) => pe(f) + lt(f, 7),
         th: (f: any) => tz(f) + `<path d="M50 6V50M32 14L68 42M68 14L32 42" stroke="#cfeaff" stroke-width="2"/>`,
         bt: (f: any) => tz(f, 10) + tz(f, 38) + tz(f, 66), ft: (f: any) => ring(f, 22) + lg('#ffe066'), gc: (f: any) => ART.fe(f) + ring(f, 26),
         ra: (f: any) => `<ellipse cx="50" cy="40" rx="36" ry="9" fill="${f}" opacity=".4"/><circle cx="50" cy="20" r="12" fill="${f}"/>`,
         sl: (f: any, b: any) => ART.pl(f, b) + `<ellipse cx="50" cy="52" rx="26" ry="4" fill="#000" opacity=".4"/>`,
         ec: (f: any) => `<circle cx="50" cy="28" r="20" fill="${f}"/><circle cx="50" cy="28" r="17" fill="#000"/><circle cx="50" cy="28" r="24" fill="none" stroke="${f}" opacity=".5"/>`,
         dg: (f: any, b: any) => mn(f, b) + `<path d="M36 54Q38 30 50 30T64 54Z" fill="${f}"/><circle cx="50" cy="22" r="6" fill="${f}"/>`,
         sd: (_f: any) => `<path d="M50 6C62 24 70 32 62 44C58 50 42 50 38 44C30 32 38 24 50 6Z" fill="#e8604f"/><path d="M40 40L44 52L48 40M52 40L56 52L60 40" fill="#fff"/>`,
         pd: (f: any) => `<circle cx="50" cy="26" r="14" fill="${f}"/><rect x="42" y="36" width="16" height="8" fill="${f}"/><circle cx="44" cy="25" r="3" fill="#000"/><circle cx="56" cy="25" r="3" fill="#000"/>`,
         ba: (f: any) => `<g transform="translate(-10 -6) scale(1.2)">${hf(f)}</g><path d="M6 50Q26 34 38 52M94 50Q74 34 62 52" stroke="${f}" stroke-width="3" fill="none"/>`,
         sn: (f: any) => ART.av(f) + `<path d="M36 6l6 8 8-10 8 10 6-8v10H36Z" fill="#ffe066"/>`,
         eg: (f: any) => [0, 1, 2].map((r: any) => [0, 1, 2, 3].map((c: any) => `<path d="M${22 + c * 14 + (r % 2) * 7} ${14 + r * 12}a7 7 0 0 0 14 0Z" fill="${f}"/>`).join('')).join(''),
         sf: (f: any) => dr(f, 4) + fl('#ff4a2a', 'transform="translate(10 12) scale(.5)"'), dy: (f: any) => dr(f, 6) + lg('#ffe066'), sb: (f: any) => dr(f, 11) + ring(f, 26),
         aa: (f: any) => pe(f) + `<path d="M70 20h8v10l8 18H62l8-18Z" fill="#6cc4a1"/>`,
         pg: (f: any) => `<circle cx="50" cy="38" r="12" fill="${f}"/>` + fl('#ff7a3a', 'transform="translate(15 -6) scale(.7)"'),
         lb: (f: any) => `<path d="M24 10L40 24H60L76 10L80 36L50 54L20 36Z" fill="${f}"/><path d="M38 34l6 3M62 34l-6 3" stroke="#000" stroke-width="2"/>`,
         as: (f: any) => pe(f) + `<path d="M44 26Q50 50 56 26Z" fill="#fff"/>`,
         md: (f: any) => `<circle cx="50" cy="20" r="7" fill="${f}"/><path d="M26 52Q30 32 50 30Q70 32 74 52Z" fill="${f}"/>` + ring(f, 24),
         aj: (f: any, b: any) => ART.ar(f, b) + ring(f, 26), gi: (f: any) => pe(f) + ring(f, 24) + sw(f, 78, 52, 20, 30),
         pn: (f: any) => [0, 1, 2].map((r: any) => [0, 1, 2].map((c: any) => `<circle cx="${34 + c * 16}" cy="${12 + r * 14}" r="5" fill="${f}"/>`).join('')).join(''),
         td: (f: any) => ART.tc(f) + ring(f, 24), ia: (f: any) => pe(f) + ring(f, 26) + `<path d="M10 14l8 4M90 14l-8 4" stroke="${f}" stroke-width="2"/>`
      });
      Object.assign(SC, { ce: 'esp', ae: 'esp', ru: 'esp', bn: 'lot', rl: 'lot', gl: 'lot', tn: 'tal', sg: 'tal', mg: 'tal', ei: 'lun', ls: 'lun', vn: 'lun', ap: 'val', cn: 'val', rk: 'val', gz: 'dra', ed: 'dra', cb: 'dra' });
      const star = `<path d="M50 4l3 7h7l-6 5 2 7-6-4-6 4 2-7-6-5h7Z" fill="#fff"/>`, frost = `<path d="M16 52L24 30L32 52ZM68 52L78 24L88 52Z" fill="#cfeaff" opacity=".85"/>`;
      Object.assign(ART, {
         ce: (f: any) => sw(f, 50, 50, 0, 34) + `<circle cx="50" cy="20" r="10" fill="none" stroke="#ff6a6a" stroke-width="2"/><path d="M50 6v28M36 20h28" stroke="#ff6a6a"/>`,
         ae: (f: any) => sw(f, 50, 52, 0, 34) + ring(f, 24) + `<circle cx="50" cy="28" r="30" fill="none" stroke="${f}" opacity=".4"/>`,
         ru: (f: any) => sw(f, 50, 52, 0, 48) + `<path d="M44 10L52 20L46 28L54 38" stroke="#fff" stroke-width="2" fill="none"/>`,
         bn: (f: any) => lt(f) + star, rl: (f: any) => `<path d="M50 52Q28 40 40 22Q50 36 48 10M50 52Q72 40 60 22" stroke="${f}" stroke-width="3" fill="none"/>` + frost,
         gl: (f: any) => pe(f) + ring(f, 24), tn: (f: any) => ART.th(f),
         sg: (f: any) => tz(f) + `<circle cx="50" cy="24" r="8" fill="#eee"/><circle cx="47" cy="23" r="2" fill="#000"/><circle cx="53" cy="23" r="2" fill="#000"/>`,
         mg: (f: any) => `<rect x="10" y="22" width="80" height="30" fill="${f}"/><path d="M10 22v-8h12v8M34 22v-8h12v8M58 22v-8h12v8M80 22v-8h10v8" fill="${f}"/>`,
         ei: (f: any) => ART.em(f) + frost, ls: (f: any, b: any) => mn(f, b) + `<path d="M50 30C56 40 60 44 56 50C54 54 46 54 44 50C40 44 44 40 50 30Z" fill="#cfeaff"/>`,
         vn: (f: any) => `<path d="M20 54Q22 28 50 22Q78 28 80 54Z" fill="${f}" opacity=".7"/>` + pe(f),
         ap: (_f: any) => `<path d="M34 50V26Q34 8 50 8Q66 8 66 26V50L58 44L50 50L42 44Z" fill="#cfd8ff"/><circle cx="45" cy="24" r="2.5" fill="#000"/><circle cx="55" cy="24" r="2.5" fill="#000"/><path d="M70 10l10 20" stroke="#e8604f" stroke-width="3"/>`,
         cn: (f: any) => `<path d="M24 20Q50 52 76 20" fill="none" stroke="${f}" stroke-width="4"/><path d="M36 32L40 46L44 34M56 34L60 46L64 32" fill="#fff"/>`,
         rk: (f: any) => hf(f) + `<path d="M36 6l6 8 8-10 8 10 6-8v10H36Z" fill="#e8604f"/>`,
         gz: (f: any) => `<path d="M24 6Q40 28 36 52M44 4Q60 28 56 52M64 6Q80 28 76 52" stroke="${f}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
         ed: (f: any) => ART.eg(f) + ring(f, 26), cb: (f: any) => dr(f, 3) + `<path d="M6 16h22M2 28h18" stroke="${f}" opacity=".5" stroke-width="2"/>`,
         tp: (f: any) => `<path d="M10 52L20 24L30 52L40 24L50 52L60 24L70 52L80 24L90 52Z" fill="${f}"/>`, bc: (f: any) => ring(f, 24) + star,
         gu: (f: any) => `<rect x="34" y="14" width="32" height="26" fill="${f}"/><rect x="22" y="18" width="12" height="24" fill="${f}"/><rect x="66" y="18" width="12" height="24" fill="${f}"/><rect x="38" y="40" width="10" height="12" fill="${f}"/><rect x="52" y="40" width="10" height="12" fill="${f}"/><circle cx="44" cy="24" r="2" fill="#000"/><circle cx="56" cy="24" r="2" fill="#000"/>`
      });
       const art = (id: any) => {
          const k = SC[id] || 'neu', [b, f] = PAL[k], g = ART[id]; if (!g) return artK(k, 0); return svgEnmarcado(k, b, f, g(f, b));
       };
Object.assign(PAL, { mon: ['#3b3a35', '#c9b27c'], pil: ['#2f4a2f', '#9be37a'], tru: ['#222a52', '#ffe066'], bam: ['#1f4a3a', '#8fe0a8'] });

// Bestias domables: reutilizan arte de cartas (`Object.assign(ART, {BS…})`
// de js/06-contenido.js:56) — sin esto `arteCarta('BS1')` caería al fallback.
Object.assign(SC, { BS1: 'bam', BS2: 'lot', BS3: 'val', BS4: 'lun', BS5: 'tru', BS6: 'lot', BS7: 'esp', BS8: 'dra' });
Object.assign(ART, {
  BS1: (f: any, b: any) => ART.lb(f, b), BS2: (f: any) => ART.gr(f), BS3: (f: any) => ART.gr(f), BS4: (f: any, b: any) => ART.zl(f, b), BS5: (f: any) => ART.dy(f), BS6: (f: any) => ART.gr(f) + ring(f, 22), BS7: (f: any, b: any) => ART.ti(f, b) + sw(f, 78, 52, 20, 26), BS8: (f: any) => ART.fn(f),
});

/* ---------- MOT · motivos de las 129 cartas nuevas ---------- */
/* Port verbatim de `MOT` (js/05-arte.js:202-224): 33 motivos `(f)` o
   `(f, b)` que se componen con los helpers/`ART` de arriba. */
export const MOT: Record<string, (f: any, b?: any) => any> = {
         monk: (f: any) => pe(f) + `<path d="M12 54L32 34L48 54Z" fill="${f}" opacity=".5"/>`,
         shield: (f: any) => `<path d="M30 8H70V30Q70 46 50 54Q30 46 30 30Z" fill="${f}"/><path d="M50 8V54" stroke="#000" opacity=".3"/>`,
         golem: (f: any) => ART.gu(f), titan: (f: any) => `<g transform="translate(-10 -8) scale(1.2)">${ART.gu(f)}</g>`, armor: (f: any, b: any) => ART.ar(f, b), wall: (f: any) => ART.mg(f),
         quake: (f: any) => `<path d="M0 36L24 30L38 40L56 28L74 38L100 30" stroke="${f}" stroke-width="3" fill="none"/><path d="M30 20L40 36L34 54M62 14L56 34L66 54" stroke="${f}" stroke-width="2" fill="none"/>`,
         boulder: (f: any) => `<circle cx="40" cy="34" r="16" fill="${f}"/><circle cx="66" cy="42" r="10" fill="${f}" opacity=".8"/>`,
         peak: (f: any) => `<path d="M10 54L40 14L56 36L68 24L92 54Z" fill="${f}"/><path d="M40 14L34 26L42 24L46 30Z" fill="#fff" opacity=".8"/>`,
         crack: (f: any) => `<rect x="10" y="30" width="80" height="24" fill="${f}" opacity=".6"/><path d="M50 4L44 20L54 28L46 42L52 54" stroke="${f}" stroke-width="3" fill="none"/>`,
         pills: (f: any) => ART.pn(f), furnace: (f: any) => `<rect x="26" y="14" width="48" height="36" fill="${f}"/><circle cx="50" cy="34" r="10" fill="#ff7a3a"/>`,
         flask: (f: any) => `<path d="M44 6h12v14l14 28H30l14-28Z" fill="${f}"/>`, bomb: (f: any) => `<path d="M44 14h12v12l14 24H30l14-24Z" fill="${f}"/>` + fl('#ff7a3a', 'transform="translate(18 -10) scale(.55)"'),
         sage: (f: any) => pe(f) + `<path d="M70 20h8v10l8 18H62l8-18Z" fill="#6cc4a1"/>`,
         herb: (f: any) => `<path d="M50 54V14" stroke="${f}" stroke-width="3"/>` + [[40, 24], [60, 20], [38, 38], [62, 34]].map(([x, y]) => `<ellipse cx="${x}" cy="${y}" rx="9" ry="4" fill="${f}"/>`).join(''),
         cauldron: (f: any) => ART.ca(f), pearl: (f: any) => ART.pf(f), gourd: (f: any) => ART.pq(f),
         bolt: (f: any) => lg('#ffe066') + ring(f, 24), cloud: (f: any) => `<ellipse cx="36" cy="26" rx="22" ry="11" fill="${f}" opacity=".8"/><ellipse cx="64" cy="26" rx="24" ry="12" fill="${f}" opacity=".8"/><path d="M52 36L44 50M62 36L54 52" stroke="#ffe066" stroke-width="3"/>`,
         hammer: (f: any) => `<rect x="46" y="14" width="8" height="38" fill="${f}"/><rect x="30" y="6" width="40" height="16" fill="${f}"/>` + lg('#ffe066'),
         drum: (f: any) => `<ellipse cx="50" cy="22" rx="24" ry="8" fill="${f}"/><rect x="26" y="22" width="48" height="24" fill="${f}" opacity=".85"/><ellipse cx="50" cy="46" rx="24" ry="8" fill="${f}"/>`,
         bird: (f: any) => bd(f) + `<path d="M50 6L46 16H50L47 24L56 12H51Z" fill="#ffe066"/>`, god: (f: any) => pe(f) + ring(f, 24) + lg('#ffe066'),
         sprout: (f: any) => `<path d="M50 54V30" stroke="${f}" stroke-width="3"/><ellipse cx="38" cy="26" rx="12" ry="5" fill="${f}"/><ellipse cx="62" cy="22" rx="12" ry="5" fill="${f}"/>`,
         leaf: (f: any) => `<ellipse cx="40" cy="30" rx="24" ry="8" fill="${f}" transform="rotate(-35 40 30)"/><path d="M18 50L62 10" stroke="#000" opacity=".3"/>`,
         panda: (f: any) => `<circle cx="50" cy="30" r="18" fill="#eee"/><circle cx="38" cy="14" r="6" fill="#222"/><circle cx="62" cy="14" r="6" fill="#222"/><circle cx="43" cy="30" r="4" fill="#222"/><circle cx="57" cy="30" r="4" fill="#222"/><rect x="10" y="10" width="5" height="44" fill="${f}"/><rect x="85" y="10" width="5" height="44" fill="${f}"/>`,
         tiger: (f: any, b: any) => ART.ti(f, b), fox: (f: any, b: any) => ART.zl(f, b), rain: (f: any) => ART.ml(f), dragon: (f: any) => dr(f, 6),
         grove: (f: any) => [0, 1, 2, 3].map(i => `<rect x="${22 + i * 17}" y="4" width="7" height="50" fill="${f}"/><path d="M${22 + i * 17} ${18 + i * 8}h7M${22 + i * 17} ${34 + i * 4}h7" stroke="#000" stroke-width="2"/>`).join('') + `<path d="M60 20q16-6 24 4q-14 6-24-4Z" fill="${f}" opacity=".7"/>`
      };

/** Motivo de cada una de las 129 cartas nuevas: elemento `m` de las tuplas
  * de js/06-contenido.js (NS: 6º, XC/XF/XR/XH/XV: 7º). Si `m` no está en
  * `MOT`, el arte se reutiliza de la carta `ART[m]` (regla `MOT[m] || ART[m]`
  * del monolito). */
export const MOTIVOS: Record<string, string> = {
  // NS · Montaña (mon)
  M01: 'monk', M02: 'shield', M03: 'golem', M04: 'quake', M05: 'titan', M06: 'boulder', M07: 'armor', M08: 'monk', M09: 'wall', M10: 'titan', M11: 'peak', M12: 'crack', M13: 'peak',
  // NS · Alquimia (pil)
  P01: 'sage', P02: 'pills', P03: 'furnace', P04: 'bomb', P05: 'sage', P06: 'herb', P07: 'flask', P08: 'cauldron', P09: 'pills', P10: 'pearl', P11: 'golem', P12: 'gourd', P13: 'sage',
  // NS · Trueno (tru)
  T01: 'monk', T02: 'bolt', T03: 'cloud', T04: 'hammer', T05: 'bird', T06: 'bolt', T07: 'bolt', T08: 'drum', T09: 'cloud', T10: 'god', T11: 'bolt', T12: 'cloud', T13: 'bolt',
  // NS · Bambú (bam)
  B01: 'sprout', B02: 'leaf', B03: 'panda', B04: 'tiger', B05: 'grove', B06: 'sprout', B07: 'grove', B08: 'fox', B09: 'tiger', B10: 'fox', B11: 'rain', B12: 'dragon', B13: 'grove',
  // XC · cartas del nuevo reino
  Z01: 'ld', Z02: 'te', Z03: 'se', Z04: 'lc', Z05: 'lm', Z06: 'dl', Z07: 'tn', Z08: 'gc', Z09: 'mt', Z10: 'ei', Z11: 'dg', Z12: 'ec', Z13: 'sa',
  Z14: 'sn', Z15: 'av', Z16: 'dc', Z17: 'rd', Z18: 'dt', Z19: 'wall', Z20: 'titan', Z21: 'peak', Z22: 'furnace', Z23: 'sage', Z24: 'pills', Z25: 'bolt', Z26: 'god',
  Z27: 'cloud', Z28: 'sprout', Z29: 'grove', Z30: 'grove', Z31: 'monk', Z32: 'tl',
  // XF · formaciones y runas
  Y01: 'ma', Y02: 'ej', Y03: 'fe', Y04: 'zl', Y05: 'dm', Y06: 'ad', Y07: 'wall', Y08: 'cauldron', Y09: 'bolt', Y10: 'grove', Y11: 'ld', Y12: 'ab', Y13: 'tl',
  Y14: 'pl', Y15: 'cd', Y16: 'pf', Y17: 'boulder', Y18: 'flask', Y19: 'cloud', Y20: 'leaf', Y21: 'ex', Y22: 'pearl',
  // XR · renovación
  X01: 'pearl', X02: 'cloud', X03: 'ld', X04: 'lc', X05: 'tl', X06: 'pl', X07: 'cd', X08: 'dc', X09: 'boulder', X10: 'flask', X11: 'bolt', X12: 'sprout',
  // XH · horno
  H01: 'gourd', H02: 'pills', H03: 'pearl', H04: 'flask',
  // XV · vacío
  V01: 'cloud', V02: 'crack', V03: 'pearl', V04: 'sage', V05: 'god', V06: 'rain', V07: 'cauldron'
}

/** Secta (paleta) de las cartas nuevas: `SC[id] = k` de js/06-contenido.js
  * (líneas 12, 24, 28, 30, 42, 45). Las 15 sin secta (Z31, Z32, Y21, Y22,
  * X01, X02, H01, H02, V01…V07) no aparecen aquí → `SC[id] || 'neu'`. */
export const SC_SECTAS: Record<string, string> = {
  // NS · Montaña (mon)
  M01: 'mon', M02: 'mon', M03: 'mon', M04: 'mon', M05: 'mon', M06: 'mon', M07: 'mon', M08: 'mon', M09: 'mon', M10: 'mon', M11: 'mon', M12: 'mon', M13: 'mon',
  // NS · Alquimia (pil)
  P01: 'pil', P02: 'pil', P03: 'pil', P04: 'pil', P05: 'pil', P06: 'pil', P07: 'pil', P08: 'pil', P09: 'pil', P10: 'pil', P11: 'pil', P12: 'pil', P13: 'pil',
  // NS · Trueno (tru)
  T01: 'tru', T02: 'tru', T03: 'tru', T04: 'tru', T05: 'tru', T06: 'tru', T07: 'tru', T08: 'tru', T09: 'tru', T10: 'tru', T11: 'tru', T12: 'tru', T13: 'tru',
  // NS · Bambú (bam)
  B01: 'bam', B02: 'bam', B03: 'bam', B04: 'bam', B05: 'bam', B06: 'bam', B07: 'bam', B08: 'bam', B09: 'bam', B10: 'bam', B11: 'bam', B12: 'bam', B13: 'bam',
  // XC · cartas del nuevo reino
  Z01: 'esp', Z02: 'esp', Z03: 'esp', Z04: 'lot', Z05: 'lot', Z06: 'lot', Z07: 'tal', Z08: 'tal', Z09: 'tal', Z10: 'lun', Z11: 'lun', Z12: 'lun', Z13: 'val',
  Z14: 'val', Z15: 'val', Z16: 'dra', Z17: 'dra', Z18: 'dra', Z19: 'mon', Z20: 'mon', Z21: 'mon', Z22: 'pil', Z23: 'pil', Z24: 'pil', Z25: 'tru', Z26: 'tru',
  Z27: 'tru', Z28: 'bam', Z29: 'bam', Z30: 'bam',
  // XF · formaciones y runas
  Y01: 'esp', Y02: 'lot', Y03: 'tal', Y04: 'lun', Y05: 'val', Y06: 'dra', Y07: 'mon', Y08: 'pil', Y09: 'tru', Y10: 'bam', Y11: 'esp', Y12: 'lot', Y13: 'tal',
  Y14: 'lun', Y15: 'val', Y16: 'dra', Y17: 'mon', Y18: 'pil', Y19: 'tru', Y20: 'bam',
  // XR · renovación
  X03: 'esp', X04: 'lot', X05: 'tal', X06: 'lun', X07: 'val', X08: 'dra', X09: 'mon', X10: 'pil', X11: 'tru', X12: 'bam',
  // XH · horno
  H03: 'pil', H04: 'pil'
}

/* js/06-contenido.js:12,24,28,30,42,45 — misma registración que el monolito:
   secta de la carta (`SC[id] = k`) y glypho (`ART[id] = MOT[m] || ART[m]`),
   de modo que `art()`/`arteCarta()` no caigan al fallback `artK`. */
Object.assign(SC, SC_SECTAS)
for (const id in MOTIVOS) ART[id] = MOT[MOTIVOS[id]] || ART[MOTIVOS[id]]

/** Paleta `[fondo, figura]` de una secta (`PAL` del monolito). */
export function paletaSecta(k: string): [string, string] {
  const p = PAL[k] ?? PAL.neu
  return [p[0], p[1]]
}

/** SVG con el marco completo de arte (defs, fondo, decoración, chispas).

`m` es el glypho: al igual que `art()`, sus rellenos del color de secta
se sustituyen por el gradiente `gf-`.
*/
export function svgEnmarcado(k: string, b: string, f: string, m: string): string {
  const interior = m
    .split('fill="' + f + '"')
    .join('fill="url(#gf-' + k + ')"')
  return `<svg class="art" viewBox="0 0 100 56" aria-hidden="true">${defs(k, b, f)}<rect width="100" height="56" fill="url(#sy-${k})"/><circle cx="76" cy="16" r="22" fill="url(#gl-${k})" opacity=".55"/><path d="M0 40L16 26L30 36L52 18L72 34L88 24L100 32V56H0Z" fill="${mixc(b, -.5)}" opacity=".55" class="bgm"/><path d="M0 48L22 36L44 46L66 32L100 46V56H0Z" fill="${mixc(b, -.7)}" opacity=".8" class="bgm"/><ellipse cx="30" cy="46" rx="34" ry="5" fill="#fff" opacity=".25" filter="url(#mist)"/><ellipse cx="78" cy="50" rx="30" ry="4" fill="#fff" opacity=".2" filter="url(#mist)"/>${speedL(k, f)}<g class="mt" filter="url(#bv)">${interior}</g><rect width="100" height="56" fill="url(#hz-${k})"/><rect width="100" height="56" filter="url(#nz)" opacity=".14"/>${sparkF(f)}</svg>`
}

/** SVG del arte de la carta con id (o fallback de secta). */
export function arteCarta(id: string): string {
  return art(id)
}

export default arteCarta
