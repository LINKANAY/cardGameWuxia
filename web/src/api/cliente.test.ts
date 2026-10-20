/** Tests del cliente API: envelope, errores de red y formas de llamada. */

import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ErrorApi } from './cliente'

type FirmaFetch = (ruta: string, opciones?: RequestInit) => Promise<Response>

function respuestaJson(contenido: unknown, estado = 200): Response {
  return {
    ok: estado < 400,
    status: estado,
    json: async () => contenido,
  } as Response
}

function mockFetch(respuesta: Response | Error): ReturnType<typeof vi.fn> {
  const funcion =
    respuesta instanceof Error
      ? vi.fn<FirmaFetch>(async () => {
          throw respuesta
        })
      : vi.fn<FirmaFetch>(async () => respuesta)
  vi.stubGlobal('fetch', funcion)
  return funcion
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('pedir (interno vía api.*)', () => {
  it('devuelve data en envelope de éxito', async () => {
    mockFetch(respuestaJson({ ok: true, data: { version: '1.0' } }))
    await expect(api.obtenerEstado()).resolves.toEqual({ version: '1.0' })
  })

  it('lanza ErrorApi con el code del envelope de error', async () => {
    mockFetch(
      respuestaJson(
        { ok: false, error: { code: 'not_found', message: 'No existe' } },
        404,
      ),
    )
    const promesa = api.obtenerPartida('fantasma')
    await expect(promesa).rejects.toBeInstanceOf(ErrorApi)
    await expect(promesa).rejects.toMatchObject({
      codigo: 'not_found',
      estado: 404,
      message: 'No existe',
    })
  })

  it('traduce la caída del backend en ErrorApi sin_backend', async () => {
    mockFetch(new TypeError('Failed to fetch'))
    await expect(api.obtenerEstado()).rejects.toMatchObject({
      codigo: 'sin_backend',
      estado: 0,
    })
  })

  it('rechaza respuestas que no son JSON', async () => {
    mockFetch({
      status: 200,
      json: async () => {
        throw new SyntaxError('no es JSON')
      },
    } as unknown as Response)
    await expect(api.obtenerEstado()).rejects.toMatchObject({
      codigo: 'respuesta_invalida',
    })
  })

  it('rechaza JSON fuera del envelope', async () => {
    mockFetch(respuestaJson({ sorpresa: true }))
    await expect(api.obtenerEstado()).rejects.toMatchObject({
      codigo: 'respuesta_invalida',
    })
  })
})

describe('formas de llamada', () => {
  it('crearPartida hace POST /api/game/new con el body correcto', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'mazo1', snapshot: {} } }),
    )

    await api.crearPartida('mazo1')

    expect(fetchMock).toHaveBeenCalledOnce()
    const [ruta, opciones] = fetchMock.mock.calls[0]
    expect(ruta).toBe('/api/game/new')
    expect(opciones?.method).toBe('POST')
    expect(opciones?.body).toBe(JSON.stringify({ slot: 'mazo1' }))
  })

  it('obtenerPartida codifica el slot en la URL', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'a b', snapshot: {} } }),
    )

    await api.obtenerPartida('a b')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/a%20b')
  })

  it('borrarPartida usa DELETE', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'x' } }),
    )

    await api.borrarPartida('x')

    expect(fetchMock.mock.calls[0][1]?.method).toBe('DELETE')
  })

  it('listarPartidas extrae .slots del envelope', async () => {
    mockFetch(
      respuestaJson({
        ok: true,
        data: {
          slots: [
            { slot: 'p1', nivel_reino: 0, secta: 'esp', victorias: 2 },
          ],
        },
      }),
    )
    await expect(api.listarPartidas()).resolves.toEqual([
      { slot: 'p1', nivel_reino: 0, secta: 'esp', victorias: 2 },
    ])
  })

  it('elaborarPildora hace POST …/alquimia/elaborar con el body correcto', async () => {
    const fetchMock = mockFetch(
      respuestaJson({
        ok: true,
        data: { slot: 'viaje', mensaje: 'Elaboraste: X', snapshot: {} },
      }),
    )

    await api.elaborarPildora('viaje', 'vit')

    const [ruta, opciones] = fetchMock.mock.calls[0]
    expect(ruta).toBe('/api/game/viaje/alquimia/elaborar')
    expect(opciones?.method).toBe('POST')
    expect(opciones?.body).toBe(JSON.stringify({ pildora: 'vit' }))
  })

  it('forjarCarta usa la rareza en el body', async () => {
    const fetchMock = mockFetch(
      respuestaJson({
        ok: true,
        data: { slot: 'viaje', mensaje: 'Forjaste: X', carta: 'cf', snapshot: {} },
      }),
    )

    await api.forjarCarta('viaje', 2)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/alquimia/forjar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ rareza: 2 }))
  })

  it('fusionarCarta propaga el código de error del envelope', async () => {
    mockFetch(
      respuestaJson(
        {
          ok: false,
          error: { code: 'coleccion_insuficiente', message: 'Necesitas 3 copias' },
        },
        400,
      ),
    )

    await expect(api.fusionarCarta('viaje', 'cf')).rejects.toMatchObject({
      codigo: 'coleccion_insuficiente',
      estado: 400,
    })
  })

  it('desmantelarCarta POSTea el id de la carta', async () => {
    const fetchMock = mockFetch(
      respuestaJson({
        ok: true,
        data: { slot: 'viaje', mensaje: 'Desmantelaste X: +1', polvo: 1, snapshot: {} },
      }),
    )

    await api.desmantelarCarta('viaje', 'cf')

    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ carta: 'cf' }))
  })

  it('crearMazo POSTea desde_automatico', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: '', snapshot: {} } }),
    )

    await api.crearMazo('viaje', true)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mazos')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ desde_automatico: true }),
    )
  })

  it('usarMazo envía el índice (−1 = automático)', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: '', snapshot: {} } }),
    )

    await api.usarMazo('viaje', -1)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mazos/usar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ indice: -1 }))
  })

  it('anadirCartaMazo usa la ruta con índice', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: '', snapshot: {} } }),
    )

    await api.anadirCartaMazo('viaje', 2, 'cf')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mazos/2/anadir')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ carta: 'cf' }))
  })

  it('renombrarMazo envía el nombre recortable', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: '', snapshot: {} } }),
    )

    await api.renombrarMazo('viaje', 0, 'Mago de fuego')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mazos/0/renombrar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ nombre: 'Mago de fuego' }),
    )
  })

  it('eliminarMazo y desequiparCarta usan POST con body mínimo', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: '', snapshot: {} } }),
    )

    await api.eliminarMazo('viaje', 3)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mazos/eliminar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ indice: 3 }))

    await api.desequiparCarta('viaje', 'cf')
    expect(fetchMock.mock.calls[1][0]).toBe('/api/game/viaje/mazos/desequipar')
    expect(fetchMock.mock.calls[1][1]?.body).toBe(JSON.stringify({ carta: 'cf' }))
  })

  it('obtenerMercado y obtenerGacha son GET de catálogo', async () => {
    const fetchMercado = mockFetch(
      respuestaJson({
        ok: true,
        data: { puestos: [], precios_venta: {}, pildoras_en_venta: [] },
      }),
    )
    await api.obtenerMercado()
    expect(fetchMercado.mock.calls[0][0]).toBe('/api/data/mercado')
    expect(fetchMercado.mock.calls[0][1]?.method).toBe('GET')

    const fetchGacha = mockFetch(
      respuestaJson({ ok: true, data: { tickets: [], pools: [], rarezas: [] } }),
    )
    await api.obtenerGacha()
    expect(fetchGacha.mock.calls[0][0]).toBe('/api/data/gacha')
    expect(fetchGacha.mock.calls[0][1]?.method).toBe('GET')
  })

  it('detalleCarta codifica el id y añade la secta como query', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { carta: { identificador: 'ex' } } }),
    )

    await api.detalleCarta('ex', 'esp')

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/data/cartas/ex/detalle?secta=esp',
    )
  })

  it('comprarCarta y comprarMaterial POSTean con el body del monolito', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: 'ok', snapshot: {} } }),
    )

    await api.comprarCarta('viaje', 'pq')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mercado/comprar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ carta: 'pq' }))

    await api.comprarMaterial('viaje', 'esp', true)
    expect(fetchMock.mock.calls[1][0]).toBe(
      '/api/game/viaje/mercado/comprar-material',
    )
    expect(fetchMock.mock.calls[1][1]?.body).toBe(
      JSON.stringify({ puesto: 'esp', confirmado: true }),
    )
  })

  it('venderMaterial y comprarPildora usan claves cortas', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', mensaje: 'ok', snapshot: {} } }),
    )

    await api.venderMaterial('viaje', 'h')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/mercado/vender')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ material: 'h' }))

    await api.comprarPildora('viaje', 'vit')
    expect(fetchMock.mock.calls[1][0]).toBe(
      '/api/game/viaje/mercado/comprar-pildora',
    )
    expect(fetchMock.mock.calls[1][1]?.body).toBe(JSON.stringify({ pildora: 'vit' }))
  })

  it('tirarGacha envía pool y count (1 o 10)', async () => {
    const fetchMock = mockFetch(
      respuestaJson({
        ok: true,
        data: {
          slot: 'viaje',
          mensaje: 'ok',
          resultados: [],
          tickets_restantes: 0,
          piedad: 0,
          snapshot: {},
        },
      }),
    )

    await api.tirarGacha('viaje', 'PREMIUM', 10)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/gacha/tirar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ pool: 'PREMIUM', count: 10 }),
    )
  })

  it('tirarGacha propaga tickets_insuficientes', async () => {
    mockFetch(
      respuestaJson(
        {
          ok: false,
          error: { code: 'tickets_insuficientes', message: 'No tienes suficientes' },
        },
        400,
      ),
    )

    await expect(api.tirarGacha('viaje', 'STANDARD', 1)).rejects.toMatchObject({
      codigo: 'tickets_insuficientes',
      estado: 400,
    })
  })
})

