/** Pantalla de combate por turnos: intro (`storyHTML`) + batalla (`render`).

La intro replica `storyHTML()` de js/01-datos.js:182: ficha del enemigo
(vida escalada por reino, dificultad, historia, frase), aviso de muerte
permanente, selección de píldoras de inicio (máx. 3, `eqp`) y bolsa de
combate (máx. 4, `eqpB`; 2 usos durante la partida), botones Combatir /
Volver. El combate replica el `render()` de js/06-contenido.js:183 con
barras de héroe, filas con casillas huecas (`<i class="slot">`), mano
con cartas asequibles/no, modales EC/ED/VP y evento de mapa (`ev`).

La sesión de combate vive en el backend (`CombatService`); aquí sólo se
pinta el snapshot y se envían acciones.
*/

import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import { arteCarta } from '../arte/artCarta'
import { figuraSecta } from '../arte/figura'
import { escenaFondo } from '../arte/escena'
import { ding } from '../sonidos'
import type {
  CartaCombate,
  CartaResumen,
  EnemigoResumen,
  EstadoCombate,
  EventoCampana,
  LadoCombate,
  Narrativa,
  PildoraResumen,
  ResultadoCombate,
  SnapshotPartida,
} from '../api/tipos'

interface Props {
  slot: string
  indiceEnemigo: number
  snapshot: SnapshotPartida
  narrativa: Narrativa | null
  onSnapshot: (snapshot: SnapshotPartida) => void
  onSalir: () => void
  /**
   * Tras la muerte permanente (`fin === 'l'`), vuelve al splash para
   * renacer (`reborn()` de js/07-campamento.js:90 → el splash con la
   * puerta de sectas). Sin él se mantiene «Continuar» al campamento.
   */
  onMorir?: () => void
}

const MAX_INICIO = 3
const MAX_BOLSA = 4
const MAX_USOS_BOLSA = 2
const TAMANO_MANO = 5
/** Vida extra por reino aplicada al enemigo (`HP_PER_REALM`). */
const VIDA_POR_REINO = 2

/** Dificultades del monolito (`DF`). */
const DIFICULTADES = [
  'Muy fácil',
  'Fácil',
  'Normal',
  'Difícil',
  'Muy difícil',
  'Boss final',
]

/** Colores de dificultad (`DC`). */
const COLOR_DIFICULTAD = [
  '#8fd9b6',
  '#6cc4a1',
  '#d9b55b',
  '#e09a4a',
  '#c4483d',
  '#b070e0',
]

/** Nombres y colores de rareza (`RN`/`RC` de js/01-datos.js:39). */
const NOMBRE_RAREZA = [
  'Común',
  'Poco común',
  'Rara',
  'Épica',
  'Legendaria',
  'Celestial',
]
const COLOR_RAREZA = [
  '#aab8b2',
  '#6cc4a1',
  '#5aa0e8',
  '#b070e0',
  '#e8a23a',
  '#ff6a6a',
]

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

/** Icono de píldora (`pillIco` de js/07-campamento.js:113). */
function PillIco({ icono }: { icono: string }) {
  if (icono === 'tal') {
    return (
      <span className="tali" aria-hidden="true">
        <i>符</i>
      </span>
    )
  }
  return <span className={`pill ${icono}`} aria-hidden="true" />
}

/** ¿Hay pila aceptable para apilar esta carta de mano (`stkT`)? */
function pilaAceptable(lado: LadoCombate, carta: CartaCombate): boolean {
  if (carta.tipo !== 'C' || carta.bestia) return false
  return lado.tablero.some((c) => c.id === carta.id && !c.bestia)
}

/** `playableCards` de js/10-jugabilidad-musica.js:11. */
function cartasJugables(P: LadoCombate): CartaCombate[] {
  return P.mano.filter(
    (c) =>
      c.coste <= P.qi &&
      !(c.tipo === 'C' && P.tablero.length >= TAMANO_MANO && !pilaAceptable(P, c)),
  )
}

/** `activableCreatures` de js/10-jugabilidad-musica.js:14. */
function habilidadesListas(P: LadoCombate): CartaCombate[] {
  return P.tablero.filter(
    (c) => c.habilidad && !c.usada && P.qi >= c.habilidad.coste,
  )
}

/** `canStillAct` de js/10-jugabilidad-musica.js:15. */
function puedeSeguirActuando(P: LadoCombate): boolean {
  return cartasJugables(P).length > 0 || habilidadesListas(P).length > 0
}

function Carta({
  carta,
  seleccionada,
  no,
  onClick,
  claseExtra,
  golpe,
  bonusFormacion,
}: {
  carta: CartaCombate
  seleccionada?: boolean
  no?: boolean
  onClick?: () => void
  claseExtra?: string
  golpe?: boolean
  /** `pa` de formación + `opa` del lado (`bdg`); sólo en tablero. */
  bonusFormacion?: number
}) {
  const cls = [
    'cartacomate',
    `tipo-${carta.tipo}`,
    seleccionada ? 'seleccionada' : '',
    no ? 'no' : '',
    carta.lista ? 'lista' : '',
    carta.provocar ? 'provocar' : '',
    golpe ? 'golpe' : '',
    claseExtra ?? '',
  ]
    .filter(Boolean)
    .join(' ')
  // `bdg` de F/R: badge izquierdo (pa o daño) y derecho (ph o turno).
  const fr = carta.formacion
  const frIzq = fr
    ? fr.pa
      ? {
          txt: `+${fr.pa}`,
          titulo: `Tus criaturas ganan +${fr.pa} de ataque`,
        }
      : fr.ts && (fr.ts[0] === 'd' || fr.ts[0] === 'm')
        ? {
            txt: String(fr.ts[1]),
            titulo: `Daño por turno: ${fr.ts[1]}`,
          }
        : null
    : null
  const frDer = fr
    ? fr.ph
      ? {
          txt: `+${fr.ph}`,
          titulo: `Tus criaturas ganan +${fr.ph} de vida`,
        }
      : fr.ts
        ? fr.ts[0] === 'h'
          ? {
              txt: String(fr.ts[1]),
              titulo: `Cura por turno: ${fr.ts[1]}`,
            }
          : fr.ts[0] === 's'
            ? {
                txt: String(fr.ts[1]),
                titulo: `Escudo por turno: ${fr.ts[1]}`,
              }
            : fr.ts[0] === 'q'
              ? {
                  txt: String(fr.ts[1]),
                  titulo: `Qi por turno: ${fr.ts[1]}`,
                }
              : fr.ts[0] === 'r'
                ? {
                    txt: String(fr.ts[1]),
                    titulo: `Cartas por turno: ${fr.ts[1]}`,
                  }
                : null
        : null
    : null
  return (
    <button
      type="button"
      className={cls}
      onClick={onClick}
      disabled={!onClick}
      title={`${carta.nombre} (${carta.coste} Qi)`}
    >
      <span className="fila-cabecera">
        <span className="coste">{carta.coste}</span>
        {carta.ataque !== null && (
          <span
            className={`badge-stat batq${bonusFormacion ? ' up' : ''}`}
            title={
              bonusFormacion
                ? `Ataque ${carta.ataque + bonusFormacion} (incluye +${bonusFormacion} de la formación)`
                : `Ataque ${carta.ataque}`
            }
          >
            {bonusFormacion ? carta.ataque + bonusFormacion : carta.ataque}
          </span>
        )}
        {frIzq && (
          <span className="badge-stat batq" title={frIzq.titulo}>
            {frIzq.txt}
          </span>
        )}
        {carta.vida !== null && (
          <span className="badge-stat bvid" title={`Vida ${carta.vida}`}>
            {carta.vida}
          </span>
        )}
        {frDer && (
          <span className="badge-stat bqi" title={frDer.titulo}>
            {frDer.txt}
          </span>
        )}
      </span>
      <b>{carta.nombre}</b>
      <span
        className="carta-arte"
        aria-hidden="true"
        dangerouslySetInnerHTML={{ __html: arteCarta(carta.id) }}
      />
      {carta.provocar && <span className="marca">Provocar</span>}
      {carta.habilidad && <span className="marca hab">Habilidad</span>}
      {carta.usada && <span className="marca usada">Usada</span>}
      {carta.descripcion.length > 0 && (
        <span className="carta-desc">{carta.descripcion.join(' · ')}</span>
      )}
    </button>
  )
}

