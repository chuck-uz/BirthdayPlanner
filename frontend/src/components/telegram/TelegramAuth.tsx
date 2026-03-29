import { useEffect, useRef } from 'react'
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
    <div className="flex w-full max-w-[320px] flex-col items-center justify-center">
      <div
        className="flex w-full min-h-[52px] flex-col items-center justify-center rounded-2xl border border-zinc-200/90 bg-white/60 px-4 py-5 shadow-inner shadow-zinc-900/5 dark:border-zinc-700/80 dark:bg-zinc-950/40 dark:shadow-black/20"
      >
        <div ref={widgetHostRef} className="flex min-h-[40px] w-full flex-col items-center justify-center" />
      </div>
    </div>
  )
}
