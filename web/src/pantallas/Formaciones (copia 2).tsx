/** Pantalla Formaciones (`frUI` de js/04-mazos-formaciones.js:57).

Catálogo de formaciones, runas y técnicas con «Disipar Formación»
(`dsp`): reglas de uso, leyendas de insignias/propiedades, filtros
(all/F/R/mi secta/las que tengo) y compra directa por piedras
espirituales (`buy` de js/03-cartas-mercado.js:8).
*/

import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/cliente'
import { arteCarta } from '../arte/artCarta'
import type {
  CartaResumen,
  EnemigoResumen,
  SectaResumen,
  SnapshotPartida,
} from '../api/tipos'
import { mensajeDe, nombreRareza, precioCompraLocal } from './Mercado'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  sectas: SectaResumen[]
  onSnapshot: (snapshot: SnapshotPartida) => void
}

const COLOR_RAREZA = [
  '#aab8b2',
  '#6cc4a1',
  '#5aa0e8',
  '#b070e0',
  '#e8a23a',
  '#ff6a6a',
]

/** `DF` de js/01-datos.js:111: nombres de dificultad. */
const DIFICULTADES = [
  'Muy fácil',
  'Fácil',
  'Normal',
  'Difícil',
  'Muy difícil',
  'Boss final',
]

/** Propiedades de cartas (`KI` de js/04-mazos-formaciones.js:68). */
const KI: Record<string, [string, string]> = {
  rf: [
    'Renovar: devuelve tu mano al mazo y roba cartas nuevas al azar',
    '<path d="M10.2 6.2A4.2 4.2 0 1 1 8.6 2.9M9.2 1.2V4H6.4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
  ],
  tk: [
    'Provocar: hay que atacarla primero',
    '<path d="M6 1L10.5 2.6V6.2C10.5 8.7 8.7 10.4 10.4 8.7M6 10.5H3.3V6.6L6 10.5Z"/>',
  ],
  rs: [
    'Ímpetu: ataca el turno en que entra',
    '<path d="M7.2 1L2.6 6.6H5.6L4.8 11 9.4 5.2H6.4Z"/>',
  ],
  vm: [
    'Roba vida: cura lo que daña',
    '<path d="M6 10.6C2.2 7.8 1.6 5.8 1.6 4.4 1.6 2.9 2.8 2 4 2 5 2 5.7 2.5 6 3.2 6.3 2.5 7 2 8 2 9.2 2 10.4 2.9 10.4 4.4 10.4 5.8 9.8 7.8 6 10.6Z"/>',
  ],
  gr: [
    'Crece: gana ataque al atacar',
    '<path d="M6 1.2L10.3 6H7.4V10.8H4.6V6H1.7Z"/>',
  ],
  ul: [
    'Último aliento: efecto al morir',
    '<path d="M6 1.2A4.2 4.2 0 0 0 3.4 8.8V10.8H8.6V8.8A4.2 4.2 0 0 0 6 1.2Z"/><circle cx="4.6" cy="6" r="1" fill="#0b1514"/><circle cx="7.4" cy="6" r="1" fill="#0b1514"/>',
  ],
  bc: [
    'Al entrar: efecto inmediato',
    '<path d="M6 11L1.8 6.4H4.6V1.2H7.4V6.4H10.2Z"/>',
  ],
  ab: [
    'Activa: habilidad que cuesta Qi',
    '<path d="M6 .9L7.4 4.6 11.1 6 7.4 7.4 6 11.1 4.6 7.4 .9 6 4.6 4.6Z"/>',
  ],
  fz: [
    'Congela: pierde su próximo ataque',
    '<path d="M6 1V11M1.7 3.5L10.3 8.5M1.7 8.5L10.3 3.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
  ],
  k: [
    'Espada: cada 3ª técnica de espada da +3 de daño a la siguiente',
    '<path d="M9.6 1.4L5.4 5.6 6.4 6.6 10.6 2.4ZM4.6 6.4L1.6 9.4 2.6 10.4 5.6 7.4Z"/>',
  ],
  dsp: [
    'Disipa formaciones y runas rivales',
    '<circle cx="6" cy="6" r="4.2" stroke="currentColor" stroke-width="1.4" fill="none"/><path d="M3.5 8.5L8.5 3.5" stroke="currentColor" stroke-width="1.4"/>',
  ],
  eq: [
    'Drena Qi: el rival pierde Qi en su turno',
    '<path d="M2.6 1.2H9.4L6.9 6 9.4 10.8H2.6L5.1 6Z"/>',
  ],
  dr: [
    'Roba cartas',
    '<rect x="2.4" y="3" width="6" height="7.6" rx="1"/><path d="M4.4 1.4H9.6V8" stroke="currentColor" stroke-width="1.2" fill="none"/>',
  ],
  sac: [
    'Pagas vida al jugarla',
    '<path d="M6 10.6C2.2 7.8 1.6 5.8 1.6 4.4 1.6 2.9 2.8 2 4 2 5 2 5.7 2.5 6 3.2 6.3 2.5 7 2 8 2 9.2 2 10.4 2.9 10.4 4.4 10.4 5.8 9.8 7.8 6 10.6Z" fill="none" stroke="currentColor" stroke-width="1.3"/>',
  ],
}

