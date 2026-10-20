/** Persistencia de la pestaña/combate activo entre recargas (F5).

El estado de UI vive en memoria; al recargar se pierde. Aquí se guarda
sólo «dónde estaba» (pestaña + combate en curso) para que App pueda
volver ahí directamente tras el arranque, sin pasar por el splash.

Todo envuelto en try/catch: si localStorage falla, se ignora y se
empieza en la bienvenida.
 */

/** Pestañas del shell (`TB` del monolito, versión reducida). */
export type Pestana =
  | 'camp'
  | 'alq'
  | 'dgn'
  | 'mis'
  | 'dk'
  | 'mkt'
  | 'fr'
  | 'gacha'
  | 'eqp'
  | 'trj'
  | 'bag'
  | 'gui'

/** Dónde estaba el jugador: pestaña y, si hay combate, su índice. */
export interface PantallaJuego {
  pestana: Pestana
  combate: number | null
}

const CLAVE = 'sdi_pantalla'

const PESTANAS_VALIDAS: Pestana[] = [
  'camp',
  'alq',
  'dgn',
  'mis',
  'dk',
  'mkt',
  'fr',
  'gacha',
  'eqp',
  'trj',
  'bag',
  'gui',
]

/** `fr` es el nombre legacy de la pestaña Gacha (guardados previos). */
const MAPEO_LEGACY: Partial<Record<Pestana, Pestana>> = {
  fr: 'gacha',
}

/** Lee la última pestaña/combate guardados, o `null` si no hay. */
export function leerPantalla(): PantallaJuego | null {
  try {
    const crudo = localStorage.getItem(CLAVE)
    if (crudo == null) return null
    const obj: unknown = JSON.parse(crudo)
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return null
    const dato = obj as Record<string, unknown>
    const cruda = dato.pestana as Pestana
    const pestana = PESTANAS_VALIDAS.includes(cruda)
      ? (MAPEO_LEGACY[cruda] ?? cruda)
      : 'camp'
    const combate =
      typeof dato.combate === 'number' && Number.isInteger(dato.combate)
        ? dato.combate
        : null
    return { pestana, combate }
  } catch {
    return null
  }
}

/** Guarda la pestaña/combate actuals (se llama en cada cambio de pantalla). */
export function guardarPantalla(pantalla: PantallaJuego): void {
  try {
    localStorage.setItem(CLAVE, JSON.stringify(pantalla))
  } catch {
    /* almacenamiento no disponible: se ignora */
  }
}

/** Borra la pestaña/combate guardados (volver a la bienvenida). */
export function limpiarPantalla(): void {
  try {
    localStorage.removeItem(CLAVE)
  } catch {
    /* almacenamiento no disponible: se ignora */
  }
}
