import { useEffect, useRef } from 'react'

import {
  buildTelegramAuthRedirectFromWidgetUser,
  normalizeTelegramAuthBase,
} from '@/lib/telegramLoginUrls'

/** Официальный telegram-widget.js: data-onauth → редирект на бэкенд с теми же query, что и data-auth-url. */
const TELEGRAM_WIDGET_SCRIPT = 'https://telegram.org/js/telegram-widget.js?22'
const WIDGET_ON_AUTH_GLOBAL = '__birthdayPlannerTelegramOnAuth'

function parseWidgetUser(raw: Record<string, unknown> | string): Record<string, unknown> {
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw) as Record<string, unknown>
    } catch {
      return {}
    }
  }
  return raw
}

export function TelegramAuth() {
  const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME?.trim()
  const authRaw = import.meta.env.VITE_TELEGRAM_AUTH_URL?.trim() ?? ''
  const authBase = authRaw ? normalizeTelegramAuthBase(authRaw) : ''
  const widgetHostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!botName || !authBase || !widgetHostRef.current) return

    const hostEl = widgetHostRef.current
    hostEl.replaceChildren()

    const w = window as Window & {
      [WIDGET_ON_AUTH_GLOBAL]?: (user: Record<string, unknown> | string) => void
    }
    w[WIDGET_ON_AUTH_GLOBAL] = (userRaw) => {
      const user = parseWidgetUser(userRaw)
      window.location.assign(buildTelegramAuthRedirectFromWidgetUser(authBase, user, false))
    }

    const script = document.createElement('script')
    script.async = true
    script.src = TELEGRAM_WIDGET_SCRIPT
    script.setAttribute('data-telegram-login', botName)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-onauth', `${WIDGET_ON_AUTH_GLOBAL}(user)`)
    script.setAttribute('data-origin', window.location.origin)
    hostEl.appendChild(script)

    return () => {
      delete w[WIDGET_ON_AUTH_GLOBAL]
      hostEl.replaceChildren()
    }
  }, [botName, authBase])

  if (!botName || !authBase) {
    return <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">Вход недоступен</p>
  }

  return (
    <div className="flex w-full max-w-[320px] flex-col items-center justify-center">
      <div ref={widgetHostRef} className="flex min-h-[44px] w-full flex-col items-center justify-center" />
    </div>
  )
}
