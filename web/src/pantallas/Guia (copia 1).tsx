/** Guía del Sendero: secciones mecánicas del monolito + sectas y bestiario.

Port de `GS`/`GB` de js/08-efectos.js:116-129 (7 secciones: Introducción,
Cartas, Formaciones, Equipo, Mercado, Combate y salud, Otras mecánicas),
más las secciones React de siempre (Sectas y Bestiario). Los valores
dinámicos del monolito se fijan aquí con sus constantes exactas:
`HP_BASE`/`HP_PER_REALM` (js/06-contenido.js:224), `OVH` (js/02-motor.js:22),
`HM` (js/02-motor.js:12), `DM` (js/03-cartas-mercado.js:35), `RP`/`SELL`
(js/03-cartas-mercado.js:4,6), `TYN` (:12), `RN` (js/01-datos.js:39),
`MAXSK` (js/01-datos.js:301), `SLOTS`/`SLN` (js/06-contenido.js:65,
js/08-efectos.js:104).

Adaptaciones al front React: la lista de pestañas es la del shell actual
(sin Maznorras/Misiones/Equipo/Trajes/Bolsa), el Mercado SÍ confirma la
compra (como el override v47) y Formaciones/Runas se editan en el mazo.
*/

import { useEffect, useState } from 'react'
import { api, ErrorApi } from '../api/cliente'
import type { EnemigoResumen, SectaResumen } from '../api/tipos'

interface Props {
  sectas: SectaResumen[]
}

/** Constantes del monolito (citas en el docstring). */
const HP_BASE = 30
const HP_PER_REALM = 2
const OVH = 1.5
const HM = 5
const DM = 40
const MAXSK = 3
const RP = [6, 12, 24, 45, 90, 180]
const SELL = { h: 1, p: 2, n: 8 }
const TYN = ['Criatura', 'Técnica', 'Píldora', 'Formación', 'Runa']
const RN = ['Común', 'Poco común', 'Rara', 'Épica', 'Legendaria', 'Celestial']
const SLOTS = [
  'Cabeza',
  'Cuerpo',
  'Guantes',
  'Botas',
  'Reliquia',
  'Artefacto',
]
/** Pestañas del shell React (`PESTANAS` de App.tsx). */
const PESTANAS = [
  'Campaña',
  'Alquimia',
  'Mazos',
  'Mercado',
  'Gacha',
  'Guía',
]

/** `GS` de js/08-efectos.js:118. */
const GS: Array<[string, string, string]> = [
  ['int', '📜', 'Introducción'],
  ['car', '🃏', 'Cartas'],
  ['frm', '阵', 'Formaciones'],
  ['eq', '🛡', 'Equipo'],
  ['mer', '💎', 'Mercado'],
  ['cmb', '⚔', 'Combate y salud'],
  ['otr', '🧭', 'Otras mecánicas'],
]

function mensajeDe(errorDeLlamada: unknown): string {
  if (errorDeLlamada instanceof ErrorApi) return errorDeLlamada.message
  if (errorDeLlamada instanceof Error) return errorDeLlamada.message
  return 'Error inesperado'
}

