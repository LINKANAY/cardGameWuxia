/** Campamento: perfil del cultivador + mapa de la campaña.

El perfil replica `.cultivator-profile` de js/06-contenido.js:175: figura
procedural del cultivador (`fig()` de js/05-arte.js:183), secta y reino
con puntos de progreso, estadísticas (victorias, cartas, Qi, vida,
caídos). Los recursos (piedras, materiales, píldoras…) se muestran en
la pestaña Bolsa; aquí solo van las stats del perfil.

El mapa replica el tab `camp` del monolito (`camp()` en
`js/06-contenido.js:179`): 8 niveles × 6 enemigos (índices 0–47 del
bestiario). Un nivel se desbloquea al vencer al jefe del anterior
(`wins` incluye `(li-1)*6+5`); dentro del nivel, el enemigo `d` se abre
si `d==0` o si ya ganaste a `d-1`.

El botón «Reiniciar partida» replica `rstGame` (js/06-contenido.js:73):
doble confirmación; al confirmar, el backend crea una partida nueva
(`POST /api/game/new`) y se vuelve a la bienvenida.
*/

import { useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import { figuraSecta } from '../arte/figura'
import type {
  EnemigoResumen,
  Narrativa,
  SectaResumen,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  snapshot: SnapshotPartida
  narrativa: Narrativa | null
  sectas: SectaResumen[]
  onCombatir: (indice: number) => void
  onReiniciar: () => void
}

/** Dificultades del monolito (`DF`). */
const DIFICULTADES = [
  'Muy fácil',
  'Fácil',
  'Normal',
  'Difícil',
  'Muy difícil',
  'Boss final',
]

/** Colores de dificultad (`DC`). */
const COLOR_DIFICULTAD = [
  '#8fd9b6',
  '#6cc4a1',
  '#d9b55b',
  '#e09a4a',
  '#c4483d',
  '#b070e0',
]

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

export default function Campamento({
  snapshot,
  narrativa,
  sectas,
  onCombatir,
  onReiniciar,
}: Props) {
  const [enemigos, setEnemigos] = useState<EnemigoResumen[]>([])
  const [error, setError] = useState<string | null>(null)
  const [nivelAbierto, setNivelAbierto] = useState(0)
  const [confirmarReinicio, setConfirmarReinicio] = useState(false)
  const [reiniciando, setReiniciando] = useState(false)

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const lista = await api.listarEnemigos()
        if (!vigente) return
        // Campaña principal: solo índices 0–47 (8 niveles × 6)
        setEnemigos(lista.filter((e) => e.indice < 48))
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const nombreReino = (indice: number): string =>
    narrativa?.reinos[indice] ?? `Reino ${indice}`

  const nombreSecta = (identificador: string): string =>
    sectas.find((secta) => secta.identificador === identificador)?.nombre ??
    identificador

  /** Estadísticas del perfil (`.cultivator-stats` de js/06-contenido.js:175). */
  const cartasObtenidas = Object.values(snapshot.col).reduce(
    (total, n) => total + n,
    0,
  )
  const qiMax = Math.min(12, 6 + snapshot.realm)
  const vidaMax = 30 + 2 * snapshot.realm
  const vidaActual =
    snapshot.hp === null ? vidaMax : Math.min(snapshot.hp, vidaMax)
  const victoriasCampana = snapshot.wins.filter((k) => k < 48).length

  /** Reinicio en 2 pasos (`rstGame` del monolito). */
  const manejarReinicio = () => {
    if (reiniciando) return
    if (!confirmarReinicio) {
      setConfirmarReinicio(true)
      return
    }
    setReiniciando(true)
    void (async () => {
      try {
        await api.crearPartida('viaje')
        onReiniciar()
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
        setReiniciando(false)
        setConfirmarReinicio(false)
      }
    })()
  }

  const nivelAbiertoDe = (li: number): boolean =>
    li === 0 || snapshot.wins.includes((li - 1) * 6 + 5)

  const enemigoAbierto = (indice: number): boolean => {
    const d = indice % 6
    return d === 0 || snapshot.wins.includes(indice - 1)
  }

  const niveles: Array<{ li: number; nombre: string; abierto: boolean }> =
    Array.from({ length: 8 }, (_, li) => ({
      li,
      nombre: narrativa?.textos_intro_nivel[li] ?? `Nivel ${li + 1}`,
      abierto: nivelAbiertoDe(li),
    }))

  return (
    <section className="pantalla campamento" aria-label="Campamento">
      <h1>Campamento</h1>

      <section className="cultivator-profile" aria-label="Perfil del cultivador">
        <div
          className="pf"
          aria-hidden="true"
          dangerouslySetInnerHTML={{ __html: figuraSecta(snapshot.sect) }}
        />
        <div className="pi">
          <h2>Cultivador de {nombreSecta(snapshot.sect)}</h2>
          <div className="reino-perfil">
            Reino: <b>{nombreReino(snapshot.realm)}</b>
          </div>
          <div className="lad" aria-hidden="true">
            {(narrativa?.reinos ?? []).map((nombre, i) => (
              <i
                key={nombre}
                className={`nd${i <= snapshot.realm ? ' on' : ''}`}
                title={nombre}
              />
            ))}
          </div>
          <div className="cultivator-stats">
            <span>
              Victorias <b>{victoriasCampana}/48</b>
            </span>
            <span>
              Cartas obtenidas <b>{cartasObtenidas}</b>
            </span>
            <span>
              Qi máximo <b>{qiMax}</b>
            </span>
            <span>
              ♥ Vida <b>{vidaActual}/{vidaMax}</b>
            </span>
            <span className="fallen-stat">
              <span aria-hidden="true">☠</span> Caídos: {snapshot.dt} (mejor
              reino: {nombreReino(snapshot.bt)})
            </span>
          </div>
          <div className="acciones-perfil">
            <button
              type="button"
              className={`boton${confirmarReinicio ? ' peligro' : ''}`}
              onClick={manejarReinicio}
              disabled={reiniciando}
            >
              {reiniciando
                ? 'Reiniciando…'
                : confirmarReinicio
                  ? '¿Seguro? Se borra TODO el progreso'
                  : 'Reiniciar partida'}
            </button>
          </div>
        </div>
      </section>

      <h2>Mapa de la campaña</h2>
      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}
      {!error && enemigos.length === 0 && <p>Cargando mapa…</p>}

      <div className="mapa-campana">
        {niveles.map(({ li, nombre, abierto }) => {
          const abiertoUi = abierto || nivelAbierto === li
          const jefes = enemigos.filter((e) => e.indice >= li * 6 && e.indice < li * 6 + 6)
          const ganados = jefes.filter((e) => snapshot.wins.includes(e.indice)).length
          return (
            <div
              key={li}
              className={`lv${abierto ? '' : ' lock'}${abiertoUi ? '' : ' cl'}`}
            >
              <div
                className="lh"
                role="button"
                tabIndex={0}
                aria-expanded={abiertoUi}
                onClick={() => setNivelAbierto(abiertoUi ? -1 : li)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    setNivelAbierto(abiertoUi ? -1 : li)
                  }
                }}
              >
                <b>
                  {abiertoUi ? '▾' : '▸'} {nombre}
                </b>
                <span>
                  {abierto
                    ? `${ganados}/6 ✔`
                    : 'Bloqueado: vence al jefe anterior'}
                </span>
              </div>
              {abiertoUi && (
                <div className="en">
                  {jefes.map((enemigo) => {
                    const ok = abierto && enemigoAbierto(enemigo.indice)
                    const esJefe = enemigo.dificultad === 5
                    const ganado = snapshot.wins.includes(enemigo.indice)
                    return (
                      <button
                        key={enemigo.indice}
                        type="button"
                        className={`nodeb${esJefe ? ' boss' : ''}`}
                        style={{
                          '--dc': COLOR_DIFICULTAD[enemigo.dificultad] ?? '#aab8b2',
                        } as React.CSSProperties}
                        disabled={!ok}
                        onClick={() => onCombatir(enemigo.indice)}
                        title={enemigo.frase_inicio}
                      >
                        {ganado && <i className="ck">✔</i>}
                        <span
                          aria-hidden="true"
                          dangerouslySetInnerHTML={{
                            __html: figuraSecta(
                              enemigo.secta,
                              enemigo.dificultad >= 4,
                              enemigo.dificultad % 4,
                            ),
                          }}
                        />
                        <b>{enemigo.nombre_enemigo}</b>
                        <em style={{ color: COLOR_DIFICULTAD[enemigo.dificultad] }}>
                          {DIFICULTADES[enemigo.dificultad] ?? '—'}
                        </em>
                        <small>
                          {enemigo.vida} vida · {nombreSecta(enemigo.secta)}
                        </small>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