describe('combate (Fase 3)', () => {
  it('iniciarCombate hace POST …/combate/iniciar con enemigo, píldoras y bolsa', async () => {
    const fetchMock = mockFetch(
      respuestaJson({
        ok: true,
        data: { slot: 'viaje', combate: { activo: true }, campaña: [] },
      }),
    )

    await api.iniciarCombate('viaje', 7, ['sombra'], ['fue'])

    const [ruta, opciones] = fetchMock.mock.calls[0]
    expect(ruta).toBe('/api/game/viaje/combate/iniciar')
    expect(opciones?.method).toBe('POST')
    expect(opciones?.body).toBe(
      JSON.stringify({ enemigo: 7, pildoras: ['sombra'], bolsa: ['fue'] }),
    )
  })

  it('resolverEventoCombate envía la opción elegida', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', combate: {}, campaña: [] } }),
    )
    await api.resolverEventoCombate('viaje', 1)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/combate/evento')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ opcion: 1 }))
  })

  it('usarPildoraCombate envía el identificador de la píldora', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', combate: {}, campaña: [] } }),
    )
    await api.usarPildoraCombate('viaje', 'fue')
    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/game/viaje/combate/usar-pildora',
    )
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ pildora: 'fue' }),
    )
  })

  it('cancelarDescartarExceso hace POST sin cuerpo', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', combate: {}, campaña: [] } }),
    )
    await api.cancelarDescartarExceso('viaje')
    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/game/viaje/combate/descartar-cancelar',
    )
  })

  it('jugarCartaCombate envía índice y objetivo opcional', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', combate: {}, campaña: [] } }),
    )

    await api.jugarCartaCombate('viaje', 2, 1)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/combate/jugar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ indice: 2, objetivo: 1 }),
    )

    await api.jugarCartaCombate('viaje', 0)
    expect(fetchMock.mock.calls[1][1]?.body).toBe(
      JSON.stringify({ indice: 0, objetivo: null }),
    )
  })

  it('atacarCombate usa atacante y objetivo (−1 = héroe)', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', combate: {}, campaña: [] } }),
    )

    await api.atacarCombate('viaje', 0, -1)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/combate/atacar')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ atacante: 0, objetivo: -1 }),
    )
  })

  it('terminarTurno envía forzar en el body', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { slot: 'viaje', combate: {}, campaña: [] } }),
    )

    await api.terminarTurno('viaje', true)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/combate/fin-turno')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ forzar: true }))
  })

  it('cerrarCombate usa POST …/combate/cerrar', async () => {
    const fetchMock = mockFetch(
      respuestaJson({ ok: true, data: { fin: 'w' } }),
    )

    await api.cerrarCombate('viaje')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/game/viaje/combate/cerrar')
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST')
  })
})
