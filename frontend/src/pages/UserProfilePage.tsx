import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, CalendarDays, Gift, ListChecks } from 'lucide-react'

import { WishlistItemCard } from '@/components/wishlist/WishlistItemCard'
import { Link, useParams } from 'react-router-dom'

import { BotStartModal } from '@/components/bot/BotStartModal'
import { BirthdayNotifyBell } from '@/components/birthday/BirthdayNotifyBell'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import { formatBirthDateLongRu } from '@/lib/birthdayFormat'
import type { UserPublicProfile } from '@/types/publicUser'
import type { SubscriptionState, TelegramDelivery } from '@/types/subscription'

function displayName(p: UserPublicProfile): string {
  const n = p.full_name?.trim()
  if (n) return n
  return `Участник #${p.id}`
}

export function UserProfilePage() {
  const { userId } = useParams<{ userId: string }>()
  const { user: me, refreshUser } = useAuth()
  const [profile, setProfile] = useState<UserPublicProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [delivery, setDelivery] = useState<TelegramDelivery | null>(null)
  const [subscribed, setSubscribed] = useState(false)
  const [botModalOpen, setBotModalOpen] = useState(false)

  const idNum = userId ? Number.parseInt(userId, 10) : NaN

  const patchDelivery = useCallback((patch: Partial<TelegramDelivery>) => {
    setDelivery((d) => ({
      can_receive_bot_messages:
        patch.can_receive_bot_messages ?? d?.can_receive_bot_messages ?? true,
      bot_username:
        patch.bot_username !== undefined ? patch.bot_username : (d?.bot_username ?? null),
    }))
  }, [])

  useEffect(() => {
    if (!userId || Number.isNaN(idNum) || idNum < 1) {
      setLoading(false)
      setError('Некорректная ссылка')
      setProfile(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    ;(async () => {
      try {
        const { data } = await api.get<UserPublicProfile>(`/api/users/${idNum}`)
        if (!cancelled) {
          setProfile(data)
          setError(null)
        }
      } catch (e: unknown) {
        if (!cancelled) {
          setProfile(null)
          const status = (e as { response?: { status?: number } })?.response?.status
          setError(status === 404 ? 'Пользователь не найден' : 'Не удалось загрузить профиль')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [userId, idNum])

  const isSelf = me?.id === profile?.id

  useEffect(() => {
    if (!profile || isSelf) {
      setDelivery(null)
      setSubscribed(false)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const [dRes, sRes] = await Promise.all([
          api.get<TelegramDelivery>('/api/users/me/telegram-delivery'),
          api.get<SubscriptionState>(`/api/users/${profile.id}/subscription`),
        ])
        if (!cancelled) {
          setDelivery(dRes.data)
          setSubscribed(sRes.data.subscribed)
          void refreshUser()
        }
      } catch {
        if (!cancelled) {
          setDelivery({ can_receive_bot_messages: false, bot_username: null })
          setSubscribed(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [profile, isSelf, refreshUser])

  const isBotActive = me?.is_bot_active ?? false

  return (
    <div className="flex flex-col gap-8">
      <BotStartModal
        open={botModalOpen}
        onClose={() => setBotModalOpen(false)}
        botUsername={delivery?.bot_username ?? null}
      />
      <div>
        <Link
          to="/"
          className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-zinc-600 transition hover:text-orange-600 dark:text-zinc-400 dark:hover:text-orange-400"
        >
          <ArrowLeft className="size-4" aria-hidden />
          К списку дней рождения
        </Link>
        {loading ? (
          <div className="h-10 w-64 animate-pulse rounded-lg bg-zinc-200/80 dark:bg-zinc-800" />
        ) : profile ? (
          <>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
                  {displayName(profile)}
                </h1>
                <p className="mt-1 flex flex-wrap items-center gap-1.5 text-zinc-600 dark:text-zinc-400">
                  <CalendarDays className="size-4 shrink-0" aria-hidden />
                  {profile.birth_date ? formatBirthDateLongRu(profile.birth_date) : '—'}
                </p>
              </div>
              {!isSelf && delivery ? (
                <BirthdayNotifyBell
                  targetUserId={profile.id}
                  subscribed={subscribed}
                  delivery={delivery}
                  isBotActive={isBotActive}
                  onSubscribedChange={setSubscribed}
                  onDeliveryPatch={patchDelivery}
                  onOpenBotHint={() => setBotModalOpen(true)}
                />
              ) : null}
            </div>
            {isSelf ? (
              <p className="mt-3 text-sm text-orange-700 dark:text-orange-300">
                Это ваш профиль — вишлист можно редактировать в разделе{' '}
                <Link to="/profile" className="font-medium underline underline-offset-2">
                  Профиль
                </Link>
                .
              </p>
            ) : null}
          </>
        ) : (
          <h1 className="text-3xl font-semibold text-zinc-900 dark:text-white">Профиль</h1>
        )}
      </div>

      {error && !loading ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      ) : null}

      {profile && !loading ? (
        <Card id="wishlist" className="scroll-mt-24 border-white/50 dark:border-white/10">
          <CardHeader>
            <div className="mb-2 flex items-center gap-2 text-orange-600 dark:text-orange-400">
              <ListChecks className="size-5" aria-hidden />
              <CardTitle className="text-lg">Вишлист</CardTitle>
            </div>
            <CardDescription>Идеи подарков с референсами и ссылками</CardDescription>
          </CardHeader>
          {profile.wishlists.length === 0 ? (
            <div className="px-6 pb-8 pt-0">
              <div className="flex flex-col items-center rounded-2xl border border-dashed border-zinc-300/90 py-12 text-center dark:border-zinc-700">
                <Gift className="mb-2 size-9 text-zinc-400 dark:text-zinc-500" aria-hidden />
                <p className="text-sm text-zinc-600 dark:text-zinc-400">Пока нет пунктов в вишлисте</p>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 px-6 pb-8 sm:grid-cols-2 lg:grid-cols-3">
              {profile.wishlists.map((w) => (
                <WishlistItemCard key={w.id} item={w} variant="public" />
              ))}
            </div>
          )}
        </Card>
      ) : null}
    </div>
  )
}
