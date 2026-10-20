/** Bolsa Qiankun: inventario completo del cultivador.

Port de `bagUI` (js/06-contenido.js:154-162): muestra materiales,
píldoras/talismanes, un aviso de armaduras/artefactos (el detalle está
en la pestaña Equipo), bestias domadas, cartas por rareza y recetas. El
registro `nlog` del monolito vive solo en memoria y no persiste, así
que aquí se omite (con estado vacío fijo).
*/

import { useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import { iconoMaterial } from '../arte/iconoMaterial'
import type {
  BestiaResumen,
  CartaResumen,
  CatalogoAlquimia,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  snapshot: SnapshotPartida
}

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** Nombres de materiales (`MN` del JS). */
const NOMBRE_MATERIAL: Record<string, string> = {
  h: 'Hierbas espirituales',
  n: 'Núcleos de bestia',
  p: 'Polvo de jade',
}

/** Iconos de materiales (clases de `ico()` del monolito). */
const ICO_MATERIAL: Record<string, string> = {
  h: 'herb',
  n: 'core',
  p: 'dust',
}

/** Descripciones de uso (`bagUI`). */
const USO_MATERIAL: Record<string, string> = {
  h: 'Píldoras y armaduras',
  n: 'Recetas y equipo raros',
  p: 'Forja y refinado',
}

export default function Bolsa({ snapshot }: Props) {
  const [alquimia, setAlquimia] = useState<CatalogoAlquimia | null>(null)
  const [cartas, setCartas] = useState<CartaResumen[]>([])
  const [bestias, setBestias] = useState<BestiaResumen[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [catAlq, listaCartas, listaBestias] = await Promise.all([
          api.obtenerAlquimia(),
          api.listarCartas(),
          api.listarBestias(),
        ])
        if (!vigente) return
        setAlquimia(catAlq)
        setCartas(listaCartas)
        setBestias(listaBestias)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const pildoras = Object.keys(snapshot.pil).filter(
    (k) => (snapshot.pil[k] ?? 0) > 0,
  )
  const recetas = Object.keys(snapshot.rec)
  const cartasPorId = new Map(cartas.map((c) => [c.identificador, c]))
  const bestiasDomadas = bestias.filter((_, i) =>
    snapshot.wins.includes(i * 6 + 5),
  )
  const idsCol = Object.keys(snapshot.col)
  const totalCartas = idsCol.reduce((a, id) => a + (snapshot.col[id] ?? 0), 0)
  const totalObjetos =
    snapshot.mat.h +
    snapshot.mat.n +
    snapshot.mat.p +
    pildoras.reduce((a, k) => a + (snapshot.pil[k] ?? 0), 0) +
    bestiasDomadas.length +
    totalCartas

  const nombrePildora = (k: string): string =>
    alquimia?.pildoras.find((p) => p.identificador === k)?.nombre ?? k

  const efectoPildora = (k: string): string =>
    alquimia?.pildoras.find((p) => p.identificador === k)?.efecto ?? ''

  const iconoPildora = (k: string): string =>
    alquimia?.pildoras.find((p) => p.identificador === k)?.icono ?? 'poc'

  const agruparPorRareza = (): Array<{ rareza: number; ids: string[] }> => {
    const grupos = new Map<number, string[]>()
    for (const id of idsCol) {
      const carta = cartasPorId.get(id)
      const rareza = carta?.rareza ?? 0
      const lista = grupos.get(rareza) ?? []
      lista.push(id)
      grupos.set(rareza, lista)
    }
    return [...grupos.entries()]
      .sort((a, b) => a[0] - b[0])
      .map(([rareza, ids]) => ({ rareza, ids }))
  }

  const tile = (
    icono: React.ReactNode,
    cantidad: string,
    nombre: string,
    sub: string,
    activa = false,
  ) => (
    <div className={`bt${activa ? ' on' : ''}`}>
      {icono}
      <b>{cantidad}</b>
      <small>{nombre}</small>
      {sub && <small>{sub}</small>}
    </div>
  )

  const glyph = (k: string) => (
    <span
      className="ico-material"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: iconoMaterial(k) }}
    />
  )

  return (
    <section className="pantalla bolsa" aria-label="Bolsa Qiankun">
      <h1>Bolsa Qiankun</h1>
      <p className="qk-sub">Anillo de almacenamiento</p>

      <div className="st-qk">
        <span>Objetos en total: {totalObjetos}</span>
        <span>Cartas distintas: {idsCol.length}</span>
        <span>
          Recetas: {recetas.length}/{alquimia?.pildoras.length ?? '…'}
        </span>
      </div>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      <h2 className="sh2">Materiales</h2>
      <div className="bags">
        {tile(
          glyph('dust'),
          String(snapshot.stn),
          'Piedras espirituales',
          'Moneda del mercado',
        )}
        {(['h', 'n', 'p'] as const).map((k) =>
          tile(
            glyph(ICO_MATERIAL[k] ?? 'dust'),
            String(snapshot.mat[k]),
            NOMBRE_MATERIAL[k] ?? k,
            USO_MATERIAL[k] ?? '',
          ),
        )}
      </div>

      <h2 className="sh2">Píldoras y talismanes</h2>
      {pildoras.length ? (
        <div className="bags">
          {pildoras.map((k) =>
            tile(
              glyph(iconoPildora(k)),
              `x${snapshot.pil[k]}`,
              nombrePildora(k),
              efectoPildora(k),
            ),
          )}
        </div>
      ) : (
        <p className="nl">
          No llevas píldoras ni talismanes. Elabóralos en Alquimia.
        </p>
      )}

      <h2 className="sh2">Armaduras y artefactos</h2>
      <p className="nl">
        Aún no hay equipo disponible. Forja piezas en la pestaña Equipo.
      </p>

      <h2 className="sh2">Bestias domadas</h2>
      {bestiasDomadas.length ? (
        <div className="bags">
          {bestiasDomadas.map((b) =>
            tile(
              '🐾',
              `${b.ataque}/${b.vida}`,
              b.nombre,
              b.identificador === snapshot.be ? 'Equipada' : '',
              b.identificador === snapshot.be,
            ),
          )}
        </div>
      ) : (
        <p className="nl">
          No has domado bestias aún. Vence a los jefes de nivel para ganar
          una por nivel.
        </p>
      )}

      <h2 className="sh2">Cartas</h2>
      {idsCol.length ? (
        agruparPorRareza().map(({ rareza, ids }) => (
          <div key={rareza}>
            <h3 className="sh3">Rareza {rareza}</h3>
            <div className="bags">
              {ids.map((id) => {
                const carta = cartasPorId.get(id)
                return tile(
                  carta?.nombre ?? id,
                  `x${snapshot.col[id]}`,
                  carta?.nombre ?? id,
                  carta
                    ? `${carta.ataque}/${carta.vida} · ${carta.secta ?? 'neutral'}`
                    : '',
                )
              })}
            </div>
          </div>
        ))
      ) : (
        <p className="nl">
          Tu colección está vacía. Gana combates o compra cartas en el
          Mercado.
        </p>
      )}

      <h2 className="sh2">Recetas aprendidas</h2>
      {recetas.length ? (
        <div className="bags">
          {recetas.map((k) =>
            tile(glyph('scroll'), '✓', nombrePildora(k), 'Receta aprendida'),
          )}
        </div>
      ) : (
        <p className="nl">
          No has aprendido recetas aún. Visita la Alquimia o reclama
          misiones.
        </p>
      )}
    </section>
  )
}
