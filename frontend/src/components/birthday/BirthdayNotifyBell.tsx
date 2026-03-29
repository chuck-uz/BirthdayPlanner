import { useCallback, useEffect, useState } from 'react'
import { Bell, BellRing, Loader2 } from 'lucide-react'

import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import type { SubscriptionState, TelegramDelivery } from '@/types/subscription'

type Props = {
  targetUserId: number
  subscribed: boolean
  delivery: TelegramDelivery | null
  /** Из БД: пользователь нажал /start у бота (или синхронизировано через getChat). */
  isBotActive: boolean
  onSubscribedChange: (subscribed: boolean) => void
  onDeliveryPatch: (patch: Partial<TelegramDelivery>) => void
  onOpenBotHint?: () => void
}

export function BirthdayNotifyBell({
  targetUserId,
  subscribed: initialSubscribed,
  delivery,
  isBotActive,
  onSubscribedChange,
  onDeliveryPatch,
  onOpenBotHint,
}: Props) {
  const [subscribed, setSubscribed] = useState(initialSubscribed)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setSubscribed(initialSubscribed)
  }, [initialSubscribed])

  const mergeDelivery = useCallback(
    (s: SubscriptionState) => {
      onDeliveryPatch({
        can_receive_bot_messages: s.can_receive_bot_messages,
        bot_username: s.bot_username,
      })
    },
    [onDeliveryPatch],
  )

  const subscribe = async () => {
    if (!isBotActive) {
      onOpenBotHint?.()
      return
    }
    setBusy(true)
    try {
      const { data } = await api.post<SubscriptionState>(
        `/api/users/${targetUserId}/subscription`,
      )
      setSubscribed(true)
      onSubscribedChange(true)
      mergeDelivery(data)
    } finally {
      setBusy(false)
    }
  }

  const unsubscribe = async () => {
    setBusy(true)
    try {
      await api.delete(`/api/users/${targetUserId}/subscription`)
      setSubscribed(false)
      onSubscribedChange(false)
    } finally {
      setBusy(false)
    }
  }

  const canReceive = delivery?.can_receive_bot_messages ?? true
  const botUser = delivery?.bot_username
  const blockSubscribe = !subscribed && !isBotActive

  return (
    <div className="flex flex-col items-stretch gap-1.5">
      {subscribed ? (
        <Button
          type="button"
          variant="outline"
          disabled={busy}
          className="gap-1.5 border-orange-200/80 bg-orange-50/80 px-3 py-2 text-xs text-orange-900 hover:bg-orange-100/90 dark:border-orange-900/50 dark:bg-orange-950/40 dark:text-orange-100 dark:hover:bg-orange-950/70"
          onClick={() => void unsubscribe()}
        >
          {busy ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : (
            <BellRing className="size-4" aria-hidden />
          )}
          Уведомления вкл.
        </Button>
      ) : (
        <>
          <Button
            type="button"
            variant="primary"
            disabled={busy || blockSubscribe}
            className="gap-1.5 px-3 py-2 text-xs"
            onClick={() => void subscribe()}
          >
            {busy ? (
              <Loader2 className="size-4 animate-spin" aria-hidden />
            ) : (
              <Bell className="size-4" aria-hidden />
            )}
            Подписаться
          </Button>
          {blockSubscribe ? (
            <button
              type="button"
              onClick={() => onOpenBotHint?.()}
              className="text-center text-[0.7rem] font-medium text-orange-700 underline underline-offset-2 dark:text-orange-300"
            >
              Запустите бота для подписки
            </button>
          ) : null}
        </>
      )}
      {subscribed && !canReceive ? (
        <p className="text-[0.65rem] leading-snug text-amber-800 dark:text-amber-200">
          Нажмите «Старт» у бота в Telegram, иначе напоминание не дойдёт.
          {botUser ? (
            <>
              {' '}
              <a
                href={`https://t.me/${botUser}`}
                target="_blank"
                rel="noreferrer"
                className="font-medium underline underline-offset-2"
              >
                @{botUser}
              </a>
            </>
          ) : null}
        </p>
      ) : null}
    </div>
  )
}
