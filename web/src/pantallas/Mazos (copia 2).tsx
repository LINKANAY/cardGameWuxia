/** Mazos: crear, editar, activar y desequipar mazos de 40 cartas.

Puerto del tab `dk` del monolito (`dkUI`/`dNew`/`dAdd`/`dRm`/`dRen`/
`dClr`/`dFill`/`dUse`/`dDup`/`dDel`/`dUneq` en `js/04-mazos-formaciones.js`
y `js/12-v47-init.js`). Dos vistas: lista de mazos (con el automático)
y editor de un mazo (curva de coste, filtros y ± por carta).
*/

import { useEffect, useMemo, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type {
  CartaResumen,
  MazoGuardado,
  ResultadoMazos,
  SectaResumen,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  slot: string
  snapshot: SnapshotPartida
  sectas: SectaResumen[]
  onSnapshot: (snapshot: SnapshotPartida) => void
}

/** Copias máximas por carta y tamaño de mazo (`own3`/`DM` del JS). */
const MAX_COPIAS = 3
const TAMANO_MAZO = 40
const MAX_MAZOS = 8

const TEXTO_INTRO =
  'Arma mazos de 40 cartas (máximo 3 copias de una) con las cartas de ' +
  'tu secta, las neutrales y las que ganas tras cada combate. Si el ' +
  'mazo en uso está incompleto, se usa el automático.'

const COLOR_RAREZA = [
  '#a8b4c2',
  '#7be0b8',
  '#e3bf6a',
  '#c084fc',
  '#f0a868',
  '#ff6b6b',
]

const NOMBRE_RAREZA = [
  'Común',
  'Poco común',
  'Rara',
  'Épica',
  'Legendaria',
  'Celestial',
]

/** Filtros de sección del editor (`F` de `dkUI`). */
const FILTROS_SECCION: Array<[string, string]> = [
  ['all', 'Todas'],
  ['in', 'En el mazo'],
  ['sec', 'Mi secta'],
  ['neu', 'Neutrales'],
  ['oth', 'Otras sectas'],
  ['C', 'Criaturas'],
  ['T', 'Técnicas'],
  ['P', 'Píldoras'],
  ['FR', 'Formac. y runas'],
]

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

function tamanoMazo(mazo: MazoGuardado): number {
  return Object.values(mazo.c).reduce((total, n) => total + n, 0)
}

export default function Mazos({ slot, snapshot, sectas, onSnapshot }: Props) {
  const [cartas, setCartas] = useState<CartaResumen[]>([])
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [editor, setEditor] = useState<number | null>(null)
  const [confirmarBorrar, setConfirmarBorrar] = useState<number | null>(null)
  const [filtroSeccion, setFiltroSeccion] = useState('all')
  const [filtroCartas, setFiltroCartas] = useState('all')
  const [ordenCartas, setOrdenCartas] = useState<'name' | 'cost' | 'rarity'>(
    'name',
  )
  const [inspeccionada, setInspeccionada] = useState<string | null>(null)

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const lista = await api.listarCartas()
        if (vigente) setCartas(lista)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const cartaPorId = useMemo(
    () => Object.fromEntries(cartas.map((carta) => [carta.identificador, carta])),
    [cartas],
  )

  const baseSecta = useMemo(() => {
    const propia = sectas.find(
      (secta) => secta.identificador === snapshot.sect,
    )
    return new Set(propia?.cartas_iniciales ?? [])
  }, [sectas, snapshot.sect])

  /** `own3(id)` del JS: base/neutral gratis a 3, resto lo poseído. */
  const copiasUsables = (identificador: string): number => {
    const carta = cartaPorId[identificador]
    const gratis = baseSecta.has(identificador) || carta?.es_neutral === true
    return Math.min(
      MAX_COPIAS,
      Math.max(gratis ? 3 : 0, snapshot.col[identificador] ?? 0),
    )
  }

  const mazoValido = (mazo: MazoGuardado | undefined): boolean => {
    if (!mazo) return false
    if (tamanoMazo(mazo) !== TAMANO_MAZO) return false
    return Object.entries(mazo.c).every(
      ([identificador, n]) =>
        cartaPorId[identificador] !== undefined &&
        n <= copiasUsables(identificador),
    )
  }

  const mazoEnUso =
    snapshot.ad >= 0 && snapshot.ad < snapshot.dk.length
      ? snapshot.dk[snapshot.ad]
      : undefined
  const enUsoValido = mazoValido(mazoEnUso)

  const ejecutar = async (
    llamada: Promise<ResultadoMazos>,
    opciones: { cerrarEditor?: boolean } = {},
  ) => {
    try {
      const resultado = await llamada
      setMensaje(resultado.mensaje)
      setError(null)
      onSnapshot(resultado.snapshot)
      if (opciones.cerrarEditor) setEditor(null)
    } catch (errorDeLlamada) {
      setMensaje('')
      setError(mensajeDe(errorDeLlamada))
    }
  }

  // ---- Acciones de la lista ----

  const crear = (desdeAutomatico: boolean) =>
    void ejecutar(api.crearMazo(slot, desdeAutomatico))

  const usar = (indice: number) =>
    void ejecutar(api.usarMazo(slot, indice))

  const duplicar = (indice: number) =>
    void ejecutar(api.duplicarMazo(slot, indice))

  const eliminar = (indice: number) => {
    if (confirmarBorrar !== indice) {
      setConfirmarBorrar(indice)
      return
    }
    setConfirmarBorrar(null)
    void ejecutar(api.eliminarMazo(slot, indice), { cerrarEditor: true })
  }

  const desequipar = (identificador: string) =>
    void ejecutar(api.desequiparCarta(slot, identificador))

  // ---- Acciones del editor ----

  const mazoEditado = editor !== null ? snapshot.dk[editor] : undefined

  const renombrar = (nombre: string) => {
    if (editor === null) return
    if (!nombre.trim()) return
    void ejecutar(api.renombrarMazo(slot, editor, nombre))
  }

  const anadir = (identificador: string) => {
    if (editor === null) return
    void ejecutar(api.anadirCartaMazo(slot, editor, identificador))
  }

  const quitar = (identificador: string) => {
    if (editor === null) return
    void ejecutar(api.quitarCartaMazo(slot, editor, identificador))
  }

  const vaciar = () => {
    if (editor === null) return
    void ejecutar(api.vaciarMazo(slot, editor))
  }

  const autocompletar = () => {
    if (editor === null) return
    void ejecutar(api.autocompletarMazo(slot, editor))
  }

  // ---- Vista: lista de mazos ----

  if (editor === null || !mazoEditado) {
    return (
      <section className="pantalla mazos" aria-label="Mazos">
        <h1>Mazos</h1>
        <p className="q">{TEXTO_INTRO}</p>
        <div className="st">
          <span>
            En uso:{' '}
            <b>
              {enUsoValido && mazoEnUso ? mazoEnUso.n : 'Automático'}
            </b>
          </span>
          <span>
            Mazos: {snapshot.dk.length}/{MAX_MAZOS}
          </span>
        </div>

        {mensaje && <p className="hint">{mensaje}</p>}
        {error && (
          <div className="banner-error" role="alert">
            {error}
          </div>
        )}

        <div className="grid">
          <div className={`opt dki${enUsoValido ? '' : ' on'}`}>
            <b>Mazo automático</b>
            <small>
              Tu secta y todo lo que has ganado, completado con neutrales.
            </small>
            <button
              type="button"
              className="chip"
              onClick={() => usar(-1)}
            >
              {enUsoValido ? 'Usar' : '✔ En uso'}
            </button>
          </div>

          {snapshot.dk.map((mazo, indice) => {
            const tamano = tamanoMazo(mazo)
            const valido = mazoValido(mazo)
            const activo = snapshot.ad === indice
            const estado = valido
              ? '✔ válido'
              : tamano < TAMANO_MAZO
                ? 'incompleto'
                : 'tiene cartas que ya no tienes'
            return (
              <div key={`${mazo.n}-${indice}`} className={`opt dki${activo ? ' on' : ''}`}>
                <b>{mazo.n}</b>
                <small>
                  {tamano}/{TAMANO_MAZO} cartas · {estado}
                </small>
                <div className="acciones-cartas">
                  <button
                    type="button"
                    className="chip"
                    onClick={() => usar(indice)}
                  >
                    {activo ? '✔ En uso' : 'Usar'}
                  </button>
                  <button
                    type="button"
                    className="chip"
                    onClick={() => {
                      setEditor(indice)
                      setFiltroSeccion('all')
                      setInspeccionada(null)
                    }}
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    className="chip"
                    onClick={() => duplicar(indice)}
                  >
                    Duplicar
                  </button>
                  <button
                    type="button"
                    className="chip"
                    onClick={() => eliminar(indice)}
                  >
                    {confirmarBorrar === indice ? '¿Seguro?' : 'Eliminar'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        <p className="fila-nuevos-mazos">
          <button
            type="button"
            className="chip"
            onClick={() => crear(false)}
          >
            ＋ Mazo vacío
          </button>{' '}
          <button
            type="button"
            className="chip"
            onClick={() => crear(true)}
          >
            ＋ Copia del automático
          </button>
        </p>

        <h2 className="sh2">Colección ({Object.keys(snapshot.col).length})</h2>
        <p className="q">
          Todas tus cartas. Fusionar y desmantelar están en Alquimia; aquí
          puedes sacar copias del mazo en uso.
        </p>
        {Object.keys(snapshot.col).length ? (
          <div className="fila-cartas colx">
            {Object.entries(snapshot.col)
              .filter(([, n]) => n > 0)
              .map(([identificador, n]) => {
                const carta = cartaPorId[identificador]
                const enUso = mazoEnUso?.c[identificador] ?? 0
                return (
                  <div key={identificador} className="mini-carta">
                    <small
                      className="color-rareza"
                      style={{
                        color:
                          COLOR_RAREZA[carta?.rareza ?? 0],
                      }}
                    >
                      {carta?.nombre ?? identificador}
                    </small>
                    <small className="copias">
                      ×{n}
                      {enUso ? ` · en mazo ×${enUso}` : ''}
                    </small>
                    <div className="acciones-cartas">
                      <button
                        type="button"
                        className="chip"
                        disabled={!enUso}
                        onClick={() => desequipar(identificador)}
                      >
                        Desequipar
                      </button>
                    </div>
                  </div>
                )
              })}
          </div>
        ) : (
          <p>Aún no tienes cartas obtenidas.</p>
        )}
      </section>
    )
  }

  // ---- Vista: editor de un mazo ----

  const d = mazoEditado
  const tamano = tamanoMazo(d)

  const conteoPorTipo = (tipo: string): number =>
    Object.entries(d.c).reduce(
      (total, [identificador, n]) =>
        total + (cartaPorId[identificador]?.tipo === tipo ? n : 0),
      0,
    )

  // curva de coste: índice 0–8 (8 = 8+)
  const curva = Array.from({ length: 9 }, () => 0)
  for (const [identificador, n] of Object.entries(d.c)) {
    const coste = cartaPorId[identificador]?.coste_qi ?? 0
    curva[Math.min(8, coste)] += n
  }
  const curvaMax = Math.max(1, ...curva)

  const coincideFiltro = (identificador: string): boolean => {
    const carta = cartaPorId[identificador]
    if (!carta) return false
    switch (filtroSeccion) {
      case 'in':
        return (d.c[identificador] ?? 0) > 0
      case 'sec':
        return carta.secta === snapshot.sect
      case 'neu':
        return carta.secta === null || carta.secta === 'neu'
      case 'oth':
        return carta.secta !== null && carta.secta !== 'neu' &&
          carta.secta !== snapshot.sect
      case 'C':
      case 'T':
      case 'P':
        return carta.tipo === filtroSeccion
      case 'FR':
        return carta.tipo === 'F' || carta.tipo === 'R'
      default:
        return true
    }
  }

  const pool = cartas
    .filter(
      (carta) =>
        copiasUsables(carta.identificador) > 0 &&
        coincideFiltro(carta.identificador) &&
        (filtroCartas === 'all' ||
          (filtroCartas === 'in' &&
            (d.c[carta.identificador] ?? 0) > 0) ||
          (filtroCartas === 'rarity' && carta.rareza >= 4)),
    )
    .sort((a, b) => {
      if (ordenCartas === 'cost') {
        return a.coste_qi - b.coste_qi || a.nombre.localeCompare(b.nombre)
      }
      if (ordenCartas === 'rarity') {
        return b.rareza - a.rareza || a.nombre.localeCompare(b.nombre)
      }
      return a.nombre.localeCompare(b.nombre)
    })

  return (
    <section className="pantalla mazos" aria-label={`Editor de ${d.n}`}>
      <div className="dkh">
        <div className="bar">
          <button
            type="button"
            className="boton fantasma"
            onClick={() => setEditor(null)}
          >
            ‹ Mazos
          </button>
          <input
            className="dnm"
            defaultValue={d.n}
            maxLength={22}
            aria-label="Nombre del mazo"
            key={`${editor}-${d.n}`}
            onBlur={(evento) => renombrar(evento.target.value)}
            onKeyDown={(evento) => {
              if (evento.key === 'Enter') {
                renombrar((evento.target as HTMLInputElement).value)
              }
            }}
          />
          <b
            style={{
              color: tamano === TAMANO_MAZO ? 'var(--jade)' : 'var(--gold)',
            }}
          >
            {tamano}/{TAMANO_MAZO}
          </b>
        </div>

        <div className="cur" aria-label="Curva de coste">
          {curva.map((cantidad, coste) => (
            <div key={coste}>
              <span>{cantidad || ''}</span>
              <i
                style={{ height: `${(cantidad / curvaMax) * 34 + 2}px` }}
              />
              <small>
                {coste}
                {coste === 8 ? '+' : ''}
              </small>
            </div>
          ))}
        </div>

        <div className="st">
          <span>⚔ {conteoPorTipo('C')} criaturas</span>
          <span>✦ {conteoPorTipo('T')} técnicas</span>
          <span>
            阵 {conteoPorTipo('F') + conteoPorTipo('R')} formac./runas
          </span>
          <span>◈ {conteoPorTipo('P')} píldoras</span>
        </div>

        <div className="dact">
          <button type="button" className="chip" onClick={autocompletar}>
            Autocompletar
          </button>
          <button type="button" className="chip" onClick={vaciar}>
            Vaciar
          </button>
          <button
            type="button"
            className="chip"
            onClick={() => usar(editor)}
          >
            {snapshot.ad === editor ? '✔ En uso' : 'Usar este mazo'}
          </button>
        </div>
      </div>

      {mensaje && <p className="hint">{mensaje}</p>}
      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      <div className="card-tools">
        <label>
          Mostrar{' '}
          <select
            aria-label="Filtrar cartas"
            value={filtroCartas}
            onChange={(evento) => setFiltroCartas(evento.target.value)}
          >
            <option value="all">Todas las que posees</option>
            <option value="in">En este mazo</option>
            <option value="rarity">Raras y superiores</option>
          </select>
        </label>
        <label>
          Ordenar{' '}
          <select
            aria-label="Ordenar cartas"
            value={ordenCartas}
            onChange={(evento) =>
              setOrdenCartas(
                evento.target.value as 'name' | 'cost' | 'rarity',
              )
            }
          >
            <option value="name">Nombre</option>
            <option value="cost">Coste</option>
            <option value="rarity">Rareza</option>
          </select>
        </label>
      </div>

      <div className="sects wsel">
        {FILTROS_SECCION.map(([clave, titulo]) => (
          <button
            key={clave}
            type="button"
            className={`chip${filtroSeccion === clave ? ' on' : ''}`}
            onClick={() => setFiltroSeccion(clave)}
          >
            {titulo}
          </button>
        ))}
      </div>

      <div className="dl">
        {pool.map((carta) => {
          const enMazo = d.c[carta.identificador] ?? 0
          const usables = copiasUsables(carta.identificador)
          return (
            <div
              key={carta.identificador}
              className={`dr${enMazo ? ' in' : ''}`}
              style={{
                borderLeft: `3px solid ${COLOR_RAREZA[carta.rareza]}`,
              }}
            >
              <span className="dc">{carta.coste_qi}</span>
              <div className="dn2">
                <b style={{ color: COLOR_RAREZA[carta.rareza] }}>
                  {carta.nombre}{' '}
                  <small>{NOMBRE_RAREZA[carta.rareza] ?? ''}</small>
                </b>
                <small>
                  {carta.tipo === 'C'
                    ? `⚔ ${carta.ataque}/${carta.vida} · `
                    : ''}
                  {carta.reliquia ? '🔒 Requiere progreso · ' : ''}
                  {carta.tipo === 'F'
                    ? 'Formación'
                    : carta.tipo === 'R'
                      ? 'Runa'
                      : carta.tipo === 'C'
                        ? 'Criatura'
                        : carta.tipo === 'P'
                          ? 'Píldora'
                          : 'Técnica'}
                </small>
                {carta.descripcion.length > 0 && (
                  <span className="card-descripcion">
                    {carta.descripcion.map((linea) => (
                      <small key={linea}>{linea}</small>
                    ))}
                  </span>
                )}
                {inspeccionada === carta.identificador && (
                  <small className="card-inspector">
                    Rareza: {NOMBRE_RAREZA[carta.rareza] ?? 'Común'} · Coste:{' '}
                    {carta.coste_qi}
                    {carta.secta
                      ? ` · Secta: ${carta.secta === 'neu' ? 'General' : carta.secta}`
                      : ''}
                  </small>
                )}
              </div>
              <div className="dq">
                <button
                  type="button"
                  aria-label={`Quitar ${carta.nombre}`}
                  disabled={!enMazo}
                  onClick={() => quitar(carta.identificador)}
                >
                  −
                </button>
                <i>
                  {enMazo}/{usables}
                </i>
                <button
                  type="button"
                  aria-label={`Añadir ${carta.nombre}`}
                  disabled={enMazo >= usables || tamano >= TAMANO_MAZO}
                  onClick={() => anadir(carta.identificador)}
                >
                  +
                </button>
              </div>
            </div>
          )
        })}
        {!pool.length && <p className="nl">No tienes cartas en esta categoría.</p>}
      </div>
    </section>
  )
}
