import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// El proxy /api → backend (:8765) evita CORS en desarrollo:
// el front siempre habla con su propia origen.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8765',
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