export default function Guia({ sectas }: Props) {
  const [nombreDeCarta, setNombreDeCarta] = useState<Record<string, string>>({})
  const [enemigos, setEnemigos] = useState<EnemigoResumen[]>([])
  const [error, setError] = useState<string | null>(null)
  /** Sección activa de la guía (`gsec`). */
  const [seccion, setSeccion] = useState('int')

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const [cartas, listaEnemigos] = await Promise.all([
          api.listarCartas(),
          api.listarEnemigos(),
        ])
        if (!vigente) return
        setNombreDeCarta(
          Object.fromEntries(
            cartas.map((carta) => [carta.identificador, carta.nombre]),
          ),
        )
        setEnemigos(listaEnemigos)
      } catch (errorDeLlamada) {
        if (vigente) setError(mensajeDe(errorDeLlamada))
      }
    })()
    return () => {
      vigente = false
    }
  }, [])

  const campana = enemigos.filter((e) => e.origen === 'nivel')
  const niveles = Math.max(1, Math.ceil(campana.length / 6))

  /** Contenido de la sección activa (port de `GB`). */
  const contenido = (() => {
    switch (seccion) {
      case 'int':
        return (
          <>
            <h3>Objetivo</h3>
            <p>
              Eres Lin Yu, un cultivador que elige una secta (no se puede
              cambiar) y avanza por la campaña venciendo combates de cartas. Hay{' '}
              {niveles} niveles de 6 enemigos ({campana.length} victorias de
              campaña); el último jefe cierra la historia. Vencer por primera
              vez al jefe de un nivel te hace subir de reino.
            </p>
            <h3>La interfaz</h3>
            <ul>
              <li>
                <b>Pestañas</b> (arriba): {PESTANAS.join(', ')}.
              </li>
              <li>
                <b>Cabecera de Campaña</b>: reino, victorias, cartas obtenidas,
                Qi máximo y vida actual/máxima.
              </li>
              <li>
                <b>Mapa de la campaña</b>: elige un enemigo (el siguiente nivel
                se abre al vencer al jefe del anterior).
              </li>
            </ul>
            <h3>Recursos y estadísticas</h3>
            <ul>
              <li>
                <b>Piedras espirituales</b>: la moneda (Mercado).
              </li>
              <li>
                <b>Hierbas, núcleos y polvo de jade</b>: materiales para
                Alquimia y Herrería.
              </li>
              <li>
                <b>Vida</b>: {HP_BASE} + {HP_PER_REALM} por reino. No se
                recupera sola.
              </li>
              <li>
                <b>Qi</b>: se gasta para jugar cartas; empieza el combate en 1 y
                sube 1 por turno hasta tu máximo (6 + reino, tope 12, más el
                bono de equipo).
              </li>
              <li>
                <b>Escudo</b>: absorbe daño antes que la vida.
              </li>
            </ul>
          </>
        )
      case 'car':
        return (
          <>
            <h3>Glosario de efectos y palabras clave</h3>
            <p>
              Estas palabras resumen efectos de cartas. La descripción completa
              aparece en cada carta; aquí tienes una referencia rápida.
            </p>
            <div className="glk">
              <p>
                <b>Provocar:</b> el rival debe atacar primero a las criaturas
                con esta marca.
              </p>
              <p>
                <b>Ímpetu:</b> la criatura puede atacar el mismo turno en que
                entra.
              </p>
              <p>
                <b>Roba vida:</b> el daño que inflige cura a su dueño.
              </p>
              <p>
                <b>Crece:</b> gana el ataque indicado cada vez que ataca.
              </p>
              <p>
                <b>Último aliento:</b> activa su efecto al morir.
              </p>
              <p>
                <b>Al entrar:</b> activa su efecto al jugar la criatura.
              </p>
              <p>
                <b>Activa:</b> habilidad opcional de una criatura; cuesta Qi y
                se usa con el botón de rayo.
              </p>
              <p>
                <b>Congelar:</b> impide que la criatura afectada ataque durante
                el siguiente turno.
              </p>
              <p>
                <b>Renovar:</b> devuelve tu mano al mazo y roba la cantidad
                indicada.
              </p>
              <p>
                <b>Vacío:</b> el rival descarta cartas al azar.
              </p>
              <p>
                <b>Ciclo:</b> descarta tu mano y roba la misma cantidad.
              </p>
              <p>
                <b>Abismo:</b> recupera cartas del Agujero Negro a tu mano.
              </p>
              <p>
                <b>Samsara:</b> devuelve cartas del Agujero Negro a tu mazo.
              </p>
              <p>
                <b>Disipa:</b> destruye formaciones y runas rivales.
              </p>
              <p>
                <b>Bendición:</b> mejora una criatura aliada; si no hay, otorga
                3 de escudo.
              </p>
            </div>
            <h3>Tipos y rareza</h3>
            <p>
              Tipos: {TYN.join(', ')}. Rarezas: {RN.join(', ')}. Cada carta
              tiene un coste en Qi; las criaturas tienen Ataque/Vida.
            </p>
            <h3>Cómo obtenerlas</h3>
            <ul>
              <li>
                Tras ganar un combate eliges <b>1 de 3 cartas</b> (rareza hasta
                la indicada en el nodo del mapa).
              </li>
              <li>
                <b>Mercado</b>: comprar con piedras espirituales.
              </li>
              <li>
                <b>Alquimia</b>: forjar una carta al azar de la rareza elegida,
                o fusionar 3 copias en una de rareza superior (si no,
                desmantelar una copia da polvo de jade).
              </li>
              <li>
                <b>Reliquias</b> y cartas Celestiales: solo caen de jefes
                finales.
              </li>
            </ul>
            <p>
              Máximo <b>3 copias</b> de cada carta.
            </p>
            <h3>Consultarlas</h3>
            <ul>
              <li>
                En el Mercado, pulsa una carta para ver su detalle completo.
              </li>
              <li>
                En la pestaña Mazos tienes el editor y el detalle de cada
                carta, con su descripción de efectos.
              </li>
              <li>
                Insignias en las cartas: Provocar, Ímpetu, Roba vida, Crece,
                Último aliento, Al entrar, Activa, Congela, Renovar (pasa el
                cursor para leerlas).
              </li>
            </ul>
            <h3>Usarlas</h3>
            <ul>
              <li>
                En combate, pulsa una carta de tu mano para jugarla pagando su
                coste en Qi. Las técnicas con objetivo piden elegirlo después.
              </li>
              <li>
                Criaturas: máximo <b>5 en mesa</b>. Si juegas otra copia de una
                que ya está en juego, se <b>apila</b> sobre ella (sin ocupar
                casilla) hasta el nivel {MAXSK}.
              </li>
              <li>
                Mano: máximo <b>{HM}</b>. Si terminas el turno con más,
                descartas el exceso al Agujero Negro.
              </li>
              <li>
                Las cartas jugadas, descartadas o destruidas van al Agujero
                Negro y no vuelven solas al mazo.
              </li>
              <li>
                Mazo propio: {DM} cartas, ver «Mazos».
              </li>
            </ul>
          </>
        )
      case 'frm':
        return (
          <>
            <h3>Qué son</h3>
            <p>
              Las Formaciones (阵) y las Runas (符) son cartas que se juegan
              desde la mano, como las demás, y producen un efecto continuo o al
              inicio de tu turno. Tú y tus enemigos usan las mismas reglas.
            </p>
            <ul>
              <li>
                <b>Formación</b>: solo 1 por bando; dura hasta que la
                reemplacen o la disipen. Da un bono continuo (Ataque, vida) o un
                efecto al inicio de turno.
              </li>
              <li>
                <b>Runa</b>: hasta 2 por bando (la tercera reemplaza a la más
                antigua); dura 2 o 3 turnos.
              </li>
              <li>
                <b>Disipar Formación</b> destruye las formaciones y runas del
                rival.
              </li>
            </ul>
            <h3>Cómo se configuran</h3>
            <p>
              No hay una pantalla para «activar» una formación: la incluyes en
              tu mazo (pestaña Mazos) y se activa al jugarla en combate. Jugar
              otra formación sustituye la actual. En el catálogo de Mazos ves
              cuáles tienes, sus efectos y sus descripciones.
            </p>
          </>
        )
      case 'eq':
        return (
          <>
            <h3>Los 6 espacios</h3>
            <p>
              El cultivador puede llevar equipo en 6 espacios: {SLOTS.join(', ')}
              .
            </p>
            <h3>Equipar, sustituir y retirar</h3>
            <ul>
              <li>
                Forja un objeto con materiales (los planos de rareza alta se
                desbloquean al vencer jefes de nivel). Si su espacio está vacío,
                se equipa solo.
              </li>
              <li>Equipar reemplaza al que hubiera en ese espacio.</li>
              <li>Retirar deja el espacio vacío.</li>
            </ul>
            <h3>Bonificaciones</h3>
            <ul>
              <li>
                <b>Ataque +N</b>: tus técnicas de daño hacen +N y tus criaturas
                entran con +N/2 (redondeado arriba).
              </li>
              <li>
                <b>Qi +N</b>: empiezas con +N Qi y tu Qi máximo sube N.
              </li>
              <li>
                Ambos suman entre todo el equipo con tope <b>+4</b> cada uno.
              </li>
              <li>
                <b>Artefacto</b>: te revive con la vida indicada cuando mueres;
                tiene usos limitados y se rompe al agotarlos.
              </li>
              <li>
                Las armaduras no dan defensa ni vida: el valor está en los
                bonos.
              </li>
            </ul>
          </>
        )
      case 'mer':
        return (
          <>
            <h3>Acceso y moneda</h3>
            <p>
              Pestaña <b>Mercado</b>. La moneda son las piedras espirituales.
              Cada secta tiene su puesto: solo compras en el de tu secta (★) y
              en el General; los demás se pueden mirar.
            </p>
            <h3>Qué se compra</h3>
            <ul>
              <li>
                <b>Cartas</b>: precio por rareza:{' '}
                {RN.slice(0, 5)
                  .map((n, i) => `${n} ${RP[i]}`)
                  .join(', ')}
                . Las Celestiales y las reliquias no se venden. Las cartas
                iniciales de tu secta ya están en tu mazo.
              </li>
              <li>
                <b>Material</b> propio de cada puesto por un precio fijo.
              </li>
              <li>
                <b>Vender</b> (puesto General): hierba {SELL.h}, polvo de jade{' '}
                {SELL.p}, núcleo {SELL.n} piedras cada uno.
              </li>
            </ul>
            <h3>Restricciones y confirmación</h3>
            <ul>
              <li>
                Máximo 3 copias de cada carta; sin piedras suficientes el botón
                queda desactivado.
              </li>
              <li>
                Cada compra pide <b>confirmación</b> en un modal antes de
                ejecutarse; al confirmar aparece un aviso y se actualizan el
                contador «Tienes N» y tus piedras.
              </li>
            </ul>
          </>
        )
      case 'cmb':
        return (
          <>
            <h3>Cómo funciona</h3>
            <ul>
              <li>
                Cada bando tiene vida, escudo, Qi, mano y mazo. Empiezas robando
                4 cartas y robas 1 al inicio de cada turno.
              </li>
              <li>
                Cada turno tu Qi máximo sube 1 hasta el tope y se rellena
                entero.
              </li>
              <li>
                Tus criaturas atacan una vez por turno: elígela y luego el
                objetivo (héroe rival o criatura). Las criaturas con Provocar
                deben atacarse primero.
              </li>
              <li>Desde el 2.º turno puede surgir un evento aleatorio (35%).</li>
            </ul>
            <h3>Daño y curación</h3>
            <ul>
              <li>
                El daño consume primero el <b>escudo</b> y luego la vida. El
                escudo se pierde al inicio de tu turno.
              </li>
              <li>
                Curas con cartas de curación, habilidades, Roba vida, píldoras
                de la bolsa y algunos eventos.
              </li>
            </ul>
            <h3>Límites de vida y sobrecuración</h3>
            <ul>
              <li>
                Vida máxima: {HP_BASE} + {HP_PER_REALM} por reino; algunas
                píldoras y trajes la suben solo durante el combate.
              </li>
              <li>
                Durante el combate puedes curarte por encima del máximo, hasta{' '}
                <b>×{OVH}</b>. Se muestra como «(+N temp.)».
              </li>
              <li>
                Al terminar (victoria, huida o salir) la vida se ajusta al
                máximo real; si es menor, se conserva tal cual. No se restaura
                sola.
              </li>
            </ul>
            <h3>Al finalizar</h3>
            <ul>
              <li>
                Vida: ver arriba. Al vencer a un jefe de nivel recuperas la
                vida completa. Escudo, Qi y mano no se conservan.
              </li>
              <li>Victoria: piedras, materiales y 1 carta a elegir.</li>
              <li>
                Derrota: el cultivador muere y reinicia el progreso (se
                conservan caídos y mejor reino), salvo salvavidas (Píldora de
                Inmortalidad, artefacto) o Talismán de Escape.
              </li>
            </ul>
          </>
        )
      default:
        return (
          <>
            <h3>Cueva de Reclusión</h3>
            <p>
              Tu vida no se recupera sola. En la Cueva de Reclusión consumes
              píldoras de recuperación (recetas que enseñan los boticarios).
              También curan las cartas de curación y derrotar al jefe de un
              piso.
            </p>
          </>
        )
    }
  })()

  return (
    <section className="pantalla guia" aria-label="Guía">
      <h1>📖 Guía del Sendero</h1>
      <p className="q">
        Reglas del juego, paso a paso. Las secciones replican la guía del
        original.
      </p>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      <div className="gs" role="tablist" aria-label="Secciones de la guía">
        {GS.map(([clave, icono, nombre]) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={seccion === clave}
            className={`chip${seccion === clave ? ' on' : ''}`}
            onClick={() => setSeccion(clave)}
          >
            {icono} {nombre}
          </button>
        ))}
      </div>

      <article className="gb">{contenido}</article>

      <h2>Sectas</h2>
      <div className="rejilla">
        {sectas.map((secta) => (
          <article key={secta.identificador} className="tarjeta">
            <h3>{secta.nombre}</h3>
            <p>{secta.descripcion}</p>
            <p className="mazo-base">
              Mazo base:{' '}
              {secta.cartas_iniciales
                .map((id) => nombreDeCarta[id] ?? id)
                .join(', ')}
            </p>
          </article>
        ))}
      </div>

      <details className="bestiario">
        <summary>Bestiario ({enemigos.length} enemigos)</summary>
        <div className="marco-tabla">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Nombre</th>
                <th>Vida</th>
                <th>Dificultad</th>
                <th>Origen</th>
              </tr>
            </thead>
            <tbody>
              {enemigos.map((enemigo) => (
                <tr key={enemigo.indice}>
                  <td>{enemigo.indice + 1}</td>
                  <td>{enemigo.nombre_enemigo}</td>
                  <td>{enemigo.vida}</td>
                  <td>{enemigo.dificultad}</td>
                  <td>{enemigo.origen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  )
}
