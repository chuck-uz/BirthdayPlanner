import { useEffect, useRef, useState } from 'react'
import { ShieldOff } from 'lucide-react'

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
  const [ready, setReady] = useState(false)

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
    script.setAttribute('data-radius', '12')
    script.setAttribute('data-lang', 'ru')
    script.setAttribute('data-onauth', `${WIDGET_ON_AUTH_GLOBAL}(user)`)
    script.setAttribute('data-origin', window.location.origin)
    script.onload = () => setReady(true)
    hostEl.appendChild(script)

    return () => {
      delete w[WIDGET_ON_AUTH_GLOBAL]
      hostEl.replaceChildren()
    }
  }, [botName, authBase])

  if (!botName || !authBase) {
    return (
      <div className="flex w-full max-w-[320px] flex-col items-center gap-3 rounded-2xl border border-dashed border-zinc-300/90 bg-zinc-50/90 px-6 py-10 text-center dark:border-zinc-600 dark:bg-zinc-950/50">
        <div className="flex size-12 items-center justify-center rounded-xl bg-zinc-200/80 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
          <ShieldOff className="size-6" aria-hidden />
        </div>
        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Вход недоступен</p>
      </div>
    )
  }

  return (
    <div className="flex w-full max-w-[320px] flex-col items-center gap-3">
      <div className="relative flex min-h-[48px] w-full items-center justify-center">
        {!ready ? (
          <div
            className="absolute inset-0 animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-800"
            aria-hidden
          />
        ) : null}
        <div
          ref={widgetHostRef}
          className={`flex w-full flex-col items-center justify-center transition-opacity duration-300 ${
            ready ? 'opacity-100' : 'opacity-0'
          }`}
        />
      </div>
      <p className="text-xs text-zinc-500 dark:text-zinc-500">Быстрый и безопасный вход без пароля</p>
    </div>
  )
}
