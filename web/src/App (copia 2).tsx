/** Shell del juego: splash de conexión y pestañas (Campaña/Alquimia/Guía).

Como en el monolito no hay selector de partidas: existe una sola
partida, con el slot fijo `viaje` (equivalente al `xcg3` del original).
Al entrar se carga; si no existe aún, se crea automáticamente.

La pestaña y el combate en curso se persisten (`persistencia.ts`) para
que una recarga (F5) vuelva al mismo sitio —incluso reanudando el
combate— en vez de empezar siempre en la bienvenida.
*/

import { useCallback, useEffect, useState } from 'react'
import { api, ErrorApi } from './api/cliente'
import type {
  EstadoServidor,
  Narrativa,
  SectaResumen,
  SnapshotPartida,
} from './api/tipos'
import Alquimia from './pantallas/Alquimia'
import Bolsa from './pantallas/Bolsa'
import Campamento from './pantallas/Campamento'
import Combate from './pantallas/Combate'
import Equipo from './pantallas/Equipo'
import Formaciones from './pantallas/Formaciones'
import Gacha from './pantallas/Gacha'
import Guia from './pantallas/Guia'
import Jardin from './pantallas/Jardin'
import Mazos from './pantallas/Mazos'
import Mazmorras from './pantallas/Mazmorras'
import Mercado from './pantallas/Mercado'
import Misiones from './pantallas/Misiones'
import Puerta from './pantallas/Puerta'
import Splash from './pantallas/Splash'
import Trajes from './pantallas/Trajes'
import {
  guardarPantalla,
  leerPantalla,
  limpiarPantalla,
  type PantallaJuego,
  type Pestana,
} from './persistencia'

/** Slot único de la partida (el `xcg3` del monolito). */
const SLOT = 'viaje'

type Pantalla =
  | { nombre: 'splash' }
  | { nombre: 'juego'; pestana: Pestana; combate: number | null }

/** Títulos de las pestañas (`TB` de js/04-mazos-formaciones.js:71). */
const TITULOS: Record<Pestana, string> = {
  camp: 'Campaña',
  alq: 'Alquimia',
  dgn: 'Mazmorras',
  mis: 'Misiones',
  jar: 'Jardín',
  dk: 'Mazos',
  mkt: 'Mercado',
  fr: 'Formaciones',
  gacha: 'Gacha',
  eqp: 'Equipo',
  trj: 'Trajes',
  bag: 'Bolsa',
  gui: 'Guía',
}

/** Iconos SVG de las pestañas (`TB` de js/04-mazos-formaciones.js:71). */
const ICONOS: Partial<Record<Pestana, string>> = {
  camp: '<path d="M1.5 14L6 5.5l3 5 2-3L14.5 14Z" fill="currentColor"/>',
  alq: '<path d="M6 2h4M7 2v4.2L3.4 12.6a1 1 0 0 0 .9 1.5h7.4a1 1 0 0 0 .9-1.5L9 6.2V2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
  dgn: '<path d="M3 14V7.5a5 5 0 0 1 10 0V14Z M8 9.5V14" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
  mis: '<path d="M4 2h8v12H4Z M6.2 5.2h3.6M6.2 8h3.6M6.2 10.8h2" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>',
  jar: '<path d="M8 14V6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M8 6c0-2.5 2-4.5 5-4.5 0 2.5-2 4.5-5 4.5Z M8 8.5C8 6.6 6.4 5 4 5c0 1.9 1.6 3.5 4 3.5Z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>',
  mkt: '<path d="M8 1.6L13.4 6 8 14.4 2.6 6Z M2.6 6h10.8" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>',
  dk: '<rect x="5" y="2.4" width="8" height="11" rx="1.3" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M2.6 4.6v9h7.4" fill="none" stroke="currentColor" stroke-width="1.3"/>',
  fr: '<path d="M5.3 1.8h5.4l3.5 3.5v5.4l-3.5 3.5H5.3l-3.5-3.5V5.3Z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><circle cx="8" cy="8" r="1.9" fill="currentColor"/>',
  bag: '<path d="M4.2 5.2h7.6l.9 8.8H3.3Z M6 5.2V4a2 2 0 0 1 4 0v1.2" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>',
  eqp: '<path d="M8 1.8l5 1.7v4.1c0 3.2-2.2 5.4-5 6.4-2.8-1-5-3.2-5-6.4V3.5Z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
  trj: '<path d="M8 6.2L1.8 11.2a.9.9 0 0 0 .6 1.6h11.2a.9.9 0 0 0 .6-1.6L8 6.2V5a1.7 1.7 0 1 0-1.7-1.7" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>',
  gui: '<path d="M3 2.5h6.5A2.5 2.5 0 0 1 12 5v9a2 2 0 0 0-2-2H3Z M13.5 2.5H9.5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>',
}

