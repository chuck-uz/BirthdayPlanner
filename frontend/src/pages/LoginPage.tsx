import { Link, Navigate, useLocation } from 'react-router-dom'
import { Lock } from 'lucide-react'

import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { TelegramAuth } from '@/components/telegram/TelegramAuth'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'

export function LoginPage() {
  const { user, loading } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  if (!loading && user) {
    const safeFrom =
      !from || from === '/login' || from === '/setup-profile' ? '/' : from
    const target = user.is_profile_complete ? safeFrom : '/setup-profile'
    return <Navigate to={target} replace />
  }

  return (
    <div className="relative min-h-svh overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-200/50 via-zinc-50 to-zinc-100 dark:from-orange-950/40 dark:via-zinc-950 dark:to-black"
        aria-hidden
      />
      <div className="absolute right-4 top-4 z-10 sm:right-6 sm:top-6">
        <ThemeToggle />
      </div>
      <div className="flex min-h-svh items-center justify-center px-4 py-16">
        <div className="mx-auto flex w-full max-w-md flex-col gap-6">
          <Card className="text-center">
            <CardHeader className="pb-8 pt-10">
              <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-2xl bg-orange-600/10 text-orange-600 dark:bg-orange-500/15 dark:text-orange-400">
                <Lock className="size-6" aria-hidden />
              </div>
              <CardTitle className="text-xl">Вход через Telegram</CardTitle>
            </CardHeader>
            <div className="flex flex-col items-center gap-6 px-6 pb-10">
              {loading ? (
                <div className="h-10 w-10 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
              ) : (
                <TelegramAuth />
              )}
              <Link
                to="/"
                className="text-sm text-zinc-500 underline-offset-4 hover:text-orange-600 hover:underline dark:text-zinc-400 dark:hover:text-orange-400"
              >
                На главную
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
