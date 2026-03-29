import { useEffect, useState } from 'react'
import { CalendarDays, Gift, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

import { api } from '@/lib/api'
import { daysUntilLabelRu, formatAnnualBirthdayRu } from '@/lib/birthdayFormat'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type UpcomingBirthday = {
  user_id: number
  full_name: string | null
  birth_date: string
  days_until: number
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-orange-500/15 px-2.5 py-0.5 text-xs font-medium text-orange-800 dark:text-orange-300">
      {children}
    </span>
  )
}

function displayName(row: UpcomingBirthday): string {
  const n = row.full_name?.trim()
  if (n) return n
  return `Участник #${row.user_id}`
}

export function HomePage() {
  const [rows, setRows] = useState<UpcomingBirthday[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data } = await api.get<UpcomingBirthday[]>('/api/users/birthdays/upcoming')
        if (!cancelled) {
          setRows(data)
          setError(null)
        }
      } catch {
        if (!cancelled) {
          setRows(null)
          setError('Не удалось загрузить список')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
          <Sparkles className="size-5" aria-hidden />
          <span className="text-sm font-medium">Обзор</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-4xl">
          Ближайшие дни рождения
        </h1>
        <p className="max-w-2xl text-zinc-600 dark:text-zinc-400">
          Нажмите на карточку, чтобы открыть профиль и вишлист именинника.
        </p>
      </div>

      {error ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      ) : null}

      {rows === null && !error ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-48 animate-pulse rounded-2xl border border-zinc-200/60 bg-zinc-100/80 dark:border-zinc-800 dark:bg-zinc-900/50"
            />
          ))}
        </div>
      ) : null}

      {rows !== null && rows.length === 0 && !error ? (
        <div className="rounded-2xl border border-dashed border-zinc-300/90 bg-white/40 px-6 py-16 text-center dark:border-zinc-700 dark:bg-zinc-950/30">
          <Gift className="mx-auto mb-3 size-10 text-zinc-400 dark:text-zinc-500" aria-hidden />
          <p className="text-base font-medium text-zinc-800 dark:text-zinc-200">
            Пока нет дат рождения
          </p>
          <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
            Когда пользователи укажут день рождения в профиле, они появятся здесь.
          </p>
        </div>
      ) : null}

      {rows !== null && rows.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((b) => (
            <Link
              key={b.user_id}
              to={`/users/${b.user_id}`}
              aria-label={`Профиль и вишлист: ${displayName(b)}`}
              className="group block h-full rounded-2xl outline-none ring-orange-500/0 transition hover:ring-2 focus-visible:ring-2 focus-visible:ring-orange-500"
            >
              <Card className="h-full flex-col border-white/50 transition group-hover:border-orange-200/60 dark:border-white/10 dark:group-hover:border-orange-500/25">
                <CardHeader className="flex-1">
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div className="flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-orange-700 text-white shadow-lg shadow-orange-600/30">
                      <Gift className="size-5" aria-hidden />
                    </div>
                    <Badge>{daysUntilLabelRu(b.days_until)}</Badge>
                  </div>
                  <CardTitle className="text-xl">{displayName(b)}</CardTitle>
                  <CardDescription className="flex items-center gap-1.5 text-base text-zinc-600 dark:text-zinc-300">
                    <CalendarDays className="size-4 shrink-0" aria-hidden />
                    {formatAnnualBirthdayRu(b.birth_date)}
                  </CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  )
}
