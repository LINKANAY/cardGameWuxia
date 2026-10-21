/** Splash: comprobación del backend + prologo, con opción de reintentar. */

import type { EstadoServidor, Narrativa } from '../api/tipos'

interface Props {
  servidor: EstadoServidor | null
  narrativa: Narrativa | null
  cargando: boolean
  error: string | null
  onReintentar: () => void
  onEntrar: () => void
}

export default function Splash({
  servidor,
  narrativa,
  cargando,
  error,
  onReintentar,
  onEntrar,
}: Props) {
  return (
    <section className="pantalla splash" aria-label="Pantalla de inicio">
      <div className="sigilo" aria-hidden="true">
        <svg viewBox="0 0 74 74" width="74" height="74" role="presentation">
          <circle cx="37" cy="37" r="30" fill="none" stroke="#e3bf6a" strokeWidth="2" />
          <circle
            cx="37"
            cy="37"
            r="23"
            fill="none"
            stroke="rgba(123, 224, 184, 0.65)"
            strokeWidth="1"
          />
          <path
            d="M37 9 L47 37 L37 65 L27 37 Z"
            fill="none"
            stroke="#e3bf6a"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <circle cx="37" cy="37" r="4.5" fill="#7be0b8" />
        </svg>
      </div>

      <h1>Sendero del Inmortal</h1>

      {cargando && <p className="aviso">Conectando con el backend…</p>}

      {!cargando && error && (
        <div className="banner-error" role="alert">
          <p>
            <strong>Sin conexión con el backend.</strong> {error}
          </p>
          <button type="button" className="boton" onClick={onReintentar}>
            Reintentar
          </button>
        </div>
      )}

      {!cargando && !error && servidor && (
        <>
          <p className="estado-servidor">
          Backend v{servidor.version} · activo hace{' '}
          {Math.round(servidor.uptime)} s
          </p>
          {narrativa && <p className="prologo">{narrativa.prologo}</p>}
          <button type="button" className="boton principal" onClick={onEntrar}>
            ▶ Jugar
          </button>
        </>
      )}
    </section>
  )
}
