/** URL для Telegram Login Widget (embed и script). */

const DEFAULT_TELEGRAM_AUTH_BASE = 'http://127.0.0.1:8000/api/auth/telegram'

/**
 * Единый callback на бэкенд: localhost → 127.0.0.1; при корне URL подставляется /api/auth/telegram.
 * Telegram и браузер считают http://localhost:* и http://127.0.0.1:* разными origin.
 */
export function normalizeTelegramAuthBase(raw: string): string {
  const trimmed = raw.trim()
  if (!trimmed) return DEFAULT_TELEGRAM_AUTH_BASE
  let u: URL
  try {
    u = new URL(trimmed)
  } catch {
    return DEFAULT_TELEGRAM_AUTH_BASE
  }
  if (u.hostname === 'localhost') {
    u.hostname = '127.0.0.1'
  }
  let pathname = u.pathname.replace(/\/+$/, '') || '/'
  if (pathname === '/') {
    pathname = '/api/auth/telegram'
  }
  u.pathname = pathname
  u.hash = ''
  return `${u.protocol}//${u.host}${u.pathname}`
}

/**
 * После успешного data-onauth: те же query, что у редиректа с data-auth-url, плюс next (и опционально popup).
 */
export function buildTelegramAuthRedirectFromWidgetUser(
  authBase: string,
  user: Record<string, unknown>,
  popup: boolean,
): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(user)) {
    if (v === undefined || v === null) continue
    q.set(k, String(v))
  }
  const next = `${window.location.origin}/`
  const glue = authBase.includes('?') ? '&' : '?'
  let url = `${authBase}${glue}${q.toString()}`
  url += `&next=${encodeURIComponent(next)}`
  if (popup) {
    url += '&popup=1'
  }
  return url
}

export function buildReturnToUrl(authBase: string, popup: boolean): string {
  const next = `${window.location.origin}/`
  const sep = authBase.includes('?') ? '&' : '?'
  let url = `${authBase}${sep}next=${encodeURIComponent(next)}`
  if (popup) {
    url += '&popup=1'
  }
  return url
}

export function buildTelegramOAuthEmbedUrl(
  botName: string,
  authBase: string,
  popup: boolean,
): string {
  const origin = window.location.origin
  const returnTo = buildReturnToUrl(authBase, popup)
  const params = new URLSearchParams({
    origin,
    return_to: returnTo,
    size: 'large',
    lang: 'ru',
  })
  return `https://oauth.telegram.org/embed/${encodeURIComponent(botName)}?${params.toString()}`
}
