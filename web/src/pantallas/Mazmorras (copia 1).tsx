/** Mazmorras secretas: acordeón de pisos con recetas (tab `dgn`).

Port de `dgn()` (js/06-contenido.js:167). Cada mazmorra se desbloquea
al vencer al jefe del nivel `nivel` (`wins` incluye `indice_receta`);
dentro, el piso `fi` se abre si `fi==0` o si ya ganaste al anterior.
La recompensa de cada piso muestra la receta si ya se aprendió
(`snapshot.rec`), o «Secreto: ???» si aún no.
*/

import { useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import { figuraSecta } from '../arte/figura'
import type {
  EnemigoResumen,
  MazmorraResumen,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  snapshot: SnapshotPartida
  onCombatir: (indice: number) => void
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

export default function Mazmorras({ snapshot, onCombatir }: Props) {
  const [mazmorras, setMazmorras] = useState<MazmorraResumen[]>([])
  const [enemigos, setEnemigos] = useState<EnemigoResumen[]>([])
  const [error, setError] = useState<string | null>(null)
  const [abierta, setAbierta] = useState(0)

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [listaMazmorras, listaEnemigos] = await Promise.all([
          api.listarMazmorras(),
          api.listarEnemigos(),
        ])
        if (!vigente) return
        setMazmorras(listaMazmorras)
        // Mazmorras: índices 48–65 (6 × 3 pisos)
        setEnemigos(listaEnemigos.filter((e) => e.indice >= 48 && e.indice < 66))
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const nombrePildora = (id: string | null): string => id ?? '???'

  return (
    <section className="pantalla mazmorras" aria-label="Mazmorras secretas">
      <h1>Mazmorras secretas</h1>
      <p className="q">
        Los alquimistas escondieron sus recetas en lugares sellados, y cada
        piso custodia un secreto. Un alquimista errante también puede
        emboscarte tras un combate de la campaña.
      </p>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}
      {!error && mazmorras.length === 0 && <p>Cargando mazmorras…</p>}

      {mazmorras.map((mazmorra) => {
        const abiertaUi =
          snapshot.wins.includes(mazmorra.indice_receta) ||
          abierta === mazmorra.indice
        const on = abiertaUi
        const ganados = mazmorra.pisos.filter((p) =>
          snapshot.wins.includes(p),
        ).length
        return (
          <div
            key={mazmorra.indice}
            className={`lv${snapshot.wins.includes(mazmorra.indice_receta) ? '' : ' lock'}${on ? '' : ' cl'}`}
          >
            <div
              className="lh"
              role="button"
              tabIndex={0}
              aria-expanded={on}
              onClick={() => setAbierta(on ? -1 : mazmorra.indice)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  setAbierta(on ? -1 : mazmorra.indice)
                }
              }}
            >
              <b>
                {on ? '▾' : '▸'} {mazmorra.nombre}
                {snapshot.wins.includes(mazmorra.indice_receta)
                  ? ` (${ganados}/3)`
                  : ''}
              </b>
              <span>
                {snapshot.wins.includes(mazmorra.indice_receta)
                  ? mazmorra.pista
                  : `Sellada: vence al jefe del Nivel ${mazmorra.nivel}`}
              </span>
            </div>
            {on && (
              <div className="en">
                {mazmorra.pisos.map((piso, fi) => {
                  const enemigo = enemigos.find((e) => e.indice === piso)
                  if (!enemigo) return null
                  const ok =
                    snapshot.wins.includes(mazmorra.indice_receta) &&
                    (fi === 0 || snapshot.wins.includes(piso - 1))
                  const ganado = snapshot.wins.includes(piso)
                  const esJefe = enemigo.dificultad === 5
                  const recetaId = mazmorra.recetas[fi]
                  const recetaConocida =
                    recetaId !== null &&
                    recetaId !== undefined &&
                    snapshot.rec[recetaId] === 1
                  return (
                    <button
                      key={piso}
                      type="button"
                      className={`nodeb${esJefe ? ' boss' : ''}`}
                      style={{
                        '--dc':
                          COLOR_DIFICULTAD[enemigo.dificultad] ?? '#aab8b2',
                      } as React.CSSProperties}
                      disabled={!ok}
                      onClick={() => onCombatir(piso)}
                      title={enemigo.frase_inicio}
                    >
                      {ganado && <i className="ck">✔</i>}
                      <span
                        aria-hidden="true"
                        dangerouslySetInnerHTML={{
                          __html: figuraSecta(
                            enemigo.secta,
                            esJefe,
                            fi,
                          ),
                        }}
                      />
                      <b>
                        Piso {fi + 1}: {enemigo.nombre_enemigo}
                      </b>
                      <em style={{ color: COLOR_DIFICULTAD[enemigo.dificultad] }}>
                        {DIFICULTADES[enemigo.dificultad] ?? '—'}
                      </em>
                      <small>{enemigo.vida} vida</small>
                      <span className="rw" style={{ color: 'var(--gold)' }}>
                        {recetaConocida
                          ? `Receta: ${nombrePildora(recetaId)}`
                          : 'Secreto: ???'}
                      </span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </section>
  )
}