/** Modal de solo lectura para ver el mazo o el Agujero Negro (descartes). */
function VisorPila({
  titulo,
  cartas,
  onCerrar,
}: {
  titulo: string
  cartas: CartaCombate[]
  onCerrar: () => void
}) {
  return (
    <div className="modal-combate" role="dialog" aria-label={titulo}>
      <div className="evb">{titulo}</div>
      <p className="q">Cartas en la pila: {cartas.length}.</p>
      <div className="mano modal-mano">
        {cartas.map((carta, i) => (
          // eslint-disable-next-line react/no-array-index-key
          <div key={`${carta.id}-${i}`}>
            <Carta carta={carta} />
          </div>
        ))}
        {cartas.length === 0 && <p className="tablero-vacio">Pila vacía.</p>}
      </div>
      <button type="button" onClick={onCerrar}>
        Cerrar
      </button>
    </div>
  )
}

/** `fmH`: casillas huecas del tablero (`<i class="slot">`). */
function CasillasHuecas({ n }: { n: number }) {
  return (
    <>
      {Array.from({ length: Math.max(0, n) }, (_, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <i key={i} className="slot-celda" aria-hidden="true" />
      ))}
    </>
  )
}

/** `fmH` de js/04-mazos-formaciones.js:35: formación y runas del lado. */
function BanderaFormacion({ lado }: { lado: LadoCombate }) {
  if (!lado.fm && lado.rn.length === 0) return null
  return (
    <div className="fmr" role="list" aria-label="Formación y runas activas">
      {lado.fm && (
        <span className="fmb" title={lado.fm.desc.join(' · ')}>
          阵 {lado.fm.nombre}
        </span>
      )}
      {lado.rn.map((r) => (
        <span key={r.id} className="rnb" title={r.desc.join(' · ')}>
          符 {r.nombre} · {r.du} t.
        </span>
      ))}
    </div>
  )
}

function BarraLado({
  lado,
  esJugador,
  figura,
  seleccionandoAtaque,
  onObjetivoHroe,
  golpe,
  danoFlotante,
  onVerMazo,
  onVerVacio,
}: {
  lado: LadoCombate
  esJugador: boolean
  /** SVG de la figura (`fig(k, boss, oi)` del monolito). */
  figura?: string
  seleccionandoAtaque?: boolean
  onObjetivoHroe?: () => void
  golpe?: boolean
  danoFlotante?: number | null
  onVerMazo?: () => void
  onVerVacio?: () => void
}) {
  return (
    <div
      className={`barra-lado${esJugador ? ' propio' : ' rival'}${
        seleccionandoAtaque ? ' objetivo-activo' : ''
      }${golpe ? ' golpe' : ''}${onObjetivoHroe ? ' clic-objetivo' : ''}`}
      role={onObjetivoHroe ? 'button' : undefined}
      tabIndex={onObjetivoHroe ? 0 : undefined}
      aria-label={onObjetivoHroe ? 'Atacar al héroe rival' : undefined}
      onClick={onObjetivoHroe}
      onKeyDown={
        onObjetivoHroe
          ? (evento) => {
              if (evento.key === 'Enter' || evento.key === ' ') {
                evento.preventDefault()
                onObjetivoHroe()
              }
            }
          : undefined
      }
    >
      {figura && (
        <span
          className="fig-heroe"
          aria-hidden="true"
          dangerouslySetInnerHTML={{ __html: figura }}
        />
      )}
      <b>{lado.nombre}</b>
      <span className="vida">
        ♥ {lado.hp}
        {esJugador && lado.hp > lado.mx && (
          <small title="Vida temporal: se pierde al terminar el combate">
            {' '}
            (+{lado.hp - lado.mx} temp.)
          </small>
        )}
        {danoFlotante != null && danoFlotante > 0 && (
          <span className="danio-flotante" aria-hidden="true">
            −{danoFlotante}
          </span>
        )}
      </span>
      <span className="escudo">◈ {lado.sh}</span>
      <span className="qi">
        Qi {lado.qi}
        {esJugador ? `/${lado.mq}` : ''}
      </span>
      {lado.bo && <span className="marca">Intención de Espada</span>}
      {lado.atkb > 0 && (
        <span className="escudo" title="Bonus de ataque (equipo/efectos)">
          ⚔+{lado.atkb}
        </span>
      )}
      {lado.salvavidas && (
        <span
          className="escudo"
          title="Talismán, píldora de inmortalidad o artefacto"
        >
          ☠ salvavidas
        </span>
      )}
      <span className="mano-info">mano {lado.mano.length}</span>
      {onVerMazo ? (
        <button
          type="button"
          className="pila-info"
          onClick={onVerMazo}
          title="Ver mazo"
        >
          mazo {lado.mazo}
        </button>
      ) : (
        <span className="mazo-info">mazo {lado.mazo}</span>
      )}
      {lado.vacio.length > 0 &&
        (onVerVacio ? (
          <button
            type="button"
            className="pila-info"
            onClick={onVerVacio}
            title="Ver Agujero Negro (descartes)"
          >
            vacío {lado.vacio.length}
          </button>
      ) : (
        <span className="vacio-info">vacío {lado.vacio.length}</span>
      ))}
    </div>
  )
}

