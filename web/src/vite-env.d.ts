/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base del backend (vacía = relativo → proxy de Vite). */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
