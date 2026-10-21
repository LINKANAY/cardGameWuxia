/** Jardín Medicinal: siembras con tiempos, riego con piedras y cosecha.

Módulo nuevo (no existe en el monolito; ver `python/app/routers/jardin.py`).
La cuadrícula crece 4→6→9→12 casillas, cada especie tarda según su
rareza y cada piedra espiritual quita un 5 % del tiempo restante. Las
copias de formación equipadas descuentan el crecimiento sin consumirse.

El reloj de crecimiento es el del **servidor** (`ahora` epoch ms): aquí
sólo se descuenta localmente lo transcurrido desde la última respuesta
para que el contador baile, y tras cada acción (o error) se vuelve a
fijar en lo que diga el backend. El coste de riego en pantalla es el
mismo `ceil(log(umbral/restante)/log(0.95))` que valida el servicio.
*/

import { useCallback, useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type {
  CasillaJardin,
  CatalogoJardin,
  EstadoJardin,
  Materiales,
  PlantaJardinResumen,
  ResultadoJardin,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  slot: string
  onSnapshot: (snapshot: SnapshotPartida) => void
}

/** `CFG.UMBRAL_LISTO_MS` del backend: por debajo, la planta está lista. */
const UMBRAL_LISTO_MS = 1000

/** `1 − CFG.REDUCCION_PIEDRA`: cada piedra deja el 95 % del resto. */
const FACTOR_PIEDRA = 0.95

const MATERIAL_NOMBRE: Record<keyof Materiales, string> = {
  h: 'hierbas',
  n: 'núcleos',
  p: 'polvo de jade',
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** Piedras que dejarían la planta lista (espejo de `coste_max_piedras`). */
function costeDe(restante: number): number {
  if (restante <= UMBRAL_LISTO_MS) return 0
  return Math.max(
    1,
    Math.ceil(Math.log(UMBRAL_LISTO_MS / restante) / Math.log(FACTOR_PIEDRA)),
  )
}

/** Texto compacto de un recuento de milisegundos (1 h 2 min, 34 s…). */
function formatearTiempo(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const minutos = Math.floor(total / 60)
  const horas = Math.floor(minutos / 60)
  if (horas > 0) return `${horas} h ${minutos % 60} min`
  if (minutos > 0) return `${minutos} min ${total % 60} s`
  return `${total} s`
}

export default function Jardin({ slot, onSnapshot }: Props) {
  const [catalogo, setCatalogo] = useState<CatalogoJardin | null>(null)
  const [estado, setEstado] = useState<EstadoJardin | null>(null)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [sembrando, setSembrando] = useState<number | null>(null)
  const [formacionesAbiertas, setFormacionesAbiertas] = useState(false)
  const [recibido, setRecibido] = useState(() => Date.now())
  const [, hacerTic] = useState(0)

  /** Fija el estado del servidor y el instante local de referencia. */
  const fijar = useCallback((nuevo: EstadoJardin) => {
    setEstado(nuevo)
    setRecibido(Date.now())
  }, [])

  const recargar = useCallback(async () => {
    try {
      fijar(await api.jardinEstado(slot))
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    }
  }, [slot, fijar])

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [datos, estadoInicial] = await Promise.all([
          api.jardinCatalogo(),
          api.jardinEstado(slot),
        ])
        if (!vigente) return
        setCatalogo(datos)
        fijar(estadoInicial)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [slot, fijar])

  // Tic local de 1 s sólo para el recuento (el reloj manda el servidor).
  useEffect(() => {
    const id = window.setInterval(() => hacerTic((t) => t + 1), 1000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    if (sembrando === null && !formacionesAbiertas) return
    const alPulsarEscape = (evento: KeyboardEvent) => {
      if (evento.key !== 'Escape') return
      setSembrando(null)
      setFormacionesAbiertas(false)
    }
    window.addEventListener('keydown', alPulsarEscape)
    return () => window.removeEventListener('keydown', alPulsarEscape)
  }, [sembrando, formacionesAbiertas])

  if (!catalogo || !estado) {
    return (
      <section className="pantalla jardin" aria-label="Jardín Medicinal">
        <header className="cabecera-taller">
          <h1>Jardín Medicinal</h1>
        </header>
        {error ? (
          <div className="banner-error" role="alert">
            {error}
          </div>
        ) : (
          <p className="aviso">Cargando jardín…</p>
        )}
      </section>
    )
  }

  /** Tiempo transcurrido localmente desde la última respuesta. */
  const transcurrido = Math.max(0, Date.now() - recibido)

  const restanteDe = (casilla: CasillaJardin): number =>
    Math.max(0, casilla.restante_ms - transcurrido)

  const fichaDe = (identificador: string): PlantaJardinResumen | undefined =>
    catalogo.hierbas.find((planta) => planta.identificador === identificador)

  const nombreFormacion = (identificador: string): string =>
    catalogo.formaciones.find((f) => f.identificador === identificador)
      ?.nombre ?? identificador

  /** Aplica una mutación: estado nuevo, snapshot del shell y mensaje. */
  async function ejecutar<T extends ResultadoJardin>(
    llamada: Promise<T>,
    redactar: (respuesta: T) => string,
  ): Promise<void> {
    try {
      const respuesta = await llamada
      fijar(respuesta)
      setMensaje(redactar(respuesta))
      setError(null)
      onSnapshot(respuesta.snapshot)
    } catch (errorDeLlamada) {
      setMensaje('')
      setError(mensajeDe(errorDeLlamada))
      // El reloj local pudo desviarse: se relee lo que diga el servidor.
      void recargar()
    }
  }

  const sembrar = (indice: number, planta: string) => {
    setSembrando(null)
    const nombre = fichaDe(planta)?.nombre ?? planta
    void ejecutar(api.jardinSembrar(slot, indice, planta), () =>
      `Sembraste ${nombre} en la casilla ${indice + 1}.`,
    )
  }

  const acelerar = (indice: number, piedras: number) =>
    void ejecutar(api.jardinAcelerar(slot, indice, piedras), (respuesta) =>
      respuesta.resultado.restante_ms <= UMBRAL_LISTO_MS
        ? 'Planta lista para cosechar.'
        : `Riego: quedan ${formatearTiempo(respuesta.resultado.restante_ms)}.`,
    )

  const cosechar = (indice: number) =>
    void ejecutar(api.jardinCosechar(slot, indice), (respuesta) => {
      const nombre = fichaDe(respuesta.resultado.planta)?.nombre
        ?? respuesta.resultado.planta
      return `Cosechaste ${respuesta.resultado.hierbas} de ${nombre} (al Horno).`
    })

  const mejorar = () =>
    void ejecutar(api.jardinMejorar(slot), (respuesta) =>
      `Cuadrícula ampliada: ya tienes ${respuesta.resultado.casillas} casillas.`,
    )

  const equiparFormacion = (identificador: string | null) => {
    setFormacionesAbiertas(false)
    void ejecutar(api.jardinFormacion(slot, identificador), () =>
      identificador
        ? `Equipaste ${nombreFormacion(identificador)}.`
        : 'Formación de crecimiento retirada.',
    )
  }

  const puedePagar = (coste: Partial<Materiales>): boolean =>
    Object.entries(coste).every(
      ([material, cantidad]) =>
        (estado.materiales[material as keyof Materiales] ?? 0)
          >= (cantidad ?? 0),
    )

  const textoCoste = (coste: Partial<Materiales>): string =>
    Object.entries(coste)
      .map(
        ([material, cantidad]) =>
          `${cantidad} ${MATERIAL_NOMBRE[material as keyof Materiales]}`,
      )
      .join(', ')

  const totalSemillas = Object.values(estado.semillas).reduce(
    (suma, n) => suma + n,
    0,
  )
  const totalFormaciones = Object.values(estado.formaciones).reduce(
    (suma, n) => suma + n,
    0,
  )
  const mejora = estado.siguiente_mejora
  const formacionActual = estado.formacion
    ? catalogo.formaciones.find(
        (formacion) => formacion.identificador === estado.formacion,
      )
    : undefined

  return (
    <section className="pantalla jardin" aria-label="Jardín Medicinal">
      <header className="cabecera-taller">
        <h1>Jardín Medicinal</h1>
        <p className="q">
          Siembra hierbas, adelanta su crecimiento con piedras espirituales
          y recógelas para el Horno. Los boticarios errantes y las
          ascensiones de reino dejan semillas y formaciones nuevas.
        </p>
        <div className="st">
          <span>🌱 {totalSemillas} semillas</span>
          <span>💎 {estado.piedras} piedras</span>
          <span>🌿 {estado.materiales.h} hierbas</span>
          <span>◈ {estado.materiales.n} núcleos</span>
          <span>✦ {estado.materiales.p} polvo de jade</span>
        </div>
        {mensaje && <p className="hint">{mensaje}</p>}
      </header>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {totalSemillas === 0 && (
        <p className="aviso">
          No te quedan semillas: los boticarios errantes sueltan algunas
          tras un combate, y cada ascensión de reino regala una nueva.
        </p>
      )}

      <div
        className="jardin-cuadricula"
        role="list"
        aria-label={`Cuadrícula con ${estado.casillas.length} casillas`}
      >
        {estado.casillas.map((casilla, indice) => {
          if (!casilla) {
            return (
              <div key={indice} className="casilla vacia" role="listitem">
                <span className="jardin-glifo" aria-hidden="true">
                  ＋
                </span>
                <button
                  type="button"
                  className="chip"
                  onClick={() => setSembrando(indice)}
                >
                  Sembrar
                </button>
              </div>
            )
          }
          const ficha = fichaDe(casilla.planta)
          const restante = restanteDe(casilla)
          const listo = restante <= UMBRAL_LISTO_MS
          const progreso =
            casilla.duracion_ms > 0
              ? Math.max(0, Math.min(1, 1 - restante / casilla.duracion_ms))
              : 1
          const porcentaje = Math.round(progreso * 100)
          const coste = costeDe(restante)
          const nombre = ficha?.nombre ?? casilla.planta
          return (
            <div
              key={indice}
              className={`casilla sembrada${listo ? ' lista' : ''}`}
              role="listitem"
            >
              <span className="jardin-glifo" aria-hidden="true">
                {ficha?.glifo ?? '❋'}
              </span>
              <b>{nombre}</b>
              <div
                className="jardin-barra"
                role="progressbar"
                aria-valuenow={porcentaje}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Crecimiento de ${nombre}`}
              >
                <i style={{ width: `${porcentaje}%` }} />
              </div>
              <small className="jardin-tiempo">
                {listo
                  ? 'Listo para cosechar'
                  : `Quedan ${formatearTiempo(restante)}`}
              </small>
              <div className="jardin-acciones">
                {!listo && (
                  <button
                    type="button"
                    className="chip"
                    disabled={estado.piedras < coste}
                    title="Cada piedra quita 5 % del tiempo restante"
                    onClick={() => acelerar(indice, coste)}
                  >
                    💧 Riego ({coste}💎)
                  </button>
                )}
                <button
                  type="button"
                  className="chip"
                  disabled={!listo}
                  onClick={() => cosechar(indice)}
                >
                  Cosechar
                </button>
              </div>
            </div>
          )
        })}
      </div>

      <div className="jardin-formacion">
        <h2>Formación de crecimiento</h2>
        <p className="q">
          {formacionActual
            ? `${formacionActual.glifo} ${formacionActual.nombre} equipada: `
              + `−${Math.round(formacionActual.descuento * 100)} % de `
              + 'crecimiento en todas las casillas.'
            : 'Sin formación equipada. Las copias que consigas se guardan aquí y sólo se consumen al mejorar de rareza, no al equipar.'}
        </p>
        <button
          type="button"
          className="boton fantasma"
          onClick={() => setFormacionesAbiertas(true)}
        >
          Elegir formación ({totalFormaciones} poseídas)
        </button>
      </div>

      <div className="jardin-mejora">
        <h2>
          {mejora
            ? `Ampliar cuadrícula: ${mejora.casillas} casillas`
            : 'Cuadrícula al máximo'}
        </h2>
        {mejora ? (
          <>
            <p className="q">
              Reino {mejora.reino_min} · Cuesta {textoCoste(mejora.coste)}
              {estado.reino < mejora.reino_min
                ? ` (llevas reino ${estado.reino})`
                : ''}
            </p>
            <button
              type="button"
              className="boton principal"
              disabled={
                estado.reino < mejora.reino_min || !puedePagar(mejora.coste)
              }
              onClick={mejorar}
            >
              Ampliar
            </button>
          </>
        ) : (
          <p className="q">
            12 casillas: no hay más sitio para crecer en este reino.
          </p>
        )}
      </div>

      {sembrando !== null && (
        <div className="capa-oscuro" onClick={() => setSembrando(null)}>
          <div
            className="carta-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Sembrar"
            onClick={(evento) => evento.stopPropagation()}
          >
            <h3>Sembrar en la casilla {sembrando + 1}</h3>
            <p>Elige la semilla: se gasta una y empieza a correr el tiempo.</p>
            <div className="grid">
              {catalogo.hierbas.map((planta) => {
                const stock = estado.semillas[planta.identificador] ?? 0
                const reinoBajo = estado.reino < planta.reino_min
                return (
                  <button
                    key={planta.identificador}
                    type="button"
                    className="opt"
                    disabled={reinoBajo || stock < 1}
                    onClick={() => sembrar(sembrando, planta.identificador)}
                  >
                    <b>
                      {planta.glifo} {planta.nombre}
                    </b>
                    <small>
                      {formatearTiempo(planta.duracion_ms)} · +
                      {planta.rendimiento} hierba(s) · tienes {stock}
                      {reinoBajo && ` · Requiere reino ${planta.reino_min}`}
                    </small>
                  </button>
                )
              })}
            </div>
            <div className="fila-modal">
              <button
                type="button"
                className="boton fantasma"
                onClick={() => setSembrando(null)}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {formacionesAbiertas && (
        <div
          className="capa-oscuro"
          onClick={() => setFormacionesAbiertas(false)}
        >
          <div
            className="carta-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Formaciones de crecimiento"
            onClick={(evento) => evento.stopPropagation()}
          >
            <h3>Formaciones de crecimiento</h3>
            <p>
              Sólo se equipa una a la vez y equiparla no consume copia: se
              aplica a todas las casillas mientras esté puesta.
            </p>
            <div className="grid">
              {catalogo.formaciones.map((formacion) => {
                const copias =
                  estado.formaciones[formacion.identificador] ?? 0
                const equipada = estado.formacion === formacion.identificador
                return (
                  <button
                    key={formacion.identificador}
                    type="button"
                    className="opt"
                    disabled={copias < 1 || equipada}
                    onClick={() => equiparFormacion(formacion.identificador)}
                  >
                    <b>
                      {formacion.glifo} {formacion.nombre}
                      {equipada ? ' · equipada' : ''}
                    </b>
                    <small>
                      −{Math.round(formacion.descuento * 100)} % de
                      crecimiento · tienes {copias} copia(s).{' '}
                      {formacion.descripcion}
                    </small>
                  </button>
                )
              })}
            </div>
            <div className="fila-modal">
              {estado.formacion && (
                <button
                  type="button"
                  className="boton peligro"
                  onClick={() => equiparFormacion(null)}
                >
                  Quitar formación
                </button>
              )}
              <button
                type="button"
                className="boton fantasma"
                onClick={() => setFormacionesAbiertas(false)}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
