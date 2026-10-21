/** Taller de alquimia: recetario, forja de cartas y fusión/desmantelado.

Puerto del tab `alq` del monolito (`alq()`/`asec`/`cfmAct` en
`js/01-datos.js` y `js/12-v47-init.js`). La fusión y el desmantelado
piden confirmación, como el diálogo `cfOpen` del original; el texto de
confirmación es el del monolito.
*/

import { useEffect, useState, type ReactNode } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type {
  CartaResumen,
  CatalogoAlquimia,
  Materiales,
  ResultadoAlquimia,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  onSnapshot: (snapshot: SnapshotPartida) => void
}

const MATERIAL_NOMBRE: Record<keyof Materiales, string> = {
  h: 'hierbas',
  n: 'núcleos',
  p: 'polvo de jade',
}

const PISTA_DEFECTO =
  'Solo los alquimistas errantes la conocen. Pueden emboscarte tras un combate.'

/** Confirmación en vuelo, como el `CFM` del monolito. */
interface Confirmacion {
  encabezado: string
  titulo: string
  texto: string
  aviso: string
  textoBoton: string
  ejecutar: () => Promise<void>
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** Icono de píldora (glifo del monolito): esfera CSS o talismán 符. */
function IconoPildora({ icono }: { icono: string }) {
  if (icono === 'tal') {
    return (
      <span className="tali" aria-hidden="true">
        <i>符</i>
      </span>
    )
  }
  return <span className={`pill ${icono}`} aria-hidden="true" />
}

export default function Alquimia({ slot, snapshot, onSnapshot }: Props) {
  const [catalogo, setCatalogo] = useState<CatalogoAlquimia | null>(null)
  const [cartaDeId, setCartaDeId] = useState<Record<string, CartaResumen>>({})
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [confirmacion, setConfirmacion] = useState<Confirmacion | null>(null)
  const [abiertas, setAbiertas] = useState<Record<string, boolean>>({
    rec: true,
    forja: false,
    fusion: false,
  })

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [datos, cartas] = await Promise.all([
          api.obtenerAlquimia(),
          api.listarCartas(),
        ])
        if (!vigente) return
        setCatalogo(datos)
        setCartaDeId(
          Object.fromEntries(cartas.map((carta) => [carta.identificador, carta])),
        )
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  useEffect(() => {
    if (confirmacion === null) return
    const alPulsarEscape = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') setConfirmacion(null)
    }
    window.addEventListener('keydown', alPulsarEscape)
    return () => window.removeEventListener('keydown', alPulsarEscape)
  }, [confirmacion])

  const alternar = (clave: string) =>
    setAbiertas((previas) => ({ ...previas, [clave]: !previas[clave] }))

  /** Sección colapsable, como el `asec` del monolito. */
  const seccion = (clave: string, titulo: string, contenido: ReactNode) => {
    const abierta = abiertas[clave]
    return (
      <div className={`asec${abierta ? ' open' : ''}`}>
        <h2 className="asec-h">
          <button
            type="button"
            aria-expanded={abierta}
            onClick={() => alternar(clave)}
          >
            {abierta ? '▾' : '▸'} {titulo}
          </button>
        </h2>
        {abierta && contenido}
      </div>
    )
  }

  const puedePagar = (coste: Partial<Materiales>): boolean =>
    Object.entries(coste).every(
      ([material, cantidad]) =>
        (snapshot.mat[material as keyof Materiales] ?? 0) >= (cantidad ?? 0),
    )

  const textoCoste = (coste: Partial<Materiales>): string =>
    Object.entries(coste)
      .map(([material, cantidad]) =>
        `${cantidad} ${MATERIAL_NOMBRE[material as keyof Materiales]}`,
      )
      .join(', ')

  const ejecutar = async (llamada: Promise<ResultadoAlquimia>) => {
    try {
      const resultado = await llamada
      setMensaje(resultado.mensaje)
      setError(null)
      onSnapshot(resultado.snapshot)
    } catch (errorDeLlamada) {
      setMensaje('')
      setError(mensajeDe(errorDeLlamada))
    }
  }

  const fusionar = (identificador: string) => {
    const carta = cartaDeId[identificador]
    if (!carta) return
    const rareza = carta.rareza
    const colorDeRareza = (catalogo?.forja ?? []).find(
      (opcion) => opcion.rareza === rareza + 1,
    )
    void ejecutarDeConfirmacion(async () => {
      await ejecutar(api.fusionarCarta(slot, identificador))
    }, {
      encabezado: 'Fusión',
      titulo: `Fusionar «${carta.nombre}»`,
      texto:
        `Se consumirán 3 copias para obtener una carta aleatoria de rareza ` +
        `${colorDeRareza?.nombre ?? rareza + 1}. No se puede deshacer.`,
      textoBoton: 'Fusionar',
    })
  }

  const desmantelar = (identificador: string) => {
    const carta = cartaDeId[identificador]
    if (!carta) return
    void ejecutarDeConfirmacion(async () => {
      await ejecutar(api.desmantelarCarta(slot, identificador))
    }, {
      encabezado: 'Desmantelar',
      titulo: `Desmantelar «${carta.nombre}»`,
      texto:
        `Se consumirá 1 copia y recibirás ${1 + carta.rareza} de polvo de jade. ` +
        `No se puede deshacer.`,
      textoBoton: 'Desmantelar',
    })
  }

