/** Puerta: elección de secta al entrar sin secta confirmada.

Replica `gate()` de js/06-contenido.js:74: aviso de muerte permanente,
rejilla de sectas con el arte de su quinta carta base
(`art(S[k].l[4])`) y panel de confirmación «Unirme para siempre»
(`confirmS` → `schosen = sect = selS` + regalo de un Talismán de
Escape). Se muestra en la pestaña Campaña cuando `snapshot.sc` es
`null` (partida nueva o tras la muerte permanente).

La sesión de combate vive en el backend; aquí sólo se pinta y se
envía la elección (`POST …/api/game/{slot}/secta`).
*/

import { useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import { arteCarta } from '../arte/artCarta'
import { figuraSecta } from '../arte/figura'
import type { SectaResumen, SnapshotPartida } from '../api/tipos'

interface Props {
  slot: string
  sectas: SectaResumen[]
  onSnapshot: (snapshot: SnapshotPartida) => void
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** Imagen de la tarjeta de secta.

La quinta carta del mazo base (`art(S[k].l[4])` del `gate()`): las
sectas v47 también tienen mazo propio (primeras 5 cartas de `NS`),
así que todas rindan por arte de carta; si una secta viniera sin
cartas, cae a su figura (`fig()`).
*/
function arteSecta(secta: SectaResumen): string {
  const cartas = secta.cartas_iniciales ?? []
  const id = cartas[4]
  if (id) return arteCarta(id)
  return figuraSecta(secta.identificador, false, 0)
}

export default function Puerta({ slot, sectas, onSnapshot }: Props) {
  const [seleccion, setSeleccion] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const elegida = sectas.find((s) => s.identificador === seleccion) ?? null

  /** `confirmS` de js/06-contenido.js:72. */
  const confirmar = async () => {
    if (!elegida || ocupado) return
    setOcupado(true)
    setError(null)
    try {
      const partida = await api.confirmarSecta(slot, elegida.identificador)
      if (partida.snapshot) onSnapshot(partida.snapshot)
      setSeleccion(null)
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <section className="pantalla puerta" aria-label="Elige tu secta">
      <h1>Elige tu secta</h1>
      <p className="hint">Solo podrás pertenecer a una.</p>
      <p className="aviso-muerte puerta-aviso">
        ☠ Muerte permanente: si tu cultivador muere, pierdes todo. Tus
        recetas solo se pierden si eliges otra secta al renacer.
        Talismanes, píldoras y artefactos pueden salvarte.
      </p>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {elegida && (
        <section className="puerta-confirmar" aria-label="Confirmar secta">
          <span
            className="fig-heroe"
            aria-hidden="true"
            dangerouslySetInnerHTML={{
              __html: figuraSecta(elegida.identificador, false, 0),
            }}
          />
          <div>
            <h2>{elegida.nombre}</h2>
            <p className="q">{elegida.descripcion}</p>
            <p>
              ¿Unirte a esta secta? No podrás cambiar de secta después.
            </p>
            <div className="acciones-modal">
              <button
                type="button"
                className="principal"
                onClick={() => void confirmar()}
                disabled={ocupado}
              >
                {ocupado ? 'Uniéndote…' : 'Unirme para siempre'}
              </button>
              <button
                type="button"
                onClick={() => setSeleccion(null)}
                disabled={ocupado}
              >
                Cancelar
              </button>
            </div>
          </div>
        </section>
      )}

      <div className="sects">
        {sectas.map((secta) => (
          <button
            key={secta.identificador}
            type="button"
            className={`sc${seleccion === secta.identificador ? ' on' : ''}`}
            aria-pressed={seleccion === secta.identificador}
            onClick={() => setSeleccion(secta.identificador)}
          >
            <span
              className="arte-carta arte-secta"
              aria-hidden="true"
              dangerouslySetInnerHTML={{ __html: arteSecta(secta) }}
            />
            <b>{secta.nombre}</b>
            <small>{secta.descripcion}</small>
          </button>
        ))}
        {sectas.length === 0 && (
          <p className="tablero-vacio">Cargando sectas…</p>
        )}
      </div>
    </section>
  )
}
