#!/usr/bin/env node
/**
 * Проверка ответа oauth.telegram.org (как у iframe виджета).
 * Запуск из корня репозитория:
 *   node scripts/check-telegram-embed.mjs
 * Переменные из .env подхватит dotenv, либо задайте в окружении:
 *   VITE_TELEGRAM_BOT_NAME, CHECK_ORIGIN (опц., по умолчанию http://127.0.0.1)
 */
import { readFileSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const envPath = resolve(root, '.env')

if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^([^#=]+)=(.*)$/)
    if (!m) continue
    const k = m[1].trim()
    let v = m[2].trim().replace(/^["']|["']$/g, '')
    if (!(k in process.env)) process.env[k] = v
  }
}

const bot = process.env.VITE_TELEGRAM_BOT_NAME?.trim()
const authBase =
  process.env.VITE_TELEGRAM_AUTH_URL?.trim() ||
  'http://127.0.0.1:8000/api/auth/telegram'
const origin =
  process.env.CHECK_ORIGIN?.trim() || 'http://127.0.0.1'
const next = `${origin.replace(/\/$/, '')}/`
const sep = authBase.includes('?') ? '&' : '?'
const returnTo = `${authBase}${sep}next=${encodeURIComponent(next)}`

if (!bot) {
  console.error('Нет VITE_TELEGRAM_BOT_NAME в .env или окружении.')
  process.exit(1)
}

const params = new URLSearchParams({
  origin,
  return_to: returnTo,
  size: 'large',
  request_access: 'write',
})
const url = `https://oauth.telegram.org/embed/${encodeURIComponent(bot)}?${params}`

console.log('GET', url.slice(0, 120) + (url.length > 120 ? '…' : ''))

const res = await fetch(url, { redirect: 'follow' })
const text = await res.text()
const ok = res.ok && !/bot domain invalid/i.test(text)
const hasButton = /widget_login|Log in with Telegram|Войти через Telegram/i.test(
  text,
)

console.log('HTTP', res.status, ok ? 'OK' : 'FAIL')
if (!ok) {
  console.log('Тело (фрагмент):', text.slice(0, 200).replace(/\s+/g, ' '))
  console.log(
    '\nПо документации Telegram домен в @BotFather (/setdomain) должен совпадать с hostname из параметра origin.',
  )
  console.log(
    'Если в BotFather указан 127.0.0.1, нельзя открывать сайт как localhost (и наоборот).',
  )
  process.exit(1)
}

if (!hasButton) {
  console.warn('Ответ OK, но разметка кнопки не найдена — проверьте вручную.')
  process.exit(2)
}

console.log('Виджет отдаёт страницу с кнопкой входа (проверка пройдена).')
