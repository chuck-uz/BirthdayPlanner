import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { ArrowLeft, Send } from 'lucide-react'

import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { TelegramAuth } from '@/components/telegram/TelegramAuth'
import { useAuth } from '@/contexts/AuthContext'
import { readAndClearAccountBlockedFlag } from '@/lib/authSession'

export function LoginPage() {
  const { user, loading } = useAuth()
  const [wasBlocked, setWasBlocked] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setWasBlocked(readAndClearAccountBlockedFlag())
  }, [])
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  if (!loading && user) {
    const safeFrom =
      !from || from === '/login' || from === '/setup-profile' ? '/' : from
    const target = user.is_profile_complete ? safeFrom : '/setup-profile'
    return <Navigate to={target} replace />
  }

  return (
    <div className="relative min-h-svh overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden>
        <div className="absolute inset-0 bg-gradient-to-b from-orange-50/95 via-zinc-50 to-zinc-200/90 dark:from-zinc-950 dark:via-black dark:to-zinc-950" />
        <div className="absolute -top-32 left-1/2 h-[28rem] w-[min(100vw,42rem)] -translate-x-1/2 rounded-full bg-gradient-to-b from-orange-400/35 to-transparent blur-3xl dark:from-orange-500/20" />
        <div className="absolute bottom-0 right-0 h-80 w-80 translate-x-1/4 translate-y-1/4 rounded-full bg-orange-300/25 blur-3xl dark:bg-orange-600/15" />
        <div className="absolute left-0 top-1/2 h-64 w-64 -translate-x-1/3 rounded-full bg-amber-200/30 blur-3xl dark:bg-amber-900/20" />
        <div
          className="absolute inset-0 opacity-[0.35] dark:opacity-[0.12]"
          style={{
            backgroundImage: `radial-gradient(circle at center, rgba(24,24,27,0.06) 1px, transparent 1px)`,
            backgroundSize: '24px 24px',
          }}
        />
      </div>

      <div className="absolute right-4 top-4 z-20 sm:right-6 sm:top-6">
        <ThemeToggle />
      </div>

      <main className="relative z-10 flex min-h-svh flex-col items-center justify-center px-4 py-16 sm:px-6">
        <div className="bp-login-enter w-full max-w-[420px]">
          <div className="relative rounded-[1.75rem] p-[1px] shadow-[0_32px_64px_-12px_rgba(15,23,42,0.18)] dark:shadow-[0_32px_80px_-16px_rgba(0,0,0,0.65)]">
            <div
              className="absolute inset-0 rounded-[1.75rem] bg-gradient-to-br from-orange-400/70 via-orange-500/25 to-transparent opacity-90 dark:from-orange-500/40 dark:via-orange-600/15 dark:to-white/5"
              aria-hidden
            />
            <div className="relative overflow-hidden rounded-[1.7rem] border border-white/70 bg-white/75 backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900/75">
              <div
                className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-orange-400/15 blur-2xl dark:bg-orange-500/10"
                aria-hidden
              />
              <div className="relative px-8 pb-10 pt-12 sm:px-10 sm:pb-12 sm:pt-14">
                <div className="mb-8 flex flex-col items-center text-center">
                  <div className="relative mb-6">
                    <div
                      className="absolute inset-0 scale-110 rounded-3xl bg-gradient-to-br from-orange-500/30 to-amber-400/20 blur-xl dark:from-orange-500/25 dark:to-amber-600/10"
                      aria-hidden
                    />
                    <div className="relative flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 text-white shadow-lg shadow-orange-500/35 ring-4 ring-orange-500/10 dark:shadow-orange-900/40 dark:ring-orange-400/10">
                      <Send className="size-7" strokeWidth={2} aria-hidden />
                    </div>
                  </div>
                  <h1 className="text-balance text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-[1.65rem]">
                    Добро пожаловать
                  </h1>
                  <p className="mt-2 max-w-[280px] text-pretty text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                    Войдите через Telegram, чтобы вести список дней рождения в одном месте.
                  </p>
                  <Link
                    to="/about"
                    className="mt-3 text-sm font-medium text-orange-600 underline-offset-2 hover:underline dark:text-orange-400"
                  >
                    Что это такое?
                  </Link>
                </div>

                <div className="flex flex-col items-center gap-8">
                  {wasBlocked ? (
                    <p
                      role="alert"
                      className="max-w-[320px] rounded-xl border border-red-200/80 bg-red-50/90 px-4 py-3 text-center text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/50 dark:text-red-200"
                    >
                      Аккаунт заблокирован администратором. Если это ошибка, свяжитесь с поддержкой.
                    </p>
                  ) : null}
                  {loading ? (
                    <div
                      className="flex h-28 w-full max-w-[320px] items-center justify-center rounded-2xl border border-zinc-200/80 bg-zinc-50/80 dark:border-zinc-700/60 dark:bg-zinc-950/40"
                      aria-busy
                    >
                      <div className="h-9 w-9 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
                    </div>
                  ) : (
                    <TelegramAuth />
                  )}

                  <Link
                    to="/"
                    className="group inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 hover:text-orange-700 dark:text-zinc-400 dark:hover:bg-zinc-800/80 dark:hover:text-orange-300"
                  >
                    <ArrowLeft
                      className="size-4 transition group-hover:-translate-x-0.5"
                      aria-hidden
                    />
                    На главную
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
