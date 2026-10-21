/** Ceremonia de Adivinación Ancestral (gacha).

Puerto del modal `.gachab` del monolito (`GachaSystem.draw` en
`js/14-gacha.js`). Pestañas por pool, contador de piedad, tickets y
rejilla de resultados tras cada tirada.
*/

import { useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type {
  CatalogoGacha,
  PoolGacha,
  RarezaGacha,
  RecompensaGacha,
  ResultadoGacha,
  SnapshotPartida,
} from '../api/tipos'

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

export default function Gacha({ slot, snapshot, onSnapshot }: Props) {
  const [catalogo, setCatalogo] = useState<CatalogoGacha | null>(null)
  const [poolActivo, setPoolActivo] = useState('STANDARD')
  const [resultados, setResultados] = useState<RecompensaGacha[]>([])
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const datos = await api.obtenerGacha()
        if (vigente) setCatalogo(datos)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const pool: PoolGacha | undefined = catalogo?.pools.find(
    (p) => p.clave === poolActivo,
  )
  const ticket = catalogo?.tickets.find(
    (t) => t.identificador === pool?.tipo_ticket,
  )
  const tickets = snapshot.gt?.[pool?.tipo_ticket ?? ''] ?? 0
  const piedad = pool
    ? (snapshot.gp?.[pool.piedad.clave] ?? 0)
    : 0
  const rarezaDe = (clave: string): RarezaGacha | undefined =>
    catalogo?.rarezas.find((r) => r.clave === clave)

  const tirar = async (count: 1 | 10) => {
    if (!pool || ocupado) return
    setOcupado(true)
    try {
      const resultado: ResultadoGacha = await api.tirarGacha(
        slot,
        pool.clave as 'STANDARD' | 'PREMIUM',
        count,
      )
      setMensaje(resultado.mensaje)
      setError(null)
      setResultados(resultado.resultados)
      onSnapshot(resultado.snapshot)
    } catch (errorDeLlamada) {
      setMensaje('')
      setError(mensajeDe(errorDeLlamada))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <section className="pantalla gacha" aria-label="Ceremonia de Adivinación">
      <header className="cabecera-taller">
        <h1>Ceremonia de Adivinación</h1>
        <p className="q">
          Invoca Ecos del Sendero con reliquias resonantes. Cada invocación
          consume tickets; la armonía con el Sendero (piedad) garantiza un
          Épico tras demasiados comunes.
        </p>
        <div className="st">
          {(catalogo?.tickets ?? []).map((t) => (
            <span key={t.identificador}>
              {t.icono} {t.nombre}: {snapshot.gt?.[t.identificador] ?? 0}
            </span>
          ))}
        </div>
        {mensaje && <p className="hint">{mensaje}</p>}
      </header>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      <div className="sects wsel" role="tablist" aria-label="Pools de invocación">
        {(catalogo?.pools ?? []).map((p) => (
          <button
            key={p.clave}
            type="button"
            role="tab"
            aria-selected={poolActivo === p.clave}
            className={`chip${poolActivo === p.clave ? ' on' : ''}`}
            onClick={() => {
              setPoolActivo(p.clave)
              setResultados([])
            }}
          >
            {p.nombre}
          </button>
        ))}
      </div>

      {pool ? (
        <div className="panel-gacha">
          <h2>{pool.nombre}</h2>
          <p className="q">{pool.descripcion}</p>
          <div className="st">
            <span>
              Reliquia requerida:{' '}
              <b>
                {ticket?.icono} {ticket?.nombre}
              </b>{' '}
              (Tienes: {tickets})
            </span>
            <span>
              Armonía con el Sendero (Pity):{' '}
              <b>
                {piedad} / {pool.piedad.garantizado_epico_tras}
              </b>
            </span>
          </div>
          <ul className="lista-probs" aria-label="Probabilidades del pool">
            {(Object.keys(pool.probabilidades) as Array<
              keyof PoolGacha['probabilidades']
            >).map((clave) => (
              <li key={clave}>
                <span style={{ color: rarezaDe(clave)?.color }}>
                  {rarezaDe(clave)?.nombre ?? clave}
                </span>
                <b>{pool.probabilidades[clave]}%</b>
              </li>
            ))}
          </ul>
          <div className="gacha-acciones">
            <button
              type="button"
              className="opt"
              disabled={ocupado || tickets < pool.coste_por_tirada}
              onClick={() => void tirar(1)}
            >
              🧿 Escuchar un Eco (Coste: {pool.coste_por_tirada})
            </button>
            <button
              type="button"
              className="opt"
              disabled={ocupado || tickets < pool.coste_por_tirada * 10}
              onClick={() => void tirar(10)}
            >
              🌟 Meditar en el Sendero 10x (Coste:{' '}
              {pool.coste_por_tirada * 10})
            </button>
          </div>
        </div>
      ) : (
        <p className="aviso">Cargando ceremonia…</p>
      )}

      {resultados.length > 0 && (
        <div className="resultados-gacha" role="status">
          <h2>El Sendero revela los siguientes Ecos:</h2>
          <div className="rejilla-recompensas">
            {resultados.map((recompensa, indice) => {
              const rareza = rarezaDe(recompensa.rareza)
              return (
                <div
                  key={`${recompensa.nombre}-${indice}`}
                  className="recompensa"
                  style={{
                    borderColor: rareza?.color ?? 'var(--edge)',
                  }}
                >
                  <span
                    className="rareza-gacha"
                    style={{ color: rareza?.color }}
                  >
                    {rareza?.nombre ?? recompensa.rareza}
                  </span>
                  <b>{recompensa.nombre}</b>
                  <small>{recompensa.descripcion}</small>
                </div>
              )
            })}
          </div>
          <button
            type="button"
            className="chip"
            onClick={() => setResultados([])}
          >
            Limpiar resultados
          </button>
        </div>
      )}
    </section>
  )
}
