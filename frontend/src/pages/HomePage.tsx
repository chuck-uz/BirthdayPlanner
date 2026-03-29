import { useCallback, useEffect, useState } from 'react'
import { CalendarPlus, Gift, ListChecks, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

import { BotStartModal } from '@/components/bot/BotStartModal'
import { BirthdayNotifyBell } from '@/components/birthday/BirthdayNotifyBell'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import {
  buildGoogleCalendarBirthdayUrl,
  daysUntilLabelRu,
  formatAnnualBirthdayRu,
} from '@/lib/birthdayFormat'
import type { TelegramDelivery } from '@/types/subscription'

type UpcomingBirthday = {
  user_id: number
  full_name: string | null
  birth_date: string
  days_until: number
  subscribed: boolean
  has_avatar: boolean
}

function displayName(row: UpcomingBirthday): string {
  const n = row.full_name?.trim()
  if (n) return n
  return `Участник #${row.user_id}`
}

function UpcomingCard({
  b,
  meId,
  delivery,
  isBotActive,
  patchDelivery,
  setSubscribedFor,
  onOpenBotModal,
}: {
  b: UpcomingBirthday
  meId: number | undefined
  delivery: TelegramDelivery | null
  isBotActive: boolean
  patchDelivery: (patch: Partial<TelegramDelivery>) => void
  setSubscribedFor: (userId: number, subscribed: boolean) => void
  onOpenBotModal: () => void
}) {
  const [imgFailed, setImgFailed] = useState(false)
  const name = displayName(b)
  const showAvatar = b.has_avatar && !imgFailed
  const calUrl = buildGoogleCalendarBirthdayUrl(name, b.birth_date)

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="flex min-h-[140px] gap-4 border-b border-zinc-100 bg-gradient-to-br from-zinc-50 to-orange-50/40 p-4 dark:border-zinc-800 dark:from-zinc-900 dark:to-orange-950/20">
        <div className="relative h-28 w-24 shrink-0 overflow-hidden rounded-xl bg-zinc-200/90 dark:bg-zinc-800">
          {showAvatar ? (
            <img
              src={`/api/users/${b.user_id}/avatar`}
              alt=""
              className="size-full object-cover"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <div className="flex size-full items-center justify-center text-zinc-500 dark:text-zinc-400">
              <Gift className="size-10" aria-hidden />
            </div>
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col justify-center gap-1">
          <span className="inline-flex w-fit rounded-full bg-orange-500/15 px-2.5 py-0.5 text-xs font-medium text-orange-800 dark:text-orange-300">
            {daysUntilLabelRu(b.days_until)}
          </span>
          <h2 className="text-lg font-semibold leading-tight text-zinc-900 dark:text-white">{name}</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{formatAnnualBirthdayRu(b.birth_date)}</p>
        </div>
      </div>

      <div className="flex flex-col gap-2 p-3">
        <Link
          to={`/users/${b.user_id}#wishlist`}
          className="inline-flex w-full items-center justify-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm font-medium text-zinc-800 transition hover:border-orange-300 hover:bg-orange-50/50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-orange-800 dark:hover:bg-orange-950/40"
        >
          <ListChecks className="size-4 shrink-0" aria-hidden />
          Вишлист
        </Link>
        <div className="grid grid-cols-2 gap-2">
          {meId !== b.user_id ? (
            delivery ? (
              <BirthdayNotifyBell
                targetUserId={b.user_id}
                subscribed={b.subscribed}
                delivery={delivery}
                isBotActive={isBotActive}
                onSubscribedChange={(v) => setSubscribedFor(b.user_id, v)}
                onDeliveryPatch={patchDelivery}
                onOpenBotHint={onOpenBotModal}
              />
            ) : (
              <div className="h-10 animate-pulse rounded-xl bg-zinc-200/80 dark:bg-zinc-800" />
            )
          ) : (
            <div className="flex min-h-[72px] items-center justify-center rounded-xl border border-dashed border-zinc-200 px-2 text-center text-xs text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
              Это вы
            </div>
          )}
          <button
            type="button"
            disabled={!calUrl}
            title="Добавить в Google Календарь"
            onClick={() => {
              if (calUrl) window.open(calUrl, '_blank', 'noopener,noreferrer')
            }}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm font-medium text-zinc-800 transition hover:border-blue-300 hover:bg-blue-50/50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-blue-800 dark:hover:bg-blue-950/30"
          >
            <CalendarPlus className="size-4 shrink-0 text-blue-600 dark:text-blue-400" aria-hidden />
            Google Календарь
          </button>
        </div>
      </div>
    </article>
  )
}

export function HomePage() {
  const { user: me, refreshUser } = useAuth()
  const [rows, setRows] = useState<UpcomingBirthday[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [delivery, setDelivery] = useState<TelegramDelivery | null>(null)
  const [botModalOpen, setBotModalOpen] = useState(false)

  const patchDelivery = useCallback((patch: Partial<TelegramDelivery>) => {
    setDelivery((d) => ({
      can_receive_bot_messages:
        patch.can_receive_bot_messages ?? d?.can_receive_bot_messages ?? true,
      bot_username:
        patch.bot_username !== undefined ? patch.bot_username : (d?.bot_username ?? null),
    }))
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data } = await api.get<TelegramDelivery>('/api/users/me/telegram-delivery')
        if (!cancelled) {
          setDelivery(data)
          void refreshUser()
        }
      } catch {
        if (!cancelled) {
          setDelivery({ can_receive_bot_messages: false, bot_username: null })
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [refreshUser])

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

  const setSubscribedFor = useCallback((userId: number, subscribed: boolean) => {
    setRows((prev) =>
      prev?.map((r) => (r.user_id === userId ? { ...r, subscribed } : r)) ?? null,
    )
  }, [])

  const isBotActive = me?.is_bot_active ?? false
  const openBotModal = useCallback(() => setBotModalOpen(true), [])

  return (
    <div className="flex flex-col gap-8">
      <BotStartModal
        open={botModalOpen}
        onClose={() => setBotModalOpen(false)}
        botUsername={delivery?.bot_username ?? null}
      />

      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
          <Sparkles className="size-5" aria-hidden />
          <span className="text-sm font-medium">Обзор</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-4xl">
          Ближайшие дни рождения
        </h1>
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
              className="h-64 animate-pulse rounded-2xl border border-zinc-200/60 bg-zinc-100/80 dark:border-zinc-800 dark:bg-zinc-900/50"
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
            <UpcomingCard
              key={b.user_id}
              b={b}
              meId={me?.id}
              delivery={delivery}
              isBotActive={isBotActive}
              patchDelivery={patchDelivery}
              setSubscribedFor={setSubscribedFor}
              onOpenBotModal={openBotModal}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
