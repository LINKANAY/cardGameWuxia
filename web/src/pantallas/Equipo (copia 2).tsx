/** Equipo: bestias de ayuda, huecos y Herrería (tab `eqp`).

Port de `eqpUI` (js/06-contenido.js:75-80) y de `slotH`/`eqPanel`
(js/08-efectos.js:105-115). Forjar, equipar/retirar y domar bestias van
al backend (`equipo/forjar|equipar|bestia`); el estado (poseídas, puestas
y usos) sale del snapshot (`gr`/`eq`/`du`/`be`).
*/

import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type {
  BestiaResumen,
  CatalogoEquipo,
  Materiales,
  PiezaEquipoResumen,
  ResultadoEquipo,
  SnapshotPartida,
} from '../api/tipos'
import { arteCarta } from '../arte/artCarta'
import { artePieza } from '../arte/pieza'
import { figuraSecta } from '../arte/figura'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  onSnapshot: (snapshot: SnapshotPartida) => void
}

/** Iconos por hueco (`SLI` de js/08-efectos.js:103, viewBox 24). */
const SLI: Record<string, string> = {
  cabeza: '<path d="M5 20V12a7 7 0 0 1 14 0v8Z"/>',
  cuerpo: '<path d="M6 4h12l3 5-3 2v9H6v-9L3 9Z"/>',
  guantes:
    '<path d="M7 21V11L5 8l2-1 2 3V4h2v7V3h2v8V5h2v8V8h2v8l-3 5Z"/>',
  botas: '<path d="M8 3h6v9l6 3v5H8Z"/>',
  reliquia: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/>',
  artefacto: '<path d="M12 2l3 7 7 1-5 5 1 7-6-4-6 4 1-7-5-5 7-1Z"/>',
}

