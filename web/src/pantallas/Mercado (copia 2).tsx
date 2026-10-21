/** Mercado del Sendero: puestos de secta, General, detalle y confirmaciones.

Puerto del tab `mkt` del monolito (`mkt()`/`buy`/`buyM`/`sellM`/`buyC`
en `js/03-cartas-mercado.js` + override v47 de `js/12-v47-init.js`).
Toda compra pide confirmación (como el `cfOpen` del original); el
detalle de carta usa el modal `mkDet` vía `GET …/detalle`.
*/

import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, ErrorApi } from '../api/cliente'
import { arteCarta } from '../arte/artCarta'
import { iconoMaterial } from '../arte/iconoMaterial'
import type {
  CatalogoAlquimia,
  CatalogoMercado,
  CartaResumen,
  DetalleCarta,
  Materiales,
  PildoraResumen,
  PildoraVenta,
  ResultadoMercado,
  SectaResumen,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  sectas: SectaResumen[]
  onSnapshot: (snapshot: SnapshotPartida) => void
}

const MATERIAL_NOMBRE: Record<keyof Materiales, string> = {
  h: 'hierbas',
  n: 'núcleos',
  p: 'polvo de jade',
}

const MATERIAL_ICONO: Record<keyof Materiales, string> = {
  h: '🌿',
  n: '◈',
  p: '✦',
}

/** Clave de `ico()` del monolito para cada material. */
const MATERIAL_GLYPH: Record<keyof Materiales, string> = {
  h: 'herb',
  n: 'core',
  p: 'dust',
}

const TIPO_CARTA: Record<string, string> = {
  C: 'Criatura',
  T: 'Técnica',
  P: 'Píldora',
  F: 'Formación',
  R: 'Runa',
}

const COLOR_RAREZA = [
  '#a8b4c2',
  '#7be0b8',
  '#e3bf6a',
  '#c084fc',
  '#f0a868',
  '#ff6b6b',
]

/** Confirmación en vuelo, como el `CFM` del monolito. */
interface Confirmacion {
  encabezado: string
  titulo: string
  texto: string
  textoBoton: string
  ejecutar: () => Promise<void>
}

export function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** `Math.round` del monolito (mitad hacia arriba) para `mkcPrice`. */
function redondearJs(valor: number): number {
  return Math.floor(valor + 0.5)
}