  const ejecutarDeConfirmacion = (
    accion: () => Promise<void>,
    resto: Omit<Confirmacion, 'ejecutar' | 'aviso'> & { aviso?: string },
  ) => {
    setConfirmacion({
      aviso: '',
      ...resto,
      ejecutar: accion,
    })
  }

  const propias = Object.entries(snapshot.col).filter(([, n]) => n > 0)
  const aprendidas = catalogo
    ? catalogo.pildoras.filter((pildora) => snapshot.rec[pildora.identificador])
        .length
    : 0
  const colorDeRareza = (rareza: number): string | undefined =>
    catalogo?.forja.find((opcion) => opcion.rareza === rareza)?.color

  const recetario = catalogo ? (
    <div className="grid">
      {catalogo.pildoras.map((pildora) =>
        snapshot.rec[pildora.identificador] ? (
          <button
            key={pildora.identificador}
            type="button"
            className="opt"
            disabled={!puedePagar(pildora.coste)}
            onClick={() =>
              void ejecutar(api.elaborarPildora(slot, pildora.identificador))
            }
          >
            <IconoPildora icono={pildora.icono} />
            <b>{pildora.nombre}</b> (tienes {snapshot.pil[pildora.identificador] ?? 0})
            <small>
              {pildora.efecto}. Cuesta {textoCoste(pildora.coste)}.
            </small>
          </button>
        ) : (
          <div key={pildora.identificador} className="opt lockr">
            <b>🔒 Receta secreta</b>
            <small>
              Pista: «{PISTA_DEFECTO}» También puede revelarla un alquimista
              errante tras un combate.
            </small>
          </div>
        ),
      )}
    </div>
  ) : (
    <p className="aviso">Cargando recetario…</p>
  )

  const forja = catalogo ? (
    <div className="grid">
      {catalogo.forja.map((opcion) => (
        <button
          key={opcion.rareza}
          type="button"
          className="opt"
          disabled={!puedePagar(opcion.coste)}
          onClick={() =>
            void ejecutar(api.forjarCarta(slot, opcion.rareza))
          }
        >
          <b style={{ color: opcion.color }}>Carta {opcion.nombre}</b>
          <small>
            Aleatoria de esa rareza. Cuesta {textoCoste(opcion.coste)}.
          </small>
        </button>
      ))}
    </div>
  ) : (
    <p className="aviso">Cargando forja…</p>
  )

  return (
    <section className="pantalla taller-alq" aria-label="Taller de alquimia">
      <header className="cabecera-taller">
        <h1>Taller de alquimia</h1>
        <p className="q">
          Vence enemigos para reunir materiales. Elabora píldoras, forja
          cartas o refina las que ya tienes.
        </p>
        <div className="st">
          <span>🌿 {snapshot.mat.h} hierbas</span>
          <span>◈ {snapshot.mat.n} núcleos</span>
          <span>✦ {snapshot.mat.p} polvo de jade</span>
          <span>💎 {snapshot.stn} piedras</span>
        </div>
        {mensaje && <p className="hint">{mensaje}</p>}
      </header>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {seccion(
        'rec',
        `Recetario secreto (${aprendidas}/${catalogo?.pildoras.length ?? 0}). ` +
          'Las de inicio se equipan antes del combate; las de combate (⚡) ' +
          'van a la bolsa y se usan durante la partida (máx. 2 usos)',
        recetario,
      )}

      {seccion('forja', 'Forja de cartas', forja)}

      {seccion(
        'fusion',
        'Fusión y refinado',
        <>
          <p className="q">
            Fusiona 3 copias de una carta para obtener una de la rareza
            siguiente, o desmantela una copia para recuperar polvo de jade.
          </p>
          {propias.length ? (
            <div className="fila-cartas">
              {propias.map(([identificador, n]) => {
                const carta = cartaDeId[identificador]
                const nombre = carta?.nombre ?? identificador
                const rareza = carta?.rareza ?? 0
                const color = colorDeRareza(rareza)
                return (
                  <div key={identificador} className="mini-carta">
                    <small className="color-rareza" style={{ color }}>
                      {nombre}
                    </small>
                    <small className="copias">×{n}</small>
                    <div className="acciones-cartas">
                      {n >= 3 && rareza < 5 && (
                        <button
                          type="button"
                          className="chip"
                          onClick={() => fusionar(identificador)}
                        >
                          Fusionar x3
                        </button>
                      )}
                      <button
                        type="button"
                        className="chip"
                        onClick={() => desmantelar(identificador)}
                      >
                        Desmantelar
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p>
              Aún no tienes cartas obtenidas. Gana combates para conseguirlas.
            </p>
          )}
        </>,
      )}

      {confirmacion && (
        <div
          className="capa-oscuro"
          onClick={() => setConfirmacion(null)}
        >
          <div
            className="carta-modal"
            role="dialog"
            aria-modal="true"
            aria-label={confirmacion.encabezado}
            onClick={(evento) => evento.stopPropagation()}
          >
            <h3>{confirmacion.titulo}</h3>
            <p>{confirmacion.texto}</p>
            {confirmacion.aviso && (
              <p className="aviso-peligro">{confirmacion.aviso}</p>
            )}
            <div className="fila-modal">
              <button
                type="button"
                className="boton peligro"
                autoFocus
                onClick={() => {
                  const { ejecutar: accion } = confirmacion
                  setConfirmacion(null)
                  void accion()
                }}
              >
                {confirmacion.textoBoton}
              </button>
              <button
                type="button"
                className="boton fantasma"
                onClick={() => setConfirmacion(null)}
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
