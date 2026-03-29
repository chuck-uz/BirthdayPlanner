import { useEffect, useRef } from 'react'

const WIDGET_SRC = 'https://telegram.org/js/telegram-widget.js?22'

function buildAuthUrl(base: string): string {
  const next = `${window.location.origin}/`
  const sep = base.includes('?') ? '&' : '?'
  return `${base}${sep}next=${encodeURIComponent(next)}`
}

/**
 * Виджет Telegram Login. Домен в BotFather: http://127.0.0.1
 * VITE_TELEGRAM_AUTH_URL — полный URL бэкенда, например
 * http://127.0.0.1:8000/api/auth/telegram
 */
export function TelegramAuth() {
  const containerRef = useRef<HTMLDivElement>(null)
  const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME
  const authBase = import.meta.env.VITE_TELEGRAM_AUTH_URL

  useEffect(() => {
    if (!botName || !authBase || !containerRef.current) return

    const el = containerRef.current
    el.innerHTML = ''

    const script = document.createElement('script')
    script.src = WIDGET_SRC
    script.async = true
    script.setAttribute('data-telegram-login', botName)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-radius', '12')
    script.setAttribute('data-request-access', 'write')
    script.setAttribute('data-auth-url', buildAuthUrl(authBase))

    el.appendChild(script)

    return () => {
      el.innerHTML = ''
    }
  }, [botName, authBase])

  if (!botName || !authBase) {
    return (
      <p className="text-center text-sm text-orange-800 dark:text-orange-400">
        Задайте в <code className="rounded bg-black/5 px-1 dark:bg-white/10">frontend/.env</code>{' '}
        переменные <code>VITE_TELEGRAM_BOT_NAME</code> и{' '}
        <code>VITE_TELEGRAM_AUTH_URL</code>.
      </p>
    )
  }

  return (
    <div
      ref={containerRef}
      className="flex min-h-[48px] items-center justify-center [&_iframe]:rounded-xl"
    />
  )
}