/** Nombres de material (`MN` de js/01-datos.js:185). */
const MN: Record<string, string> = {
  h: 'hierbas',
  n: 'núcleos',
  p: 'polvo de jade',
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

export default function Equipo({ slot, snapshot, onSnapshot }: Props) {
  const [catalogo, setCatalogo] = useState<CatalogoEquipo | null>(null)
  const [bestias, setBestias] = useState<BestiaResumen[]>([])
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)

  const recargar = useCallback(async () => {
    try {
      const [equipo, listaBestias] = await Promise.all([
        api.equipoCatalogo(),
        api.listarBestias(),
      ])
      setCatalogo(equipo)
      setBestias(listaBestias)
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void recargar()
  }, [recargar])

  const ejecutar = useCallback(
    async (llamada: Promise<ResultadoEquipo>) => {
      setError(null)
      setAviso(null)
      try {
        const resultado = await llamada
        setAviso(resultado.mensaje)
        onSnapshot(resultado.snapshot)
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      }
    },
    [onSnapshot],
  )

  const poseida = (id: string): boolean => Boolean(snapshot.gr[id])

  const equipada = (pieza: PiezaEquipoResumen): boolean =>
    snapshot.eq[pieza.slot] === pieza.identificador

  const desbloqueada = (pieza: PiezaEquipoResumen): boolean =>
    pieza.desbloqueo == null || snapshot.wins.includes(pieza.desbloqueo)

  const puedePagar = (coste: Partial<Materiales>): boolean =>
    (['h', 'n', 'p'] as const).every(
      (material) => (coste[material] ?? 0) <= snapshot.mat[material],
    )

  /** Texto del coste (`cs()` de js/01-datos.js:189), en orden del dict. */
  const textoCoste = (coste: Partial<Materiales>): string =>
    Object.entries(coste)
      .map(([material, cantidad]) => `${cantidad} ${MN[material] ?? material}`)
      .join(', ')

  /** Bonos del equipo puesto y poseído, con tope +4 (`gearStat`). */
  const gearStat = (): { a: number; q: number; ra: number; rq: number } => {
    let ra = 0
    let rq = 0
    for (const pieza of catalogo?.piezas ?? []) {
      if (equipada(pieza) && poseida(pieza.identificador)) {
        ra += pieza.ataque
        rq += pieza.qi
      }
    }
    return { a: Math.min(4, ra), q: Math.min(4, rq), ra, rq }
  }

  /** Pieza puesta en un hueco (si existe y está poseída). */
  const delHueco = (clave: string): PiezaEquipoResumen | undefined => {
    const id = snapshot.eq[clave]
    if (typeof id !== 'string') return undefined
    return catalogo?.piezas.find((p) => p.identificador === id)
  }

  /** Hueco del panel (`slotH` de js/08-efectos.js:105-110). */
  const hueco = (
    h: { clave: string; nombre: string },
    indice: number,
  ): ReactNode => {
    const pieza = delHueco(h.clave)
    if (!pieza || !poseida(pieza.identificador)) {
      const n = (catalogo?.piezas ?? []).filter(
        (p) => p.slot === h.clave && poseida(p.identificador),
      ).length
      return (
        <div key={`${h.clave}-${indice}`} className="eqs-sl empty" title={`${h.nombre}: vacío`}>
          <i className="sln">{h.nombre}</i>
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
            dangerouslySetInnerHTML={{ __html: SLI[h.clave] ?? '' }}
          />
          <b>Vacío</b>
          <span className="eqst">
            <em>
              {n ? `Tienes ${n} para este espacio` : 'Aún no has forjado ninguno'}
            </em>
          </span>
        </div>
      )
    }
    const usos = snapshot.du[pieza.identificador] ?? 0
    const stats = [
      pieza.ataque ? `Ataque +${pieza.ataque}` : '',
      pieza.qi ? `Qi +${pieza.qi}` : '',
      pieza.revive ? `Revive con ${pieza.revive} de vida` : '',
      pieza.revive ? `${usos} usos` : '',
    ].filter(Boolean)
    const titulo = `${pieza.nombre} · ${h.nombre} · ${
      stats.join(', ') || 'sin bonificaciones numéricas'
    } · Pulsa para retirar`
    return (
      <button
        key={`${h.clave}-${indice}`}
        type="button"
        className="eqs-sl full"
        title={titulo}
        onClick={() => void ejecutar(api.equiparPieza(slot, pieza.identificador))}
      >
        <i className="sln">{h.nombre}</i>
        <span
          className="eqa"
          aria-hidden="true"
          dangerouslySetInnerHTML={{ __html: artePieza(pieza.identificador) }}
        />
        <b>{pieza.nombre}</b>
        <span className="eqst">
          {stats.length ? (
            stats.map((s) => <em key={s}>{s}</em>)
          ) : (
            <em>Sin bonificación</em>
          )}
        </span>
      </button>
    )
  }

  const st = gearStat()
  const qb = Math.min(12, 6 + snapshot.realm)
  const izquierda = catalogo?.huecos.slice(0, 3) ?? []
  const derecha = catalogo?.huecos.slice(3) ?? []

  return (
    <section className="pantalla equipo" aria-label="Equipo">
      <section className="cultivator-profile" aria-label="Perfil del cultivador">
        <div
          className="pf"
          aria-hidden="true"
          dangerouslySetInnerHTML={{
            __html: figuraSecta(
              snapshot.sect,
              false,
              snapshot.of[snapshot.sect] ?? 0,
            ),
          }}
        />
        <div className="pi">
          <h2>Equipo del cultivador</h2>
          <p className="q">
            Las armaduras aumentan el Ataque y el Qi (máx. +4 cada uno) y se
            forjan con materiales, como las píldoras.
          </p>
        </div>
      </section>

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
      {cargando && <p>Cargando equipo…</p>}

      {!cargando && (
        <>
          <h2>Bestia de ayuda (una por nivel, se gana al vencer al jefe)</h2>
          <div className="grid">
            {bestias.map((bestia) => {
              const ok = snapshot.wins.includes(bestia.indice_nivel * 6 + 5)
              const actual = snapshot.be === bestia.identificador
              return (
                <button
                  key={bestia.identificador}
                  type="button"
                  className={`opt tj${actual ? ' eqd' : ''}`}
                  disabled={!ok}
                  onClick={() =>
                    void ejecutar(api.equiparBestia(slot, bestia.identificador))
                  }
                >
                  <span
                    className="eq-arte"
                    aria-hidden="true"
                    dangerouslySetInnerHTML={{
                      __html: arteCarta(bestia.identificador),
                    }}
                  />
                  <b>{bestia.nombre}</b>
                  {ok ? (
                    <>
                      <span className="gst">
                        <em>Ataque {bestia.ataque}</em>
                        <em>Vida {bestia.vida}</em>
                      </span>
                      {actual ? null : <span className="eqb">Equipar</span>}
                    </>
                  ) : (
                    <small>
                      Vence al jefe del Nivel {bestia.indice_nivel + 1} para
                      domarla.
                    </small>
                  )}
                </button>
              )
            })}
          </div>

          <h2>Espacios de equipo</h2>
          <div className="eqs">
            <div className="col">
              {izquierda.map((h, i) => hueco(h, i))}
            </div>
            <div
              className="mid"
              aria-hidden="true"
              dangerouslySetInnerHTML={{
                __html: figuraSecta(
                  snapshot.sect,
                  false,
                  snapshot.of[snapshot.sect] ?? 0,
                ),
              }}
            />
            <div className="col">{derecha.map((h, i) => hueco(h, i))}</div>
          </div>
          <div className="eqt">
            <span>
              Ataque base 0 · no atacas a mano: el daño lo hacen tus cartas y
              criaturas. Bono del equipo <b>+{st.a}</b>
              {st.ra > st.a
                ? ` (tope +4; el equipo suma ${st.ra})`
                : ''}
            </span>
            <span>
              Qi máximo en combate: base {qb} · equipo <b>+{st.q}</b> ={' '}
              {qb + st.q}
              {st.rq > st.q ? ` (tope +4; el equipo suma ${st.rq})` : ''}
            </span>
          </div>
          <p className="eq-nota">
            Pulsa un objeto equipado para retirarlo; equipa otro de la Herrería
            para sustituirlo.
          </p>

          <h2>Herrería</h2>
          <div className="grid">
            {(catalogo?.piezas ?? []).map((pieza) => {
              const have = poseida(pieza.identificador)
              const unl = desbloqueada(pieza)
              const on = equipada(pieza)
              const can = unl && puedePagar(pieza.coste)
              const usos = have
                ? (snapshot.du[pieza.identificador] ?? 0)
                : (pieza.usos ?? 0)
              return (
                <button
                  key={pieza.identificador}
                  type="button"
                  className={`opt tj${on ? ' eqd' : ''}`}
                  disabled={!have && !can}
                  onClick={() =>
                    void ejecutar(
                      have
                        ? api.equiparPieza(slot, pieza.identificador)
                        : api.forjarEquipo(slot, pieza.identificador),
                    )
                  }
                >
                  <span
                    className="eq-arte"
                    aria-hidden="true"
                    dangerouslySetInnerHTML={{
                      __html: artePieza(pieza.identificador),
                    }}
                  />
                  <b>{pieza.nombre}</b>
                  <small className="gsl">
                    {pieza.slot[0].toUpperCase() + pieza.slot.slice(1)}
                  </small>
                  <span className="gst">
                    {pieza.ataque ? <em>Ataque +{pieza.ataque}</em> : null}
                    {pieza.qi ? <em>Qi +{pieza.qi}</em> : null}
                    {pieza.revive ? (
                      <em>Revive con {pieza.revive} de vida</em>
                    ) : null}
                    {pieza.revive ? <em>{usos} usos</em> : null}
                  </span>
                  {have ? (
                    on ? null : <span className="eqb">Equipar</span>
                  ) : unl ? (
                    <small>Forjar: {textoCoste(pieza.coste)}</small>
                  ) : (
                    <small>
                      Plano bloqueado: vence al jefe del Nivel{' '}
                      {Math.floor((pieza.desbloqueo ?? 0) / 6) + 1}
                    </small>
                  )}
                </button>
              )
            })}
          </div>
        </>
      )}
    </section>
  )
}
