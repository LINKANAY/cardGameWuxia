/** `ding()` de js/06-contenido.js:196: campanilla del evento de mapa.

Tono WebAudio (sine 660 → 880 Hz, 0.4 s) + vibración corta; ambos
envueltos en try/catch para que nunca rompan el render (el monolito
silencia todo error: navegadores sin AudioContext, permisos, etc.).
*/

export function ding(): void {
  try {
    const contexto = new AudioContext()
    const oscilador = contexto.createOscillator()
    const ganancia = contexto.createGain()
    oscilador.type = 'sine'
    oscilador.frequency.value = 660
    oscilador.connect(ganancia)
    ganancia.connect(contexto.destination)
    oscilador.start()
    oscilador.frequency.setValueAtTime(880, contexto.currentTime + 0.12)
    ganancia.gain.exponentialRampToValueAtTime(
      0.001,
      contexto.currentTime + 0.4,
    )
    oscilador.stop(contexto.currentTime + 0.42)
  } catch {
    // sin AudioContext (o bloqueado): se ignora, como en el monolito
  }
  try {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(60)
    }
  } catch {
    // sin API de vibración: se ignora
  }
}