export default function Combate({
  slot,
  indiceEnemigo,
  snapshot,
  narrativa,
  onSnapshot,
  onSalir,
  onMorir,
}: Props) {
  const [fase, setFase] = useState<'intro' | 'combate'>('intro')
  const [intro, setIntro] = useState<{
    enemigo: EnemigoResumen
    historia: string
  } | null>(null)
  const [pildoras, setPildoras] = useState<PildoraResumen[]>([])
  const [eqp, setEqp] = useState<string[]>([])
  const [eqpB, setEqpB] = useState<string[]>([])
  const [iniciando, setIniciando] = useState(false)
  const [estado, setEstado] = useState<EstadoCombate | null>(null)
  const [campaña, setCampaña] = useState<EventoCampana[]>([])
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [selMano, setSelMano] = useState<number | null>(null)
  const [selTablero, setSelTablero] = useState<number | null>(null)
  /** `'e'` = objetivo rival (`td`), `'a'` = aliado propio (`bf`). */
  const [pendienteObjetivo, setPendienteObjetivo] = useState<'e' | 'a' | null>(
    null,
  )
  const [confirmarFin, setConfirmarFin] = useState(false)
  /** Log de combate plegado (botón en la esquina). */
  const [logAbierto, setLogAbierto] = useState(false)
  /** Visor de pila: `'mazo'` | `'vacio'` | null. */
  const [visorPila, setVisorPila] = useState<'mazo' | 'vacio' | null>(null)
  /** Visor de la bolsa de combate (píldoras cargadas para el duelo). */
  const [visorBolsa, setVisorBolsa] = useState(false)
  /** Zoom lateral: carta ampliada al pasar el ratón (`#zoom` del monolito). */
  const [zoom, setZoom] = useState<CartaCombate | null>(null)
  /** Catálogo de cartas para nombrar las recompensas (`C` del monolito). */
  const [cartasCatalogo, setCartasCatalogo] = useState<
    Map<string, CartaResumen>
  >(new Map())
  /** Recompensa ya reclamada en esta victoria (índice elegido). */
  const [reclamada, setReclamada] = useState<{ nombre: string; rareza: string } | null>(
    null,
  )
  const [reclamando, setReclamando] = useState(false)
  /** Emboscada pendiente tras reclamar (`amb` del monolito). */
  const [emboscada, setEmboscada] = useState<{ boticario: boolean } | null>(
    null,
  )
  /** Flash de daño en las barras: qué lado y cuánto (`−N` flotante). */
  const [golpe, setGolpe] = useState<{ quien: 'e' | 'p'; dano: number } | null>(
    null,
  )
  const hpAnterior = useRef<{ e: number; p: number } | null>(null)
  const habíaEventoMapa = useRef(false)

  const aplicar = useCallback((resultado: ResultadoCombate) => {
    setEstado(resultado.combate)
    if (resultado.campaña?.length) setCampaña(resultado.campaña)
  }, [])

  const refrescarPartida = useCallback(async () => {
    try {
      const partida = await api.obtenerPartida(slot)
      if (partida.snapshot) onSnapshot(partida.snapshot)
    } catch {
      /* el snapshot se refresca al salir si falla */
    }
  }, [slot, onSnapshot])

  /** Recarga del combate activo tras un F5 (`GET …/combate`). */
  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const respuesta = await api.obtenerCombate(slot)
        if (!vigente || !respuesta?.combate?.activo) return
        aplicar({ slot, combate: respuesta.combate, campaña: [] })
        setFase('combate')
      } catch {
        /* sin combate activo: se muestra la intro */
      }
    })()
    return () => {
      vigente = false
    }
  }, [slot, aplicar])

  /** Carga de la intro: ficha del enemigo + catálogo de píldoras y cartas. */
  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [lista, catalogo, cartas] = await Promise.all([
          api.listarEnemigos(),
          api.obtenerAlquimia(),
          api.listarCartas(),
        ])
        if (!vigente) return
        const enemigo = lista[indiceEnemigo]
        if (!enemigo) {
          setError(`Enemigo desconocido (#${indiceEnemigo})`)
          return
        }
        const historia =
          enemigo.historia ||
          narrativa?.textos_intro_nivel[enemigo.indice_nivel] ||
          ''
        setIntro({ enemigo, historia })
        setPildoras(catalogo.pildoras)
        setCartasCatalogo(
          new Map(cartas.map((c) => [c.identificador, c])),
        )
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [indiceEnemigo, narrativa])

  /** Flash de daño: detecta caídas de vida en ambos lados (`hurt`). */
  useEffect(() => {
    if (!estado?.activo) return
    const actual = { e: estado.enemigo.hp, p: estado.jugador.hp }
    const anterior = hpAnterior.current
    hpAnterior.current = actual
    if (!anterior) return
    if (actual.e < anterior.e) {
      setGolpe({ quien: 'e', dano: anterior.e - actual.e })
    } else if (actual.p < anterior.p) {
      setGolpe({ quien: 'p', dano: anterior.p - actual.p })
    }
  }, [estado])

  /** Campanilla al aparecer un evento de mapa (`ding` de `turnP`). */
  useEffect(() => {
    if (!estado) return
    const hayEvento = estado.ev !== null
    if (hayEvento && !habíaEventoMapa.current) ding()
    habíaEventoMapa.current = hayEvento
  }, [estado])

  useEffect(() => {
    if (!golpe) return
    const temporizador = setTimeout(() => setGolpe(null), 650)
    return () => clearTimeout(temporizador)
  }, [golpe])

  const alternarInicio = (k: string) => {
    setEqp((prev) =>
      prev.includes(k)
        ? prev.filter((x) => x !== k)
        : prev.length < MAX_INICIO
          ? [...prev, k]
          : prev,
    )
  }

  const alternarBolsa = (k: string) => {
    setEqpB((prev) =>
      prev.includes(k)
        ? prev.filter((x) => x !== k)
        : prev.length < MAX_BOLSA
          ? [...prev, k]
          : prev,
    )
  }

  const iniciar = async () => {
    if (iniciando) return
    setIniciando(true)
    setError(null)
    try {
      const resultado = await api.iniciarCombate(slot, indiceEnemigo, eqp, eqpB)
      aplicar(resultado)
      setFase('combate')
      await refrescarPartida()
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    } finally {
      setIniciando(false)
    }
  }

  const recargarEstado = useCallback(async () => {
    try {
      const resultado = await api.obtenerCombate(slot)
      if (!resultado.combate.activo) {
        // Sin sesión en el servidor (cierre, reinicio del backend, combate
        // abandonado en otra pestaña): se vuelve a la intro en vez de dejar
        // el tablero congelado en «Cargando…».
        setEstado(null)
        setFase('intro')
        return
      }
      setEstado(resultado.combate)
    } catch (errorDeLlamada) {
      setError(mensajeDe(errorDeLlamada))
    }
  }, [slot])

  const ejecutar = useCallback(
    async (accion: () => Promise<ResultadoCombate>) => {
      if (ocupado) return
      setOcupado(true)
      setError(null)
      try {
        const resultado = await accion()
        aplicar(resultado)
        if (resultado.campaña?.length) {
          setCampaña(resultado.campaña)
          await refrescarPartida()
        }
      } catch (errorDeLlamada) {
        if (
          errorDeLlamada instanceof ErrorApi &&
          errorDeLlamada.codigo === 'sin_combate'
        ) {
          setConfirmarFin(false)
          await recargarEstado()
          setError(
            'El combate ya no está en curso en el servidor. Pulsa «Combatir» para empezarlo de nuevo.',
          )
        } else {
          setError(mensajeDe(errorDeLlamada))
        }
      } finally {
        setOcupado(false)
        setSelMano(null)
        setSelTablero(null)
        setPendienteObjetivo(null)
      }
    },
    [ocupado, aplicar, refrescarPartida, recargarEstado],
  )

  const cancelarSeleccion = () => {
    setSelMano(null)
    setPendienteObjetivo(null)
  }

  /** `pl` de js/07-campamento.js:111: juega o pide objetivo (td/bf). */
  const jugar = (indice: number) => {
    if (!estado || estado.fin || estado.lock) return
    if (estado.ed > 0 || estado.vp_n > 0 || estado.ev || ocupado) return
    const carta = estado.jugador.mano[indice]
    if (!carta || carta.coste > estado.jugador.qi) return
    if (selMano === indice) {
      cancelarSeleccion()
      return
    }
    const objetivo:
      | 'e'
      | 'a'
      | null =
      carta.dano_criatura !== null && estado.enemigo.tablero.length > 0
        ? 'e'
        : carta.mejora_aliada !== null && estado.jugador.tablero.length > 0
          ? 'a'
          : null
    if (objetivo) {
      setSelMano(indice)
      setPendienteObjetivo(objetivo)
      return
    }
    void ejecutar(() => api.jugarCartaCombate(slot, indice))
  }

  const jugarConObjetivo = (indice: number, objetivo: number) => {
    void ejecutar(() => api.jugarCartaCombate(slot, indice, objetivo))
  }

  /** `go` de js/07-campamento.js:118 (provocar incluido). */
  const atacar = (objetivo: number) => {
    if (selTablero === null || !estado) return
    const atacante = estado.jugador.tablero[selTablero]
    if (!atacante?.lista) return
    const provocar = estado.enemigo.tablero.some((c) => c.provocar)
    if (
      provocar &&
      objetivo >= 0 &&
      !estado.enemigo.tablero[objetivo]?.provocar
    ) {
      setError('Debes atacar primero a una criatura con Provocar.')
      return
    }
    void ejecutar(() => api.atacarCombate(slot, selTablero, objetivo))
  }

  const activar = (indice: number) => {
    void ejecutar(() => api.activarHabilidad(slot, indice))
  }

  const finTurno = (forzar: boolean) => {
    setConfirmarFin(false)
    void ejecutar(async () => {
      try {
        return await api.terminarTurno(slot, forzar)
      } catch (errorDeLlamada) {
        if (
          errorDeLlamada instanceof ErrorApi &&
          (errorDeLlamada.codigo === 'cierre_todavia_actua' ||
            errorDeLlamada.codigo === 'cierre_exceso_mano')
        ) {
          await recargarEstado()
          if (errorDeLlamada.codigo === 'cierre_todavia_actua') {
            setConfirmarFin(true)
          }
        }
        throw errorDeLlamada
      }
    })
  }

  /** Botón «Terminar turno»: aviso EC en cliente (`endT`). */
  const pedirFinTurno = () => {
    if (!estado || estado.fin || estado.lock || ocupado) return
    if (estado.ed > 0 || estado.vp_n > 0 || estado.ev) return
    if (puedeSeguirActuando(estado.jugador)) {
      setConfirmarFin(true)
      return
    }
    finTurno(false)
  }

  const descartarExceso = (indice: number) => {
    void ejecutar(() => api.descartarExceso(slot, indice))
  }

  const cancelarExceso = () => {
    void ejecutar(() => api.cancelarDescartarExceso(slot))
  }

  const elegirVacio = (indice: number) => {
    void ejecutar(() => api.elegirVacio(slot, indice))
  }

  const cancelarVacio = () => {
    void ejecutar(() => api.cancelarVacio(slot))
  }

  const resolverEvento = (opcion: number) => {
    void ejecutar(() => api.resolverEventoCombate(slot, opcion))
  }

  const usarPildora = (pildora: string) => {
    void ejecutar(() => api.usarPildoraCombate(slot, pildora))
  }

  const abandonar = () => {
    void ejecutar(async () => {
      const resultado = await api.abandonarCombate(slot)
      await refrescarPartida()
      return resultado
    })
  }

  /** `claim` de js/06-contenido.js:206: elige UNA recompensa. */
  const reclamar = (indice: number) => {
    if (reclamada || reclamando) return
    setReclamando(true)
    setError(null)
    void (async () => {
      try {
        const resultado = await api.reclamarRecompensa(slot, indice)
        const carta = cartasCatalogo.get(resultado.carta)
        setReclamada({
          nombre: carta?.nombre ?? resultado.carta,
          rareza: carta
            ? (NOMBRE_RAREZA[carta.rareza] ?? '—')
            : '—',
        })
        setEmboscada(resultado.emboscada ?? null)
        await refrescarPartida()
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      } finally {
        setReclamando(false)
      }
    })()
  }

  /** `begin(amb.o)` del popup de emboscada (js/06-contenido.js:201). */
  const entrarEmboscada = () => {
    if (ocupado) return
    setOcupado(true)
    setError(null)
    void (async () => {
      try {
        setCampaña([])
        setReclamada(null)
        setEmboscada(null)
        const resultado = await api.iniciarEmboscada(slot)
        aplicar(resultado)
        setFase('combate')
        await refrescarPartida()
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      } finally {
        setOcupado(false)
      }
    })()
  }

  /** `amb=null;render()` del botón Huir (js/06-contenido.js:201). */
  const huirEmboscada = () => {
    if (ocupado) return
    setOcupado(true)
    setError(null)
    void (async () => {
      try {
        await api.huirEmboscada(slot)
        setEmboscada(null)
        await refrescarPartida()
      } catch (errorDeLlamada) {
        setError(mensajeDe(errorDeLlamada))
      } finally {
        setOcupado(false)
      }
    })()
  }

  /* ---------- Intro (storyHTML) ---------- */

  if (fase === 'intro') {
    if (error && !intro) {
      return (
        <section className="pantalla combate" aria-label="Combate">
          <h1>Combate</h1>
          <div className="banner-error" role="alert">
            {error}
          </div>
          <button type="button" onClick={onSalir}>
            Volver al campamento
          </button>
        </section>
      )
    }
    if (!intro) {
      return (
        <section className="pantalla combate" aria-label="Combate">
          <h1>Combate</h1>
          <p>Cargando…</p>
        </section>
      )
    }

    const { enemigo, historia } = intro
    const reino = snapshot.realm
    const vidaEsc = enemigo.vida + VIDA_POR_REINO * reino
    const factorNivel =
      enemigo.origen === 'nivel' ? enemigo.indice_nivel : 0
    const cielos = narrativa?.gradientes_nivel ?? []
    const gradiente = cielos[factorNivel] ?? cielos[0]
    const dano = (1 + 0.03 * reino) * (1 + 0.02 * factorNivel)
    const stock = snapshot.pil
    const inicioDisponibles = pildoras.filter(
      (p) => !p.es_combate && (stock[p.identificador] ?? 0) > 0,
    )
    const bolsaDisponibles = pildoras.filter(
      (p) => p.es_combate && (stock[p.identificador] ?? 0) > 0,
    )

    return (
      <section className="pantalla combate intro-combate" aria-label="Intro del combate">
        {gradiente && (
          <div
            className="scene-combate"
            aria-hidden="true"
            dangerouslySetInnerHTML={{
              __html: escenaFondo(gradiente, factorNivel),
            }}
          />
        )}
        {error && (
          <div className="banner-error" role="alert">
            {error}
          </div>
        )}
        <div className="ficha-intro">
          <div className="ficha-enemigo">
            <span
              aria-hidden="true"
              dangerouslySetInnerHTML={{
                __html: figuraSecta(
                  enemigo.secta,
                  enemigo.dificultad >= 4,
                  enemigo.dificultad % 4,
                ),
              }}
            />
            <b>{enemigo.nombre_enemigo}</b>
            <em style={{ color: COLOR_DIFICULTAD[enemigo.dificultad] ?? '#aab8b2' }}>
              {DIFICULTADES[enemigo.dificultad] ?? '—'}
            </em>
            <small>
              {vidaEsc} vida. Daño ×{dano.toFixed(1)}.{' '}
              {enemigo.texto_habilidades}
            </small>
          </div>
          <div className="detalle-intro">
            <h2>{enemigo.nombre_nivel}</h2>
            {historia && <p>{historia}</p>}
            <p className="frase-inicio">
              {enemigo.nombre_enemigo}: «{enemigo.frase_inicio}»
            </p>
            <p className="aviso-muerte">
              ☠ Muerte permanente: si mueres, tu cultivador muere para
              siempre.
            </p>

            {inicioDisponibles.length > 0 && (
              <p className="pildoras-inicio">
                Píldoras de inicio (máx. {MAX_INICIO}, se usan al empezar):
                <br />
                {inicioDisponibles.map((p) => (
                  <button
                    key={p.identificador}
                    type="button"
                    className={`chip${eqp.includes(p.identificador) ? ' on' : ''}`}
                    title={p.efecto}
                    onClick={() => alternarInicio(p.identificador)}
                  >
                    <PillIco icono={p.icono} />
                    {p.nombre} x{stock[p.identificador]}
                  </button>
                ))}
              </p>
            )}

            {bolsaDisponibles.length > 0 && (
              <p className="bolsa-inicio">
                🎒 Bolsa de combate (máx. {MAX_BOLSA}; durante la partida
                podrás usar {MAX_USOS_BOLSA} píldoras):
                <br />
                {bolsaDisponibles.map((p) => (
                  <button
                    key={p.identificador}
                    type="button"
                    className={`chip${eqpB.includes(p.identificador) ? ' on' : ''}`}
                    title={p.efecto}
                    onClick={() => alternarBolsa(p.identificador)}
                  >
                    <PillIco icono={p.icono} />
                    {p.nombre} x{stock[p.identificador]}
                  </button>
                ))}
              </p>
            )}

            <div className="acciones-modal">
              <button
                type="button"
                className="principal"
                onClick={() => void iniciar()}
                disabled={iniciando}
              >
                {iniciando ? 'Preparando…' : 'Combatir'}
              </button>
              <button type="button" onClick={onSalir}>
                Volver
              </button>
            </div>
          </div>
        </div>
      </section>
    )
  }

  /* ---------- Combate ---------- */

  if (error && !estado) {
    return (
      <section className="pantalla combate" aria-label="Combate">
        <h1>Combate</h1>
        <div className="banner-error" role="alert">
          {error}
        </div>
        <button type="button" onClick={onSalir}>
          Volver al campamento
        </button>
      </section>
    )
  }

  if (!estado || !estado.activo) {
    return (
      <section className="pantalla combate" aria-label="Combate">
        <h1>Combate</h1>
        <p>Cargando…</p>
      </section>
    )
  }

  const P = estado.jugador
  const E = estado.enemigo
  const fin = estado.fin
  const terminado = fin !== ''
  const victoria = fin === 'w'
  const derrota = fin === 'l'
  const modalAbierto =
    estado.ed > 0 || estado.vp_n > 0 || estado.ev !== null || confirmarFin
  const puedeJugar = !terminado && !estado.lock && !modalAbierto && !ocupado
  /** `bub`: la última frase del rival (log con su nombre). */
  const ultimaLinea = estado.logs[estado.logs.length - 1] ?? ''
  const burbuja = ultimaLinea.startsWith(`<b>${E.nombre}:</b>`)
    ? ultimaLinea
    : ''

  /** Zoom lateral al pasar el ratón sobre una carta (`zc` de js/07:123). */
  const verZoom = (carta: CartaCombate) => () => setZoom(carta)
  const ocultarZoom = () => setZoom(null)

  return (
    <section className="pantalla combate" aria-label="Combate">
      {error && (
        <div className="banner-error combate-error" role="alert">
          {error}
        </div>
      )}

      {/* Fila 1: información del rival a la izquierda… */}
      <aside className="lateral lateral-enemigo">
        <BarraLado
          lado={E}
          esJugador={false}
          figura={
            intro?.enemigo
              ? figuraSecta(
                  intro.enemigo.secta,
                  intro.enemigo.dificultad >= 4,
                  intro.enemigo.dificultad % 4,
                )
              : undefined
          }
          seleccionandoAtaque={selTablero !== null}
          onObjetivoHroe={selTablero !== null ? () => atacar(-1) : undefined}
          golpe={golpe?.quien === 'e'}
          danoFlotante={golpe?.quien === 'e' ? golpe.dano : null}
        />
        <BanderaFormacion lado={E} />
      </aside>

      {/* …y sus cartas jugadas a la derecha. */}
      <div className="zona-rival">
        {burbuja && (
          <p className="burbuja" aria-hidden="true">
            <span dangerouslySetInnerHTML={{ __html: burbuja }} />
          </p>
        )}

        <div
          className={`tablero rival${selTablero !== null || pendienteObjetivo === 'e' ? ' seleccionable' : ''}`}
          role="list"
          aria-label="Tablero enemigo"
        >
          {E.tablero.map((carta, i) => (
            <div
              key={`${carta.id}-${i}`}
              role="listitem"
              onMouseEnter={verZoom(carta)}
              onMouseLeave={ocultarZoom}
            >
              <Carta
                carta={carta}
                bonusFormacion={(E.fm?.pa ?? 0) + E.opa || undefined}
                onClick={
                  selTablero !== null
                    ? () => atacar(i)
                    : pendienteObjetivo === 'e' && selMano !== null
                      ? () => jugarConObjetivo(selMano, i)
                      : undefined
                }
              />
            </div>
          ))}
          <CasillasHuecas n={5 - E.tablero.length} />
        </div>
      </div>

      {/* Fila 2: las cartas del jugador a la izquierda… */}
      <div className="zona-propia">
        <div
          className={`tablero propio${pendienteObjetivo === 'a' ? ' seleccionable' : ''}`}
          role="list"
          aria-label="Tablero propio"
        >
          {P.tablero.map((carta, i) => (
            <div
              key={`${carta.id}-${i}`}
              className="celda-tablero"
              role="listitem"
              onMouseEnter={verZoom(carta)}
              onMouseLeave={ocultarZoom}
            >
              <Carta
                carta={carta}
                seleccionada={selTablero === i}
                bonusFormacion={(P.fm?.pa ?? 0) + P.opa || undefined}
                onClick={
                  pendienteObjetivo === 'a' && selMano !== null
                    ? () => jugarConObjetivo(selMano, i)
                    : carta.lista && puedeJugar
                      ? () => setSelTablero(selTablero === i ? null : i)
                      : undefined
                }
              />
              <div className="acciones-celda">
                {carta.lista && !terminado && !estado.lock && (
                  <button
                    type="button"
                    className="chip atacar"
                    onClick={() => setSelTablero(selTablero === i ? null : i)}
                    disabled={ocupado || pendienteObjetivo === 'a'}
                  >
                    {selTablero === i ? 'Cancelar' : 'Atacar'}
                  </button>
                )}
                {carta.habilidad && !carta.usada && !terminado && (
                  <button
                    type="button"
                    className="chip activar"
                    onClick={() => activar(i)}
                    disabled={ocupado || estado.lock}
                    title={carta.habilidad.descripcion}
                  >
                    Activa ({carta.habilidad.coste} Qi)
                  </button>
                )}
              </div>
            </div>
          ))}
          <CasillasHuecas n={5 - P.tablero.length} />
        </div>
      </div>

      {/* Mano, pistas y píldoras del jugador (ancho completo bajo el tablero). */}
      <div className="zona-mano">
        {pendienteObjetivo === 'e' && selMano !== null && (
          <p className="pista-objetivo" role="status">
            Elige un objetivo en el tablero enemigo para «
            {P.mano[selMano]?.nombre ?? 'la carta'}» (pulsa la carta otra vez
            para cancelar).
          </p>
        )}

        {pendienteObjetivo === 'a' && selMano !== null && (
          <p className="pista-objetivo" role="status">
            Elige una criatura aliada para «{P.mano[selMano]?.nombre ?? 'la carta'}
            » (pulsa la carta otra vez para cancelar).
          </p>
        )}

        {selTablero !== null && (
          <p className="pista-objetivo" role="status">
            Elige un objetivo en el tablero enemigo o toca su héroe para
            atacarlo (pulsa la criatura otra vez para cancelar).
          </p>
        )}

        <div className="mano" role="list" aria-label="Mano">
          {P.mano.map((carta, i) => (
            <div
              key={`${carta.id}-${i}`}
              role="listitem"
              onMouseEnter={verZoom(carta)}
              onMouseLeave={ocultarZoom}
            >
              <Carta
                carta={carta}
                seleccionada={selMano === i}
                no={carta.coste > P.qi || !puedeJugar}
                onClick={puedeJugar ? () => jugar(i) : undefined}
              />
            </div>
          ))}
          {P.mano.length === 0 && <p className="tablero-vacio">Mano vacía</p>}
        </div>

        {/* Acciones del combate en fila bajo la mano. */}
        <div className="acciones-combate">
          <button
            type="button"
            className="principal"
            onClick={pedirFinTurno}
            disabled={!puedeJugar}
          >
            Terminar turno
          </button>
          <button
            type="button"
            className="chip"
            onClick={() => setVisorBolsa(true)}
            title="Ver los elementos cargados para el duelo"
          >
            🎒 Bolsa ({P.pouch.length})
          </button>
          <button
            type="button"
            className="chip"
            onClick={() => setLogAbierto((v) => !v)}
            aria-expanded={logAbierto}
            aria-controls="log-combate-contenido"
            title={logAbierto ? 'Ocultar registro' : 'Ver registro'}
          >
            {logAbierto
              ? 'Ocultar registro ▾'
              : `Registro (${estado.logs.length}) ▸`}
          </button>
          <button
            type="button"
            className="peligro"
            onClick={abandonar}
            disabled={terminado || ocupado}
          >
            Abandonar
          </button>
        </div>

        {P.pouch.length > 0 && (
          <div className="bolsa-combate" aria-label="Bolsa de píldoras">
            <b>🎒 Bolsa de píldoras</b> (usos: {P.usos}/{MAX_USOS_BOLSA})
            {P.pouch.map((k) => {
              const p = pildoras.find((x) => x.identificador === k)
              const stock = estado.pildoras_stock[k] ?? 0
              const habilitada =
                puedeJugar && P.usos < MAX_USOS_BOLSA && stock > 0
              return (
                <button
                  key={k}
                  type="button"
                  className="chip"
                  disabled={!habilitada}
                  title={p?.efecto ?? k}
                  onClick={() => usarPildora(k)}
                >
                  {p ? <PillIco icono={p.icono} /> : null}
                  {p?.nombre ?? k} x{stock}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* …y la información del jugador a la derecha (solo stats). */}
      <aside className="lateral lateral-jugador">
        <BarraLado
          lado={P}
          esJugador
          figura={figuraSecta(snapshot.sect, false, 0)}
          golpe={golpe?.quien === 'p'}
          danoFlotante={golpe?.quien === 'p' ? golpe.dano : null}
          onVerMazo={() => setVisorPila('mazo')}
          onVerVacio={P.vacio.length > 0 ? () => setVisorPila('vacio') : undefined}
        />
        <BanderaFormacion lado={P} />
      </aside>

      {/* Zoom lateral (`#zoom` de js/07-campamento.js:123). */}
      <aside className="zoom-combate" aria-hidden="true">
        {zoom ? (
          <Carta carta={zoom} />
        ) : (
          <p className="zph">
            Pasa el cursor sobre una carta
            <br />
            para verla en grande
          </p>
        )}
      </aside>

      {/* Registro de combate: panel flotante abierto desde la columna del jugador. */}
      {logAbierto && (
        <div
          className="log-combate abierto"
          id="log-combate-contenido"
          aria-live="polite"
        >
          {estado.logs
            .slice()
            .reverse()
            .slice(0, 6)
            .map((linea, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <p key={i} dangerouslySetInnerHTML={{ __html: linea }} />
            ))}
          {estado.logs.length === 0 && (
            <p className="tablero-vacio">Sin acciones todavía.</p>
          )}
        </div>
      )}

      {/* Modal: evento de mapa (`EV` de js/06-contenido.js:213) */}
      {estado.ev && !terminado && (
        <div className="modal-combate" role="dialog" aria-label="Evento de mapa">
          <div className="evb">¡Evento aleatorio!</div>
          <h2>{estado.ev.nombre}</h2>
          <p>{estado.ev.texto}</p>
          <div className="acciones-modal">
            {estado.ev.opciones.map((texto, i) => (
              <button
                key={texto}
                type="button"
                onClick={() => resolverEvento(i)}
                disabled={ocupado}
              >
                {texto}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Modal: exceso de mano (ED) */}
      {estado.ed > 0 && !terminado && (
        <div className="modal-combate" role="dialog" aria-label="Exceso de mano">
          <div className="evb">Mano excedida ({P.mano.length}/{TAMANO_MANO})</div>
          <h2>
            Descarta {estado.ed} carta{estado.ed > 1 ? 's' : ''}
          </h2>
          <p className="q">
            Las cartas de efecto te dieron más de {TAMANO_MANO}, pero al
            terminar el turno solo puedes conservar {TAMANO_MANO}. Las
            descartadas caen al Agujero Negro.
          </p>
          <div className="mano modal-mano">
            {P.mano.map((carta, i) => (
              <div key={`${carta.id}-${i}`}>
                <Carta carta={carta} onClick={() => descartarExceso(i)} />
              </div>
            ))}
          </div>
          <button type="button" onClick={cancelarExceso} disabled={ocupado}>
            Volver y jugar más cartas
          </button>
        </div>
      )}

      {/* Modal: recuperar del Agujero Negro (VP) */}
      {estado.vp_n > 0 && !terminado && (
        <div className="modal-combate" role="dialog" aria-label="Agujero Negro">
          <div className="evb">Agujero Negro</div>
          <h2>
            Recupera {estado.vp_n} carta{estado.vp_n > 1 ? 's' : ''}
          </h2>
          <p className="q">
            Elige del Agujero Negro. Mano: {P.mano.length}/{TAMANO_MANO}.
          </p>
          <div className="mano modal-mano">
            {P.vacio.map((carta, i) => (
              <div key={`${carta.id}-${i}`}>
                <Carta carta={carta} onClick={() => elegirVacio(i)} />
              </div>
            ))}
            {P.vacio.length === 0 && <p>El vacío está vacío.</p>}
          </div>
          <button type="button" onClick={cancelarVacio} disabled={ocupado}>
            Terminar selección
          </button>
        </div>
      )}

      {/* Modal: confirmar fin de turno (EC, v44) */}
      {confirmarFin && !terminado && (
        <div className="modal-combate" role="dialog" aria-label="Confirmar fin">
          <div className="evb ecb">¡Aún puedes jugar!</div>
          <h2>¿Terminar el turno?</h2>
          <p className="q">
            Aún tienes cartas que puedes activar. ¿Estás seguro de que deseas
            terminar tu turno?
          </p>
          <div className="ec-list">
            Qi disponible: <b>{P.qi}</b>
            {cartasJugables(P).length > 0 && (
              <>
                <br />
                Cartas jugables ({cartasJugables(P).length}):{' '}
                <b>{cartasJugables(P).slice(0, 4).map((c) => c.nombre).join(', ')}
                {cartasJugables(P).length > 4 ? '…' : ''}</b>
              </>
            )}
            {habilidadesListas(P).length > 0 && (
              <>
                <br />
                Habilidades listas ({habilidadesListas(P).length}):{' '}
                <b>
                  {habilidadesListas(P).slice(0, 4).map((c) => c.nombre).join(', ')}
                  {habilidadesListas(P).length > 4 ? '…' : ''}
                </b>
              </>
            )}
          </div>
          <div className="acciones-modal">
            <button
              type="button"
              onClick={() => setConfirmarFin(false)}
            >
              Seguir jugando
            </button>
            <button
              type="button"
              className="principal"
              onClick={() => finTurno(true)}
            >
              Sí, terminar turno
            </button>
          </div>
        </div>
      )}

      {/* Modal: emboscada pendiente tras reclamar (`amb && over=='w'`). */}
      {terminado && victoria && emboscada && (
        <div
          className="modal-combate emboscada"
          role="dialog"
          aria-label="¡Emboscada!"
        >
          <div className="evb">¡Emboscada!</div>
          <h2>
            {emboscada.boticario
              ? 'Un boticario te intercepta'
              : 'Un alquimista errante te sigue'}
          </h2>
          <p className="q">
            {emboscada.boticario
              ? 'Huele a hierbas y a humo. Dice conocer la receta de una píldora de recuperación (o llevar una ya hecha). ¿Aceptas el combate?'
              : 'Dice guardar una receta secreta. ¿Aceptas el combate secreto?'}
          </p>
          <button
            type="button"
            className="principal"
            disabled={ocupado}
            onClick={entrarEmboscada}
          >
            Combatir (puede ocultar una receta)
          </button>
          <button
            type="button"
            disabled={ocupado}
            onClick={huirEmboscada}
          >
            Huir
          </button>
          {error && (
            <div className="banner-error" role="alert">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Modal: fin de combate (victoria / derrota / escape) */}
      {terminado && !emboscada && (
        <div className="modal-combate fin" role="dialog" aria-label="Fin del combate">
          <h2>
            {victoria
              ? '¡Victoria!'
              : derrota
                ? 'Has caído…'
                : 'Combate terminado'}
          </h2>
          {victoria && (
            <>
              {(() => {
                const victoriaEvento = campaña.find(
                  (evento) => evento.tipo === 'victoria',
                )
                const recompensas = (victoriaEvento?.recompensas ??
                  []) as string[]
                if (!recompensas.length) return null
                if (reclamada) {
                  return (
                    <p className="q recompensa-obtenida">
                      🃏 Carta añadida a tu colección: <b>{reclamada.nombre}</b>{' '}
                      ({reclamada.rareza}).
                    </p>
                  )
                }
                return (
                  <>
                    <p className="q">Elige una carta para tu mazo:</p>
                    <div className="recompensas-modal">
                      {recompensas.map((id, i) => {
                        const info = cartasCatalogo.get(id)
                        const color =
                          COLOR_RAREZA[info?.rareza ?? 0] ?? '#aab8b2'
                        return (
                          <button
                            key={`${id}-${i}`}
                            type="button"
                            className="recompensa-carta"
                            style={{ borderColor: color, color }}
                            disabled={reclamando}
                            onClick={() => reclamar(i)}
                            title={
                              info
                                ? `${info.nombre} — ${NOMBRE_RAREZA[info.rareza] ?? ''}`
                                : id
                            }
                          >
                            <b>{info?.nombre ?? id}</b>
                            <span
                              className="recompensa-arte"
                              aria-hidden="true"
                              dangerouslySetInnerHTML={{ __html: arteCarta(id) }}
                            />
                            <small>
                              {info
                                ? (NOMBRE_RAREZA[info.rareza] ?? '—')
                                : '—'}
                              {info ? ` · ${info.coste_qi} Qi` : ''}
                              {info?.tipo === 'C' &&
                              info.ataque !== null
                                ? ` · ${info.ataque}/${info.vida ?? '–'}`
                                : ''}
                            </small>
                            {info && info.descripcion.length > 0 && (
                              <small className="recompensa-desc">
                                {info.descripcion.join(' · ')}
                              </small>
                            )}
                            <small className="recompensa-elegir">
                              Elegir
                            </small>
                          </button>
                        )
                      })}
                    </div>
                  </>
                )
              })()}
              <ul className="resumen-campana">
                {campaña
                  .filter((evento) => evento.tipo === 'victoria')
                  .map((evento, i) => {
                    const materiales = (evento.materiales ?? {}) as Record<
                      string,
                      unknown
                    >
                    return (
                      <li key={i}>
                        <b>Materiales:</b> {String(materiales.h ?? 0)} hierbas ·{' '}
                        {String(materiales.n ?? 0)} núcleos ·{' '}
                        {String(materiales.p ?? 0)} polvo ·{' '}
                        {String(materiales.s ?? 0)} piedras
                        {evento.reliquia ? (
                          <>
                            <br />
                            <b>Reliquia:</b> {String(evento.reliquia)}
                          </>
                        ) : null}
                        {evento.mision_secundaria ? (
                          <>
                            <br />
                            <b>Misión:</b> {String(evento.mision_secundaria)}
                          </>
                        ) : null}
                        {evento.ascenso ? (
                          <>
                            <br />
                            <b>¡Ascendiste de reino!</b>
                          </>
                        ) : null}
                        {evento.jardin ? (
                          <>
                            <br />
                            <b>Jardín:</b>{' '}
                            {(() => {
                              const botin = evento.jardin as {
                                semillas?: Record<string, number>
                                semilla?: string | null
                                formacion?: string | null
                                materiales?: Record<string, number>
                              }
                              const partes: string[] = []
                              if (botin.semillas) {
                                for (const [id, n] of Object.entries(
                                  botin.semillas,
                                )) {
                                  partes.push(`${id} ×${n}`)
                                }
                              }
                              if (botin.semilla) partes.push(botin.semilla)
                              if (botin.formacion)
                                partes.push(botin.formacion)
                              if (botin.materiales) {
                                const m = botin.materiales
                                partes.push(
                                  `${m.h ?? 0} hierbas · ${m.n ?? 0} núcleos · ${m.p ?? 0} polvo`,
                                )
                              }
                              return partes.join(' · ') || '—'
                            })()}
                          </>
                        ) : null}
                      </li>
                    )
                  })}
              </ul>
            </>
          )}
          {derrota && (
            <p className="q">
              La muerte permanente reinicia el progreso: reino, colección,
              mazos y materiales. Las estadísticas (muertes, mejor racha) se
              conservan.
            </p>
          )}
          <button
            type="button"
            className="principal"
            onClick={() => {
              void (async () => {
                try {
                  await api.cerrarCombate(slot)
                } catch {
                  /* ya liberado */
                }
                await refrescarPartida()
                // Muerte: renacer vuelve al splash (`reborn()` del JS).
                if (derrota && onMorir) onMorir()
                else onSalir()
              })()
            }}
          >
            {derrota && onMorir ? 'Renacer como nuevo cultivador' : 'Continuar'}
          </button>
        </div>
      )}

      {/* Modal: visor de mazo / Agujero Negro (descartes). */}
      {visorPila && (
        <VisorPila
          titulo={visorPila === 'mazo' ? 'Tu mazo' : 'Agujero Negro (descartes)'}
          cartas={visorPila === 'mazo' ? P.cartas_mazo : P.vacio}
          onCerrar={() => setVisorPila(null)}
        />
      )}

      {/* Modal: bolsa de combate (elementos cargados para el duelo). */}
      {visorBolsa && (
        <div className="modal-combate" role="dialog" aria-label="Bolsa de combate">
          <div className="evb">🎒 Bolsa de combate</div>
          <p className="q">
            Elementos cargados para este duelo. Usos de bolsa: {P.usos}/
            {MAX_USOS_BOLSA}.
          </p>
          <div className="bolsa-lista">
            {P.pouch.map((k) => {
              const p = pildoras.find((x) => x.identificador === k)
              const stock = estado.pildoras_stock[k] ?? 0
              const habilitada = puedeJugar && P.usos < MAX_USOS_BOLSA && stock > 0
              return (
                <div key={k} className="bolsa-item">
                  {p ? <PillIco icono={p.icono} /> : null}
                  <span>
                    <b>{p?.nombre ?? k}</b> x{stock}
                    <br />
                    <small>{p?.efecto ?? k}</small>
                  </span>
                  <button
                    type="button"
                    className="chip"
                    disabled={!habilitada}
                    onClick={() => {
                      setVisorBolsa(false)
                      usarPildora(k)
                    }}
                  >
                    Usar
                  </button>
                </div>
              )
            })}
            {P.pouch.length === 0 && (
              <p className="tablero-vacio">
                No cargaste píldoras de bolsa para este duelo.
              </p>
            )}
          </div>
          <button type="button" onClick={() => setVisorBolsa(false)}>
            Cerrar
          </button>
        </div>
      )}
    </section>
  )
}
