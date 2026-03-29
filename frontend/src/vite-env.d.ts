/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TELEGRAM_BOT_NAME?: string
  readonly VITE_TELEGRAM_AUTH_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
