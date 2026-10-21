/** Misiones: encargos agrupados con progreso y reclamo (tab `mis`).

Port de `misUI` (js/06-contenido.js:127-132). Cada misión muestra
progreso (`qs`), recompensa y permite reclamar (`claimQ`) o seguir
(`missionTrack`). El tracker fijo aparece arriba si hay misión seguida.
Las ya reclamadas no ocupan espacio: quedan en un pliegue cerrado
al final de la pantalla.
*/

import { useCallback, useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type {
  MisionResumen,
  SnapshotPartida,
  TrackerMision,
} from '../api/tipos'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  onSnapshot: (snapshot: SnapshotPartida) => void
}

/** Nombres de grupo (`missionGroup` del JS). */
const GRUPOS = ['Combate', 'Exploración', 'Fabricación', 'Progreso'] as const

/** Etiquetas de recompensa (`rwTxt` del JS, simplificado). */
function textoRecompensa(rw: Record<string, number>): string {
  const partes: string[] = []
  if (rw.s) partes.push(`+${rw.s} piedras`)
  if (rw.h) partes.push(`+${rw.h} hierbas`)
  if (rw.n) partes.push(`+${rw.n} núcleos`)
  if (rw.p) partes.push(`+${rw.p} polvo`)
  if (rw.tes) partes.push('Talismán de Escape')
  if (rw.card != null) partes.push(`Carta rara ${rw.card}`)
  if (rw.recipe) partes.push('Receta')
  return partes.join(', ') || '—'
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

export default function Misiones({ slot, onSnapshot }: Props) {
  const [misiones, setMisiones] = useState<MisionResumen[]>([])
  const [tracker, setTracker] = useState<TrackerMision | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const recargar = useCallback(async () => {
    try {
      const resultado = await api.listarMisiones(slot)
      setMisiones(resultado.misiones)
      setTracker(resultado.tracker)
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    } finally {
      setCargando(false)
    }
  }, [slot])

  useEffect(() => {
    void recargar()
  }, [recargar])

  const reclamar = useCallback(
    async (identificador: string) => {
      setError(null)
      setAviso(null)
      try {
        const resultado = await api.reclamarMision(slot, identificador)
        setAviso(resultado.mensaje)
        if (resultado.snapshot) onSnapshot(resultado.snapshot)
        await recargar()
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      }
    },
    [slot, onSnapshot, recargar],
  )

  const seguir = useCallback(
    async (identificador: string) => {
      setError(null)
      try {
        const resultado = await api.seguirMision(slot, identificador)
        if (resultado.snapshot) onSnapshot(resultado.snapshot)
        await recargar()
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      }
    },
    [slot, onSnapshot, recargar],
  )

  const agrupar = (
    lista: MisionResumen[],
  ): Array<{ grupo: string; items: MisionResumen[] }> =>
    GRUPOS.map((grupo) => ({
      grupo,
      items: lista.filter((m) => m.grupo === grupo),
    })).filter((g) => g.items.length > 0)

  const trackerSection = tracker ? (
    <section className="mission-tracker" aria-live="polite">
      <b>Siguiendo: {tracker.nombre}</b>
      <small>
        {Math.min(tracker.progreso, tracker.meta)}/{tracker.meta} ·{' '}
        {tracker.descripcion}
      </small>
      <div className="bar2">
        <i
          style={{
            width: `${Math.min(100, (tracker.progreso / tracker.meta) * 100)}%`,
          }}
        />
      </div>
      <button
        type="button"
        className="chip"
        onClick={() => void seguir(tracker.identificador)}
      >
        Dejar de seguir
      </button>
    </section>
  ) : null

  const fila = (mision: MisionResumen) => {
    const v = Math.min(mision.progreso, mision.meta)
    const ready = mision.lista
    const tracked = tracker?.identificador === mision.identificador
    return (
      <div
        key={mision.identificador}
        className={`opt mq${ready ? ' mission-ready' : ''}${tracked ? ' mission-tracked' : ''}`}
      >
        <div className="mission-heading">
          <b>{mision.nombre}</b>
          <button
            type="button"
            className="chip mission-track"
            aria-pressed={tracked}
            onClick={() => void seguir(mision.identificador)}
          >
            {tracked ? 'Siguiendo' : 'Seguir'}
          </button>
        </div>
        <small>{mision.descripcion}</small>
        <div className="bar2">
          <i style={{ width: `${(v / mision.meta) * 100}%` }} />
        </div>
        <small>
          {v}/{mision.meta} · Recompensa: {textoRecompensa(mision.recompensa)}
        </small>
        {ready ? (
          <button
            type="button"
            className="chip mission-claim"
            onClick={() => void reclamar(mision.identificador)}
          >
            Lista · Reclamar
          </button>
        ) : (
          <small className="mission-status">En progreso</small>
        )}
      </div>
    )
  }

  const generales = misiones.filter(
    (m) => m.identificador.startsWith('g') && !m.reclamada,
  )
  const propias = misiones.filter(
    (m) => !m.identificador.startsWith('g') && !m.reclamada,
  )
  const reclamadas = misiones.filter((m) => m.reclamada)

  return (
    <section className="pantalla misiones" aria-label="Misiones">
      {trackerSection}

      <h1>Misiones</h1>
      <p className="q">
        Encargos agrupados por actividad. El progreso corresponde a este
        cultivador y se pierde si muere.
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
      {cargando && <p>Cargando misiones…</p>}

      {!cargando && propias.length > 0 && (
        <>
          <h2 className="sh2">Misiones de tu secta</h2>
          {agrupar(propias).map(({ grupo, items }) => (
            <details key={grupo} className="mission-group" open>
              <summary>
                <span>{grupo}</span>
                <small>
                  {items.filter((m) => m.lista).length}/{items.length} objetivos
                  listos
                </small>
              </summary>
              <div className="mission-group-list">{items.map(fila)}</div>
            </details>
          ))}
        </>
      )}

      {!cargando && generales.length > 0 && (
        <>
          <h2 className="sh2">Misiones generales</h2>
          {agrupar(generales).map(({ grupo, items }) => (
            <details key={grupo} className="mission-group" open>
              <summary>
                <span>{grupo}</span>
                <small>
                  {items.filter((m) => m.lista).length}/{items.length} objetivos
                  listos
                </small>
              </summary>
              <div className="mission-group-list">{items.map(fila)}</div>
            </details>
          ))}
        </>
      )}

      {!cargando && reclamadas.length > 0 && (
        <details className="mission-claimed-fold">
          <summary>
            <span>Reclamadas ({reclamadas.length})</span>
            <small>plegadas para no ocupar espacio</small>
          </summary>
          <div className="mission-claimed-fold-list">
            {reclamadas.map((mision) => (
              <div key={mision.identificador} className="opt mq">
                <b>
                  <span aria-hidden="true">✓ </span>
                  {mision.nombre}
                </b>
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  )
}