type Filtro = 'all' | 'F' | 'R' | 'sec' | 'own'

/** `SX` de js/04: 'neu' cuenta como sin secta. */
function sectaVisible(carta: CartaResumen): string | null {
  return carta.secta === null || carta.secta === 'neu' ? null : carta.secta
}

/** `howGet` de js/04-mazos-formaciones.js:39. */
function comoObtener(
  carta: CartaResumen,
  enemigos: EnemigoResumen[],
  sectas: SectaResumen[],
  miSecta: string | null,
): string[] {
  const rareza = carta.rareza
  const secta = sectaVisible(carta)
  const lineas: string[] = []
  if (carta.es_neutral) {
    lineas.push('🎁 Gratis: carta neutral, ya la tienes (×3).')
    return lineas
  }
  if (rareza >= 5) {
    lineas.push(
      '🏆 No se vende: es de las cartas más poderosas y solo cae de jefes.',
    )
  } else {
    const nombreSecta = secta
      ? (sectas.find((s) => s.identificador === secta)?.nombre ?? secta)
      : 'General'
    lineas.push(
      `💎 Mercado: puesto ${nombreSecta} · ${precioCompraLocal(rareza)} piedras espirituales` +
        (secta && secta !== miSecta
          ? ' · 🔒 solo discípulos de esa secta'
          : ''),
    )
  }
  const premio = enemigos.find((e) => {
    const rw = e.rareza_recompensa ?? -1
    return rw >= rareza && rw <= rareza + 2
  })
  if (premio) {
    const tope = Math.min(5, rareza + 2)
    lineas.push(
      `⚔ Premio de combate: enemigos con recompensa ${nombreRareza(rareza)} a ${nombreRareza(tope)}. ` +
        `El primero: nivel ${premio.indice_nivel + 1}, ${premio.nombre_enemigo} (${DIFICULTADES[premio.dificultad]}).`,
    )
  }
  return lineas
}

/** Insignia de leyenda (`lg` de js/04:60). */
function Insignia({ clase, icono, texto }: { clase: string; icono: string; texto: string }) {
  return (
    <em className={`bg ${clase}`}>
      <span className="ic" aria-hidden="true">
        {icono}
      </span>
      {texto}
    </em>
  )
}

