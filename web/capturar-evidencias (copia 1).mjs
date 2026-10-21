/* Evidencias visuales: captura splash → campamento → alquimia → mazos
   → guía con Firefox headless (flujo con pestañas y slot fijo «viaje»). */
import puppeteer from 'puppeteer-core'

const BASE = 'http://localhost:5173'
const SALIDA =
  '/home/linkanay/me/games/Sendero_del_Inmortal/production/ui/front-basico/evidencias'
const esperar = (ms) => new Promise((resolver) => setTimeout(resolver, ms))

const navegador = await puppeteer.launch({
  browser: 'firefox',
  executablePath: '/usr/bin/firefox',
  headless: true,
})

try {
  const pagina = await navegador.newPage()
  await pagina.setViewport({ width: 1280, height: 900 })

  await pagina.goto(`${BASE}/`, { waitUntil: 'networkidle2', timeout: 30000 })
  await pagina.waitForSelector('.splash .estado-servidor', { timeout: 15000 })
  await esperar(600)
  await pagina.screenshot({ path: `${SALIDA}/01-splash.png`, fullPage: true })

  // Entrar → pestaña Campamento (slot fijo viaje, auto-creado si hace falta)
  await pagina.click('.splash .boton.principal')
  await pagina.waitForSelector('.ficha', { timeout: 15000 })
  await esperar(600)
  await pagina.screenshot({ path: `${SALIDA}/02-campamento.png`, fullPage: true })

  // Pestaña Alquimia
  await pagina.evaluate(() => {
    const alquimia = [...document.querySelectorAll('.tabs .tab')].find(
      (boton) => boton.textContent.trim() === 'Alquimia',
    )
    alquimia?.click()
  })
  await pagina.waitForSelector('.taller-alq', { timeout: 15000 })
  await esperar(600)
  await pagina.screenshot({ path: `${SALIDA}/03-alquimia.png`, fullPage: true })

  // Sembrar un mazo (copia del automático) para que la captura no esté vacía
  await pagina.evaluate(async () => {
    await fetch('/api/game/viaje/mazos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ desde_automatico: true }),
    })
  })
  await pagina.reload({ waitUntil: 'networkidle2', timeout: 30000 })
  await pagina.waitForSelector('.splash .estado-servidor', { timeout: 15000 })
  await pagina.click('.splash .boton.principal')
  await pagina.waitForSelector('.ficha', { timeout: 15000 })

  // Pestaña Mazos
  await pagina.evaluate(() => {
    const mazos = [...document.querySelectorAll('.tabs .tab')].find(
      (boton) => boton.textContent.trim() === 'Mazos',
    )
    mazos?.click()
  })
  await pagina.waitForSelector('.pantalla.mazos', { timeout: 15000 })
  await esperar(600)
  await pagina.screenshot({ path: `${SALIDA}/04-mazos.png`, fullPage: true })

  // Pestaña Guía (sectas + bestiario)
  await pagina.evaluate(() => {
    const guia = [...document.querySelectorAll('.tabs .tab')].find(
      (boton) => boton.textContent.trim() === 'Guía',
    )
    guia?.click()
  })
  await pagina.waitForSelector('.guia .bestiario', { timeout: 15000 })
  await esperar(600)
  await pagina.screenshot({ path: `${SALIDA}/05-guia.png`, fullPage: true })

  console.log('capturas OK')
} finally {
  await navegador.close()
}
