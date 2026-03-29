import fs from 'node:fs'
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

const frontendDir = path.dirname(fileURLToPath(import.meta.url))
/** Корень репозитория (рядом с docker-compose): общий .env с VITE_* и DB_* */
const repoRoot = path.resolve(frontendDir, '..')
/** В образе Docker в контексте только frontend → родитель /app без .env; не используем / как envDir. */
const envDir = fs.existsSync(path.join(repoRoot, '.env'))
  ? repoRoot
  : frontendDir

/** Сервис `backend` резолвится только внутри docker-сети; на хосте с npm run dev → 502. */
function resolveApiProxyTarget(raw: string | undefined): string {
  const fallback = 'http://127.0.0.1:8000'
  const source = (raw ?? '').trim() || fallback
  let t = source
  try {
    const u = new URL(source)
    if (u.hostname === 'backend') {
      const inDocker =
        process.env.IN_DOCKER === '1' ||
        (process.platform !== 'win32' && fs.existsSync('/.dockerenv'))
      if (!inDocker) {
        u.hostname = '127.0.0.1'
        t = u.toString().replace(/\/+$/, '')
      }
    }
  } catch {
    return fallback
  }
  return t || fallback
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, '')
  // process.env: compose задаёт переменные контейнеру; loadEnv: корневой .env на хосте.
  const fromEnv =
    process.env.VITE_API_PROXY_TARGET || env.VITE_API_PROXY_TARGET || ''
  const apiProxyTarget = resolveApiProxyTarget(fromEnv || undefined)
  const hmrClientPortRaw = (process.env.HMR_CLIENT_PORT || '').trim()
  const hmrClientPort = hmrClientPortRaw ? Number(hmrClientPortRaw) : undefined
  const hmr =
    hmrClientPort !== undefined && !Number.isNaN(hmrClientPort)
      ? { clientPort: hmrClientPort }
      : undefined

  return {
    envDir,
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      // Только 127.0.0.1 (не true / не 0.0.0.0), чтобы dev-origin совпадал с BotFather.
      // В Docker образ переопределяет: CMD `vite --host 0.0.0.0` (иначе порт с хоста не пробросится).
      host: '127.0.0.1',
      port: 5173,
      ...(hmr ? { hmr } : {}),
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
