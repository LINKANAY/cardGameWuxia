/** Trajes: armario de la secta con desbloqueos por victorias (tab `trj`).

Port de `trj()` (js/06-contenido.js:168): los 6 trajes de la secta del
jugador, con el retrato `fig(k, 0, i)` y el efecto (`OA`). Vestir va al
backend (`traje/vestir`); el traje puesto vive en el snapshot (`of`).
*/

import { useCallback, useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type { ResultadoEquipo, SnapshotPartida, TrajeResumen } from '../api/tipos'
import { figuraSecta } from '../arte/figura'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  onSnapshot: (snapshot: SnapshotPartida) => void
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

export default function Trajes({ slot, snapshot, onSnapshot }: Props) {
  const [trajes, setTrajes] = useState<TrajeResumen[]>([])
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const recargar = useCallback(async () => {
    try {
      setTrajes(await api.trajesCatalogo())
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void recargar()
  }, [recargar])

  const vestir = useCallback(
    async (traje: TrajeResumen) => {
      setError(null)
      setAviso(null)
      try {
        const resultado: ResultadoEquipo = await api.vestirTraje(
          slot,
          traje.secta,
          traje.indice,
        )
        setAviso(resultado.mensaje)
        onSnapshot(resultado.snapshot)
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      }
    },
    [slot, onSnapshot],
  )

  const sect = snapshot.sect
  const mios = trajes.filter((t) => t.secta === sect)
  const victorias = snapshot.wins.length
  const puesto = snapshot.of[sect] ?? 0

  return (
    <section className="pantalla trajes" aria-label="Trajes">
      <h1>Armario del cultivador</h1>
      <p className="q">
        Cada secta tiene {mios.length} trajes y cada uno da una habilidad en
        combate. Se desbloquean con victorias totales (
        {mios.map((t) => t.umbral).join(', ')}); las misiones secundarias y
        las mazmorras también cuentan. Solo puedes vestir los trajes de tu
        secta.
      </p>

      {aviso && (
        <div className="aviso-exito" role="status">
          {aviso}
        </div>
      )}
      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}
      {cargando && <p>Cargando trajes…</p>}

      {!cargando && (
        <div className="grid">
          {mios.map((traje) => {
            const ok = victorias >= traje.umbral
            const actual = puesto === traje.indice
            return (
              <button
                key={`${traje.secta}-${traje.indice}`}
                type="button"
                className={`opt tj${actual ? ' eqd' : ''}`}
                disabled={!ok}
                onClick={() => void vestir(traje)}
              >
                <span
                  className="eq-arte"
                  aria-hidden="true"
                  dangerouslySetInnerHTML={{
                    __html: figuraSecta(traje.secta, false, traje.indice),
                  }}
                />
                <b>{traje.nombre}</b>
                <small className="oab">
                  <u>{traje.efecto}</u>: {traje.descripcion}
                </small>
                <small>
                  {actual
                    ? 'Equipado'
                    : ok
                      ? 'Pulsa para equipar'
                      : `Se desbloquea con ${traje.umbral} victorias (${victorias}/${traje.umbral})`}
                </small>
              </button>
            )
          })}
        </div>
      )}
    </section>
  )
}