/**
 * Grupos desplegables del menú (`MENUS` de js/05-arte.js:4): al final
 * quedan Campaña, Guía y el atajo Gacha como botones sueltos (el
 * monolito los muestra como `.hzb`).
 */
const GRUPOS: Array<{
  id: string
  nombre: string
  icono: string
  claves: Pestana[]
}> = [
  { id: 'mCul', nombre: 'Cultivo', icono: '🌱', claves: ['alq', 'dgn', 'mis', 'jar'] },
  { id: 'mCar', nombre: 'Cartas', icono: '🃏', claves: ['mkt', 'dk', 'fr'] },
  { id: 'mPer', nombre: 'Cultivador', icono: '🛡', claves: ['eqp', 'trj', 'bag'] },
]

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** Icono SVG decorativo de una pestaña (el texto manda para el a11y). */
function iconoDe(clave: Pestana): string {
  const trazo = ICONOS[clave]
  if (!trazo) return ''
  return `<svg class="di" viewBox="0 0 16 16" aria-hidden="true">${trazo}</svg>`
}

export default function App() {
  const [pantalla, setPantalla] = useState<Pantalla>({ nombre: 'splash' })
  const [servidor, setServidor] = useState<EstadoServidor | null>(null)
  const [narrativa, setNarrativa] = useState<Narrativa | null>(null)
  const [sectas, setSectas] = useState<SectaResumen[]>([])
  const [snapshot, setSnapshot] = useState<SnapshotPartida | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuAbierto, setMenuAbierto] = useState<string | null>(null)
  const [misionLista, setMisionLista] = useState(false)

  // Cierra el desplegable abierto al pulsar fuera (`.dd` del monolito).
  useEffect(() => {
    if (menuAbierto === null) return
    const alPulsar = (evento: MouseEvent) => {
      const objetivo = evento.target as HTMLElement | null
      if (!objetivo?.closest?.('.dd')) setMenuAbierto(null)
    }
    document.addEventListener('click', alPulsar)
    return () => document.removeEventListener('click', alPulsar)
  }, [menuAbierto])

  // Badge «!» de la pestaña Misiones (`misReady` de js/12-v47-init.js:103).
  useEffect(() => {
    if (pantalla.nombre !== 'juego') return
    let vigente = true
    void (async () => {
      try {
        const resultado = await api.listarMisiones(SLOT)
        if (vigente) setMisionLista(resultado.misiones.some((m) => m.lista))
      } catch {
        if (vigente) setMisionLista(false)
      }
    })()
    return () => {
      vigente = false
    }
  }, [pantalla.nombre, snapshot])

  const conectar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const [estado, textos, listaSectas] = await Promise.all([
        api.obtenerEstado(),
        api.obtenerNarrativa(),
        api.listarSectas(),
      ])
      setServidor(estado)
      setNarrativa(textos)
      setSectas(listaSectas)
      return true
    } catch (errorDeConexion) {
      setError(mensajeDe(errorDeConexion))
      return false
    } finally {
      setCargando(false)
    }
  }, [])

  /** Cambia de pantalla y persiste el destino entre recargas. */
  const irA = useCallback((destino: PantallaJuego) => {
    guardarPantalla(destino)
    setPantalla({ nombre: 'juego', ...destino })
  }, [])

  /** Carga la partida única; si no existe, la crea (como el xcg3 del JS). */
  const entrar = useCallback(
    async (destino?: PantallaJuego) => {
      setError(null)
      try {
        let partida
        try {
          partida = await api.obtenerPartida(SLOT)
        } catch (errorDeCarga) {
          if (
            errorDeCarga instanceof ErrorApi &&
            errorDeCarga.codigo === 'not_found'
          ) {
            partida = await api.crearPartida(SLOT)
          } else {
            throw errorDeCarga
          }
        }
        if (partida.snapshot) setSnapshot(partida.snapshot)
        irA(destino ?? leerPantalla() ?? { pestana: 'camp', combate: null })
      } catch (errorDeEntrada) {
        setError(mensajeDe(errorDeEntrada))
      }
    },
    [irA],
  )

  useEffect(() => {
    // Tras conectar, si había una pestaña/combate guardados (recarga),
    // se vuelve ahí directamente sin pasar por la bienvenida.
    void (async () => {
      const conectado = await conectar()
      if (!conectado) return
      const guardada = leerPantalla()
      if (guardada) void entrar(guardada)
    })()
  }, [conectar, entrar])

  if (pantalla.nombre === 'splash') {
    return (
      <main className="app">
        <Splash
          servidor={servidor}
          narrativa={narrativa}
          cargando={cargando}
          error={error}
          onReintentar={() => void conectar()}
          onEntrar={() => void entrar()}
        />
      </main>
    )
  }

  const pestanaActiva = pantalla.pestana
  const combateActivo = pantalla.combate

  if (combateActivo !== null && snapshot) {
    return (
      <main className="app en-combate">
        <Combate
          key={combateActivo}
          slot={SLOT}
          indiceEnemigo={combateActivo}
          snapshot={snapshot}
          narrativa={narrativa}
          onSnapshot={setSnapshot}
          onSalir={() => irA({ pestana: 'camp', combate: null })}
          onMorir={() => {
            // Muerte permanente: vuelve a la bienvenida (`reborn()` JS).
            limpiarPantalla()
            setPantalla({ nombre: 'splash' })
          }}
        />
      </main>
    )
  }

  // Sin secta elegida: solo la Puerta (`gate()` del monolito), sin menús.
  if (snapshot && snapshot.sc == null) {
    return (
      <main className="app">
        <Puerta slot={SLOT} sectas={sectas} onSnapshot={setSnapshot} />
      </main>
    )
  }

  return (
    <main className="app">
      <nav className="tabs" aria-label="Menú principal">
        <button
          type="button"
          className={`tab${pestanaActiva === 'camp' ? ' activa' : ''}`}
          aria-current={pestanaActiva === 'camp' ? 'page' : undefined}
          onClick={() => irA({ pestana: 'camp', combate: null })}
        >
          <span
            aria-hidden="true"
            dangerouslySetInnerHTML={{ __html: iconoDe('camp') }}
          />
          <span>{TITULOS.camp}</span>
        </button>

        {GRUPOS.map((grupo) => {
          const abierto = menuAbierto === grupo.id
          const activo = grupo.claves.includes(pestanaActiva)
          return (
            <div key={grupo.id} className={`dd${activo ? ' on' : ''}`}>
              <button
                type="button"
                className={`tab${abierto ? ' open' : ''}`}
                aria-haspopup="true"
                aria-expanded={abierto}
                aria-label={grupo.nombre}
                title={grupo.nombre}
                onClick={() => setMenuAbierto(abierto ? null : grupo.id)}
              >
                <span className="di" aria-hidden="true">
                  {grupo.icono}
                </span>
                <span>{grupo.nombre}</span>
                <span className="ca" aria-hidden="true">
                  ▾
                </span>
                {grupo.claves.includes('mis') && misionLista && (
                  <i className="bang" role="status" aria-label="Misión lista para reclamar">
                    !
                  </i>
                )}
              </button>
              {abierto && (
                <div className="dm" role="group" aria-label={grupo.nombre}>
                  {grupo.claves.map((clave) => (
                    <button
                      key={clave}
                      type="button"
                      className={pestanaActiva === clave ? 'on' : ''}
                      aria-current={pestanaActiva === clave ? 'page' : undefined}
                      aria-label={TITULOS[clave]}
                      title={TITULOS[clave]}
                      onClick={() => {
                        setMenuAbierto(null)
                        irA({ pestana: clave, combate: null })
                      }}
                    >
                      <span
                        aria-hidden="true"
                        dangerouslySetInnerHTML={{ __html: iconoDe(clave) }}
                      />
                      <span>{TITULOS[clave]}</span>
                      {clave === 'mis' && misionLista && (
                        <i className="bang" role="status" aria-label="Misión lista para reclamar">
                          !
                        </i>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        <button
          type="button"
          className={`tab${pestanaActiva === 'gui' ? ' activa' : ''}`}
          aria-current={pestanaActiva === 'gui' ? 'page' : undefined}
          onClick={() => irA({ pestana: 'gui', combate: null })}
        >
          <span
            aria-hidden="true"
            dangerouslySetInnerHTML={{ __html: iconoDe('gui') }}
          />
          <span>{TITULOS.gui}</span>
        </button>

        {/* Atajo `.hzb gachab` del monolito: el icono es decorativo para
            que el nombre accesible siga siendo «Gacha». */}
        <button
          type="button"
          className={`tab hzb gachab${pestanaActiva === 'gacha' ? ' activa' : ''}`}
          aria-current={pestanaActiva === 'gacha' ? 'page' : undefined}
          onClick={() => irA({ pestana: 'gacha', combate: null })}
        >
          <span aria-hidden="true">🧿</span>
          <span>{TITULOS.gacha}</span>
        </button>
      </nav>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {pestanaActiva === 'camp' && snapshot && (
        <Campamento
          snapshot={snapshot}
          narrativa={narrativa}
          sectas={sectas}
          onCombatir={(indice) => irA({ pestana: 'camp', combate: indice })}
          onReiniciar={() => {
            limpiarPantalla()
            setPantalla({ nombre: 'splash' })
          }}
        />
      )}

      {pestanaActiva === 'alq' && snapshot && (
        <Alquimia slot={SLOT} snapshot={snapshot} onSnapshot={setSnapshot} />
      )}

      {pestanaActiva === 'dgn' && snapshot && (
        <Mazmorras
          snapshot={snapshot}
          onCombatir={(indice) => irA({ pestana: 'camp', combate: indice })}
        />
      )}

      {pestanaActiva === 'mis' && snapshot && (
        <Misiones
          slot={SLOT}
          snapshot={snapshot}
          onSnapshot={setSnapshot}
        />
      )}

      {pestanaActiva === 'jar' && snapshot && (
        <Jardin slot={SLOT} onSnapshot={setSnapshot} />
      )}

      {pestanaActiva === 'dk' && snapshot && (
        <Mazos
          slot={SLOT}
          snapshot={snapshot}
          sectas={sectas}
          onSnapshot={setSnapshot}
        />
      )}

      {pestanaActiva === 'mkt' && snapshot && (
        <Mercado
          slot={SLOT}
          snapshot={snapshot}
          sectas={sectas}
          onSnapshot={setSnapshot}
        />
      )}

      {pestanaActiva === 'fr' && snapshot && (
        <Formaciones
          slot={SLOT}
          snapshot={snapshot}
          sectas={sectas}
          onSnapshot={setSnapshot}
        />
      )}

      {pestanaActiva === 'gacha' && snapshot && (
        <Gacha slot={SLOT} snapshot={snapshot} onSnapshot={setSnapshot} />
      )}

      {pestanaActiva === 'eqp' && snapshot && (
        <Equipo slot={SLOT} snapshot={snapshot} onSnapshot={setSnapshot} />
      )}

      {pestanaActiva === 'trj' && snapshot && (
        <Trajes slot={SLOT} snapshot={snapshot} onSnapshot={setSnapshot} />
      )}

      {pestanaActiva === 'bag' && snapshot && <Bolsa snapshot={snapshot} />}

      {pestanaActiva === 'gui' && <Guia sectas={sectas} />}
    </main>
  )
}