/** Precio de vitrina de una píldora (`mkcPrice` del v47). */
function precioVitrina(pildora: PildoraResumen): number {
  const { h = 0, n = 0, p = 0 } = pildora.coste
  return Math.max(8, redondearJs((h * 6 + n * 14 + p * 8) * 1.7))
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

/** Filtro `vzOk` + secta del `ids` de `mkt()` (v47). */
function cartaEnPuesto(
  carta: CartaResumen,
  puesto: string,
  sectas: SectaResumen[],
  snapshot: SnapshotPartida,
): boolean {
  if (carta.reliquia) return false
  if (carta.rareza >= 5) return false
  if (carta.es_abismo) {
    const registro = (snapshot.qs?.['vz'] ?? {}) as Record<string, number>
    if (registro[carta.identificador] || (snapshot.col[carta.identificador] ?? 0) > 0) {
      return false
    }
  }
  const visible =
    carta.secta === null || carta.secta === 'neu' ? null : carta.secta
  if (puesto === 'neu') return visible === null
  const sectaPuesto = sectas.find((s) => s.identificador === puesto)
  const starters = sectaPuesto?.cartas_iniciales ?? []
  return visible === puesto && !starters.includes(carta.identificador)
}

export default function Mercado({
  slot,
  snapshot,
  sectas,
  onSnapshot,
}: Props) {
  const [catalogo, setCatalogo] = useState<CatalogoMercado | null>(null)
  const [alquimia, setAlquimia] = useState<CatalogoAlquimia | null>(null)
  const [cartas, setCartas] = useState<CartaResumen[]>([])
  const [puesto, setPuesto] = useState(snapshot.sc ?? snapshot.sect)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [confirmacion, setConfirmacion] = useState<Confirmacion | null>(null)
  const [detalle, setDetalle] = useState<DetalleCarta | null>(null)
  const [pildoraDetalle, setPildoraDetalle] = useState<PildoraVenta | null>(
    null,
  )

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [mercado, taller, listaCartas] = await Promise.all([
          api.obtenerMercado(),
          api.obtenerAlquimia(),
          api.listarCartas(),
        ])
        if (!vigente) return
        setCatalogo(mercado)
        setAlquimia(taller)
        setCartas(listaCartas)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  useEffect(() => {
    const alPulsarEscape = (evento: KeyboardEvent) => {
      if (evento.key !== 'Escape') return
      if (detalle) setDetalle(null)
      else if (pildoraDetalle) setPildoraDetalle(null)
      else if (confirmacion) setConfirmacion(null)
    }
    window.addEventListener('keydown', alPulsarEscape)
    return () => window.removeEventListener('keydown', alPulsarEscape)
  }, [detalle, pildoraDetalle, confirmacion])

  const esGeneral = puesto === 'neu'
  const esPropio = esGeneral || puesto === (snapshot.sc ?? snapshot.sect)
  const puestoActual = catalogo?.puestos.find(
    (p) => p.identificador === puesto,
  )
  const nombrePuesto =
    sectas.find((secta) => secta.identificador === puesto)?.nombre ?? puesto

  const cartasPuesto = useMemo(
    () =>
      cartas
        .filter((carta) =>
          cartaEnPuesto(carta, puesto, sectas, snapshot),
        )
        .sort((a, b) => a.rareza - b.rareza || a.coste_qi - b.coste_qi),
    [cartas, puesto, sectas, snapshot],
  )

  /** Vitrina: básicas del catálogo + recetas aprendidas (`mkcList`). */
  const vitrina: PildoraVenta[] = useMemo(() => {
    if (!alquimia) return []
    const basicas = new Map(
      (catalogo?.pildoras_en_venta ?? []).map((p) => [
        p.identificador,
        p.precio,
      ]),
    )
    return alquimia.pildoras
      .filter(
        (pildora) =>
          pildora.identificador !== 'inm' &&
          pildora.identificador !== 'rar' &&
          (Boolean(snapshot.rec[pildora.identificador]) ||
            basicas.has(pildora.identificador)),
      )
      .map((pildora) => {
        const tipo =
          pildora.identificador === 'tes'
            ? 'Talismán'
            : pildora.es_combate
              ? 'Píldora de combate ⚡'
              : 'Píldora de inicio'
        return {
          identificador: pildora.identificador,
          nombre: pildora.nombre,
          efecto: pildora.efecto,
          tipo,
          precio: basicas.get(pildora.identificador) ?? precioVitrina(pildora),
          icono: pildora.icono,
          es_talisman: pildora.identificador === 'tes',
          receta_aprendida: Boolean(snapshot.rec[pildora.identificador]),
        }
      })
  }, [alquimia, catalogo, snapshot.rec])

  const abrirConfirmacion = (
    resto: Omit<Confirmacion, 'ejecutar'> & { ejecutar: () => Promise<void> },
  ) => setConfirmacion(resto)

  const ejecutar = async (llamada: Promise<ResultadoMercado>) => {
    try {
      const resultado = await llamada
      setMensaje(resultado.mensaje)
      setError(null)
      onSnapshot(resultado.snapshot)
      return resultado
    } catch (errorDeLlamada) {
      setMensaje('')
      setError(mensajeDe(errorDeLlamada))
      return null
    }
  }

  const comprarCarta = (carta: CartaResumen) => {
    const copias = snapshot.col[carta.identificador] ?? 0
    const precio = precioCompraLocal(carta.rareza)
    void abrirConfirmacion({
      encabezado: 'Compra',
      titulo: `Comprar «${carta.nombre}»`,
      texto:
        `Precio: ${precio} piedras espirituales (${nombreRareza(carta.rareza)}). ` +
        `Tienes ${snapshot.stn}. Tienes ${copias}/3 copias.`,
      textoBoton: 'Comprar',
      ejecutar: async () => {
        await ejecutar(api.comprarCarta(slot, carta.identificador))
      },
    })
  }

  const comprarLote = () => {
    if (!puestoActual?.lote) return
    const lote = puestoActual.lote
    void abrirConfirmacion({
      encabezado: 'Compra',
      titulo: `Comprar ${lote.nombre}`,
      texto:
        `Recibirás ${lote.cantidad} ${MATERIAL_NOMBRE[lote.material as keyof Materiales]} ` +
        `por ${lote.costo} piedras espirituales. Tienes ${snapshot.stn}.`,
      textoBoton: 'Comprar',
      ejecutar: async () => {
        await ejecutar(api.comprarMaterial(slot, puesto, true))
      },
    })
  }

  const comprarPildora = (pildora: PildoraVenta) => {
    void abrirConfirmacion({
      encabezado: 'Compra',
      titulo: `Comprar ${pildora.nombre}`,
      texto: `Precio: ${pildora.precio} piedras espirituales. Tienes ${snapshot.stn}.`,
      textoBoton: 'Comprar',
      ejecutar: async () => {
        setPildoraDetalle(null)
        await ejecutar(api.comprarPildora(slot, pildora.identificador))
      },
    })
  }

  const vender = (material: keyof Materiales) => {
    void ejecutar(api.venderMaterial(slot, material))
  }

  const abrirDetalle = async (carta: CartaResumen) => {
    try {
      const respuesta = await api.detalleCarta(
        carta.identificador,
        snapshot.sc ?? undefined,
      )
      setDetalle(respuesta.carta)
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    }
  }

  const tabs = (
    <div className="sects wsel" role="tablist" aria-label="Puestos del mercado">
      {[...sectas.map((secta) => secta.identificador), 'neu'].map((clave) => {
        const etiqueta =
          clave === 'neu'
            ? 'General'
            : (sectas.find((secta) => secta.identificador === clave)?.nombre ??
              clave)
        const propia =
          clave === (snapshot.sc ?? snapshot.sect) || clave === 'neu'
        return (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={puesto === clave}
            className={`chip${puesto === clave ? ' on' : ''}`}
            onClick={() => {
              setPuesto(clave)
              setMensaje('')
              setDetalle(null)
              setPildoraDetalle(null)
            }}
          >
            {etiqueta}
            {propia && clave !== 'neu' ? ' ★' : ''}
          </button>
        )
      })}
    </div>
  )

  const lote = puestoActual?.lote
  const seccionLote = lote ? (
    <div className="bags">
      <div className="bt-lote">
        <span
          className="ico-material"
          aria-hidden="true"
          dangerouslySetInnerHTML={{
            __html: iconoMaterial(
              MATERIAL_GLYPH[lote.material as keyof Materiales] ?? 'dust',
            ),
          }}
        />
        <b>{lote.nombre}</b>
        <small>
          +{lote.cantidad} {MATERIAL_NOMBRE[lote.material as keyof Materiales]}
        </small>
        <button
          type="button"
          className="chip"
          disabled={!esPropio || snapshot.stn < lote.costo}
          onClick={comprarLote}
        >
          💎 {lote.costo}
        </button>
      </div>
    </div>
  ) : null

  const seccionCartas = (
    <div className="mkg">
      {cartasPuesto.map((carta) => {
        const copias = snapshot.col[carta.identificador] ?? 0
        const maximo = copias >= 3
        const precio = precioCompraLocal(carta.rareza)
        const bloqueada = !esPropio
        return (
          <div key={carta.identificador} className="mki">
            <button
              type="button"
              className="mki-carta"
              aria-label={`Ver detalles de ${carta.nombre}`}
              onClick={() => void abrirDetalle(carta)}
            >
              <span
                className="arte-carta"
                aria-hidden="true"
                dangerouslySetInnerHTML={{
                  __html: arteCarta(carta.identificador),
                }}
              />
              <small
                className="color-rareza"
                style={{ color: COLOR_RAREZA[carta.rareza] }}
              >
                {carta.nombre}
              </small>
              <small>
                {TIPO_CARTA[carta.tipo] ?? 'Carta'} · {carta.coste_qi} Qi
              </small>
            </button>
            <small className="own">Tienes {copias}</small>
            <button
              type="button"
              className="chip"
              disabled={bloqueada || maximo || snapshot.stn < precio}
              onClick={() => comprarCarta(carta)}
            >
              {maximo
                ? 'Máximo (3)'
                : bloqueada
                  ? '🔒 Bloqueado'
                  : `💎 ${precio}`}
            </button>
          </div>
        )
      })}
      {cartasPuesto.length === 0 && (
        <p className="aviso">Este puesto no tiene cartas a la venta ahora.</p>
      )}
    </div>
  )

  const seccionVitrina = esGeneral && alquimia ? (
    <>
      <h2>Píldoras</h2>
      <p className="q">
        Pulsa un objeto para ver su detalle antes de comprar. Solo se venden
        las que ya sabes elaborar y las básicas.
      </p>
      <div className="bags">
        {vitrina
          .filter((pildora) => !pildora.es_talisman)
          .map((pildora) => (
            <button
              key={pildora.identificador}
              type="button"
              className="bt-vitrina"
              aria-label={`Ver detalles de ${pildora.nombre}`}
              onClick={() => setPildoraDetalle(pildora)}
            >
              <IconoPildora icono={pildora.icono} />
              <b>{pildora.nombre}</b>
              <small>
                {pildora.tipo} · tienes {snapshot.pil[pildora.identificador] ?? 0}
              </small>
              <small>💎 {pildora.precio}</small>
            </button>
          ))}
      </div>
      <h2>Talismanes</h2>
      <div className="bags">
        {vitrina
          .filter((pildora) => pildora.es_talisman)
          .map((pildora) => (
            <button
              key={pildora.identificador}
              type="button"
              className="bt-vitrina"
              aria-label={`Ver detalles de ${pildora.nombre}`}
              onClick={() => setPildoraDetalle(pildora)}
            >
              <IconoPildora icono={pildora.icono} />
              <b>{pildora.nombre}</b>
              <small>
                {pildora.tipo} · tienes {snapshot.pil[pildora.identificador] ?? 0}
              </small>
              <small>💎 {pildora.precio}</small>
            </button>
          ))}
      </div>
    </>
  ) : null

  const seccionVenta = esGeneral ? (
    <>
      <h2>Vender materiales</h2>
      <div className="bags">
        {(['h', 'p', 'n'] as Array<keyof Materiales>).map((material) => (
          <div key={material} className="bt-lote">
            <b>
              {MATERIAL_ICONO[material]} {MATERIAL_NOMBRE[material]} (
              {snapshot.mat[material]})
            </b>
            <button
              type="button"
              className="chip"
              disabled={!snapshot.mat[material]}
              onClick={() => vender(material)}
            >
              Vender 💎 {catalogo?.precios_venta[material] ?? 0}
            </button>
          </div>
        ))}
      </div>
    </>
  ) : null

  const modalDetalle: ReactNode = detalle ? (
    <div
      className="capa-oscuro"
      onClick={() => setDetalle(null)}
    >
      <div
        className="carta-modal modal-detalle"
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle de ${detalle.nombre}`}
        onClick={(evento) => evento.stopPropagation()}
      >
        <button
          type="button"
          className="chip"
          autoFocus
          onClick={() => setDetalle(null)}
        >
          ✕ Cerrar
        </button>
        <h3 style={{ color: COLOR_RAREZA[detalle.rareza] }}>
          {detalle.nombre}
        </h3>
        <span
          className="arte-carta detalle"
          aria-hidden="true"
          dangerouslySetInnerHTML={{
            __html: arteCarta(detalle.identificador),
          }}
        />
        <p className="q">
          {TIPO_CARTA[detalle.tipo] ?? 'Carta'} ·{' '}
          <b style={{ color: COLOR_RAREZA[detalle.rareza] }}>
            {nombreRareza(detalle.rareza)}
          </b>{' '}
          · {detalle.secta_visible} · Coste {detalle.coste_qi} Qi
        </p>
        <h4>Descripción</h4>
        {detalle.descripcion.length ? (
          detalle.descripcion.map((linea, i) => (
            <p key={i} className="q">
              {linea}
            </p>
          ))
        ) : (
          <p className="q">—</p>
        )}
        {detalle.estadisticas.length > 0 && (
          <>
            <h4>Estadísticas</h4>
            <ul className="lista-detalle">
              {detalle.estadisticas.map(([etiqueta, valor]) => (
                <li key={etiqueta}>
                  <span>{etiqueta}</span>
                  <b>{valor}</b>
                </li>
              ))}
            </ul>
          </>
        )}
        {detalle.propiedades.length > 0 && (
          <>
            <h4>Propiedades</h4>
            <ul className="lista-detalle">
              {detalle.propiedades.map((propiedad) => (
                <li key={propiedad}>
                  <span>{propiedad}</span>
                </li>
              ))}
            </ul>
          </>
        )}
        <h4>Obtención</h4>
        {detalle.obtencion.map((linea, i) => (
          <p key={i} className="q">
            {linea}
          </p>
        ))}
        <p className="q">
          Tienes {snapshot.col[detalle.identificador] ?? 0}/3 copias.
        </p>
        <div className="fila-modal">
          <button
            type="button"
            className="boton principal"
            disabled={
              !esPropio ||
              (snapshot.col[detalle.identificador] ?? 0) >= 3 ||
              snapshot.stn < detalle.precio
            }
            onClick={() => {
              const copias = snapshot.col[detalle.identificador] ?? 0
              const precio = detalle.precio
              const nombre = detalle.nombre
              const rareza = detalle.rareza
              const id = detalle.identificador
              setDetalle(null)
              void abrirConfirmacion({
                encabezado: 'Compra',
                titulo: `Comprar «${nombre}»`,
                texto:
                  `Precio: ${precio} piedras espirituales ` +
                  `(${nombreRareza(rareza)}). Tienes ${snapshot.stn}. ` +
                  `Tienes ${copias}/3 copias.`,
                textoBoton: 'Comprar',
                ejecutar: async () => {
                  await ejecutar(api.comprarCarta(slot, id))
                },
              })
            }}
          >
            {(snapshot.col[detalle.identificador] ?? 0) >= 3
              ? 'Máximo (3 copias)'
              : !esPropio
                ? '🔒 No disponible para tu secta'
                : `Comprar por 💎 ${detalle.precio}`}
          </button>
          <button
            type="button"
            className="boton fantasma"
            onClick={() => setDetalle(null)}
          >
            ‹ Volver al mercado
          </button>
        </div>
      </div>
    </div>
  ) : null

  const modalPildora: ReactNode = pildoraDetalle ? (
    <div className="capa-oscuro" onClick={() => setPildoraDetalle(null)}>
      <div
        className="carta-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle de ${pildoraDetalle.nombre}`}
        onClick={(evento) => evento.stopPropagation()}
      >
        <div className="evi-pill">
          <IconoPildora icono={pildoraDetalle.icono} />
        </div>
        <h3>{pildoraDetalle.nombre}</h3>
        <p className="q">{pildoraDetalle.efecto}.</p>
        <ul className="lista-detalle">
          <li>
            <span>Tipo</span>
            <b>{pildoraDetalle.tipo}</b>
          </li>
          <li>
            <span>Precio</span>
            <b>{pildoraDetalle.precio} piedras</b>
          </li>
          <li>
            <span>Tienes</span>
            <b>{snapshot.pil[pildoraDetalle.identificador] ?? 0}</b>
          </li>
          {pildoraDetalle.receta_aprendida && (
            <li>
              <span>Receta</span>
              <b>Aprendida</b>
            </li>
          )}
        </ul>
        <div className="fila-modal">
          <button
            type="button"
            className="boton principal"
            disabled={snapshot.stn < pildoraDetalle.precio}
            onClick={() => comprarPildora(pildoraDetalle)}
          >
            Comprar por {pildoraDetalle.precio}
          </button>
          <button
            type="button"
            className="boton fantasma"
            onClick={() => setPildoraDetalle(null)}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  ) : null

  return (
    <section className="pantalla mercado" aria-label="Mercado del Sendero">
      <header className="cabecera-taller">
        <h1>Mercado del Sendero</h1>
        <p className="q">
          Aquí la moneda son las piedras espirituales (灵石). Cada secta tiene
          su puesto; solo compras en el de tu secta (★) y en el General. Las
          reliquias y las cartas Celestiales no se venden.{' '}
          <b>Pulsa un objeto para ver su detalle; toda compra pide confirmación.</b>
        </p>
        <div className="st">
          <span>💎 Tienes {snapshot.stn}</span>
        </div>
        {mensaje && <p className="hint">{mensaje}</p>}
      </header>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {tabs}

      <h2>
        {puestoActual?.vendedor ?? 'Puesto'}
        {esGeneral ? '' : ` · ${nombrePuesto}`}
      </h2>
      <p className="q">
        «{puestoActual?.frase ?? ''}»
        {!esPropio && (
          <>
            {' '}
            <b>Solo discípulos de esta secta pueden comprar aquí.</b>
          </>
        )}
      </p>

      {seccionLote}
      {seccionCartas}
      {seccionVitrina}
      {seccionVenta}

      {modalDetalle}
      {modalPildora}

      {confirmacion && (
        <div className="capa-oscuro" onClick={() => setConfirmacion(null)}>
          <div
            className="carta-modal"
            role="dialog"
            aria-modal="true"
            aria-label={confirmacion.encabezado}
            onClick={(evento) => evento.stopPropagation()}
          >
            <h3>{confirmacion.titulo}</h3>
            <p>{confirmacion.texto}</p>
            <div className="fila-modal">
              <button
                type="button"
                className="boton principal"
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

/** Tabla `RP` del monolito: precio de compra por rareza. */
const PRECIO_RAREZA = [6, 12, 24, 45, 90, 180]

export function precioCompraLocal(rareza: number): number {
  return PRECIO_RAREZA[rareza] ?? PRECIO_RAREZA[0]
}

export function nombreRareza(rareza: number): string {
  return (
    ['Común', 'Poco común', 'Rara', 'Épica', 'Legendaria', 'Celestial'][
      rareza
    ] ?? 'Común'
  )
}