export default function Formaciones({
  slot,
  snapshot,
  sectas,
  onSnapshot,
}: Props) {
  const [cartas, setCartas] = useState<CartaResumen[]>([])
  const [enemigos, setEnemigos] = useState<EnemigoResumen[]>([])
  const [filtro, setFiltro] = useState<Filtro>('all')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState<string | null>(null)
  /** Ficha expandida: una carta a la vez se abre con su detalle completo. */
  const [expandida, setExpandida] = useState<string | null>(null)

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [listaCartas, listaEnemigos] = await Promise.all([
          api.listarCartas(),
          api.listarEnemigos(),
        ])
        if (!vigente) return
        setCartas(listaCartas)
        setEnemigos(listaEnemigos)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const miSecta = snapshot.sc ?? snapshot.sect
  const tienen = (carta: CartaResumen) =>
    carta.es_neutral || (snapshot.col[carta.identificador] ?? 0) > 0

  const todas = useMemo(
    () =>
      cartas.filter(
        (carta) =>
          carta.tipo === 'F' || carta.tipo === 'R' || carta.disipa,
      ),
    [cartas],
  )

  const visibles = useMemo(() => {
    const predicados: Record<Filtro, (carta: CartaResumen) => boolean> = {
      all: () => true,
      F: (carta) => carta.tipo === 'F',
      R: (carta) => carta.tipo === 'R',
      sec: (carta) => sectaVisible(carta) === miSecta,
      own: (carta) => tienen(carta),
    }
    return todas
      .filter(predicados[filtro])
      .sort(
        (a, b) =>
          'FRT'.indexOf(a.tipo) - 'FRT'.indexOf(b.tipo) ||
          a.coste_qi - b.coste_qi,
      )
  }, [todas, filtro, miSecta, snapshot.col])

  const comprar = async (carta: CartaResumen) => {
    try {
      const resultado = await api.comprarCarta(slot, carta.identificador)
      setMensaje(resultado.mensaje)
      setError(null)
      onSnapshot(resultado.snapshot)
    } catch (errorDeLlamada) {
      setMensaje('')
      setError(mensajeDe(errorDeLlamada))
    }
  }

  const filtros: Array<[Filtro, string]> = [
    ['all', 'Todas'],
    ['F', 'Formaciones'],
    ['R', 'Runas'],
    ['sec', 'Mi secta'],
    ['own', 'Las que tengo'],
  ]

  return (
    <section className="pantalla formaciones" aria-label="Formaciones">
      <h1>Formaciones y Runas</h1>
      <div className="pi">
        <p className="q">
          Tienes {todas.filter(tienen).length} de {todas.length}. Tú y tus
          enemigos las usan con las mismas reglas.
        </p>
        <ul className="fru">
          <li>
            <b>阵 Formación</b>: solo 1 por bando; dura hasta que la
            reemplacen o la disipen. Da un bono continuo (ATK, vida) o un
            efecto al inicio de tu turno.
          </li>
          <li>
            <b>符 Runa</b>: hasta 2 por bando (la tercera reemplaza a la más
            antigua). Dura 2 o 3 turnos y actúa al inicio de tu turno.
          </li>
          <li>
            <b>Contrarresto</b>: <i>Disipar Formación</i> destruye las
            formaciones y runas del rival.
          </li>
        </ul>
        <div className="leg">
          <span>Insignias de las cartas:</span>
          <Insignia clase="a" icono="⚔" texto="Ataque" />
          <Insignia clase="h" icono="♥" texto="Vida" />
          <Insignia clase="s" icono="◈" texto="Escudo" />
          <Insignia clase="q" icono="✦" texto="Qi" />
        </div>
        <div className="leg kl">
          {Object.entries(KI).map(([clave, [texto, path]]) => (
            <span key={clave} className="kn">
              <em className={`kc k-${clave}`} title={texto} aria-label={texto}>
                <svg
                  viewBox="0 0 12 12"
                  fill="currentColor"
                  aria-hidden="true"
                  dangerouslySetInnerHTML={{ __html: path }}
                />
              </em>
              {texto.split(':')[0]}
            </span>
          ))}
        </div>
      </div>

      {mensaje && <div className="pouch">{mensaje}</div>}
      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      <div className="sects wsel" role="tablist" aria-label="Filtrar">
        {filtros.map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            className={`chip${filtro === clave ? ' on' : ''}`}
            aria-pressed={filtro === clave}
            onClick={() => {
              setFiltro(clave)
              setMensaje('')
            }}
          >
            {texto}
          </button>
        ))}
      </div>

      <div className="fl">
        {visibles.map((carta) => {
          const copias = snapshot.col[carta.identificador] ?? 0
          const secta = sectaVisible(carta)
          const okComprable =
            !carta.es_neutral &&
            carta.rareza < 5 &&
            (secta === null || secta === miSecta)
          const precio = precioCompraLocal(carta.rareza)
          const abierta = expandida === carta.identificador
          const resumen = carta.descripcion[0] ?? ''
          return (
            <div
              key={carta.identificador}
              className={`fri${tienen(carta) ? ' in' : ''}${abierta ? ' abierta' : ''}`}
            >
              <div
                className="frt"
                aria-hidden="true"
                dangerouslySetInnerHTML={{ __html: arteCarta(carta.identificador) }}
              />
              <div className="frb">
                <b style={{ color: COLOR_RAREZA[carta.rareza] }}>
                  {carta.nombre}
                </b>
                <small className="mu">
                  {carta.tipo === 'F'
                    ? 'Formación'
                    : carta.tipo === 'R'
                      ? 'Runa'
                      : 'Técnica'}{' '}
                  · {secta ? (sectas.find((s) => s.identificador === secta)?.nombre ?? secta) : 'Neutral'} · coste{' '}
                  {carta.coste_qi} · {nombreRareza(carta.rareza)}
                </small>
                <div className="frd">
                  {abierta
                    ? carta.descripcion.join(' · ')
                    : resumen.length > 90
                      ? `${resumen.slice(0, 90)}…`
                      : resumen}
                </div>
                {abierta &&
                  comoObtener(carta, enemigos, sectas, miSecta).map((linea) => (
                    <p key={linea}>{linea}</p>
                  ))}
                <div className="fra">
                  <span>
                    {carta.es_neutral
                      ? 'Tienes 3 (gratis)'
                      : `Tienes ${copias}/3`}
                  </span>
                  <button
                    type="button"
                    className="chip"
                    aria-expanded={abierta}
                    onClick={() =>
                      setExpandida(abierta ? null : carta.identificador)
                    }
                  >
                    {abierta ? 'Cerrar ficha' : 'Ver ficha'}
                  </button>
                  {okComprable && (
                    <button
                      type="button"
                      disabled={snapshot.stn < precio || copias >= 3}
                      onClick={() => void comprar(carta)}
                    >
                      {copias >= 3 ? 'Máximo' : <>Comprar 💎 {precio}</>}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
        {visibles.length === 0 && (
          <p className="nl">No tienes cartas en esta categoría.</p>
        )}
      </div>
    </section>
  )
}
