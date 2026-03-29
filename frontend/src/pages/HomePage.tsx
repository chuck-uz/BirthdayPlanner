import { CalendarDays, Gift, Sparkles } from 'lucide-react'

import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type BirthdayCard = {
  id: string
  name: string
  dateLabel: string
  daysUntil: number
  note?: string
}

/** Демо-данные до появления API списка ДР */
const DEMO_UPCOMING: BirthdayCard[] = [
  {
    id: '1',
    name: 'Анна',
    dateLabel: '3 апреля',
    daysUntil: 5,
    note: 'Любит настольные игры',
  },
  {
    id: '2',
    name: 'Михаил',
    dateLabel: '12 апреля',
    daysUntil: 14,
  },
  {
    id: '3',
    name: 'Команда BirthdayPlanner',
    dateLabel: '1 мая',
    daysUntil: 33,
    note: 'Планируем вечеринку',
  },
]

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-orange-500/15 px-2.5 py-0.5 text-xs font-medium text-orange-800 dark:text-orange-300">
      {children}
    </span>
  )
}

export function HomePage() {
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
          Карточки в стеклянном стиле: кто празднует следующим и через сколько дней.
          Позже сюда подставятся данные из API.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {DEMO_UPCOMING.map((b) => (
          <Card
            key={b.id}
            className="group flex flex-col border-white/50 dark:border-white/10"
          >
            <CardHeader className="flex-1">
              <div className="mb-3 flex items-start justify-between gap-2">
                <div className="flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-orange-700 text-white shadow-lg shadow-orange-600/30">
                  <Gift className="size-5" aria-hidden />
                </div>
                <Badge>
                  через {b.daysUntil}{' '}
                  {b.daysUntil === 1
                    ? 'день'
                    : b.daysUntil > 1 && b.daysUntil < 5
                      ? 'дня'
                      : 'дней'}
                </Badge>
              </div>
              <CardTitle className="text-xl">{b.name}</CardTitle>
              <CardDescription className="flex items-center gap-1.5 text-base text-zinc-600 dark:text-zinc-300">
                <CalendarDays className="size-4 shrink-0" aria-hidden />
                {b.dateLabel}
              </CardDescription>
              {b.note ? (
                <p className="mt-2 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">
                  {b.note}
                </p>
              ) : null}
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  )
}
