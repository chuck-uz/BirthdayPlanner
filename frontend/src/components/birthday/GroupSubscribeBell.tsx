import { useEffect, useState } from 'react'
import { Bell, BellRing, Loader2 } from 'lucide-react'

import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import type { TelegramDelivery } from '@/types/telegramDelivery'

type Props = {
  targetUserId: number
  subscribed: boolean
  canSubscribe: boolean
  delivery: TelegramDelivery | null
  isBotActive: boolean
  onSubscribedChange: (subscribed: boolean) => void
  onOpenBotHint?: () => void
  compact?: boolean
}

export function GroupSubscribeBell({
  targetUserId,
  subscribed: initialSubscribed,
  canSubscribe,
  delivery,
  isBotActive,
  onSubscribedChange,
  onOpenBotHint,
  compact = false,
}: Props) {
  const [subscribed, setSubscribed] = useState(initialSubscribed)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setSubscribed(initialSubscribed)
  }, [initialSubscribed])

  const subscribe = async () => {
    if (!isBotActive) {
      onOpenBotHint?.()
      return
    }
    setBusy(true)
    try {
      await api.post(`/api/users/${targetUserId}/group-subscription`)
      setSubscribed(true)
      onSubscribedChange(true)
    } finally {
      setBusy(false)
    }
  }

  const unsubscribe = async () => {
    setBusy(true)
    try {
      await api.delete(`/api/users/${targetUserId}/group-subscription`)
      setSubscribed(false)
      onSubscribedChange(false)
    } finally {
      setBusy(false)
    }
  }

  if (!canSubscribe) return null

  const canReceive = delivery?.can_receive_bot_messages ?? true
  const botUser = delivery?.bot_username
  const blockSubscribe = !subscribed && !isBotActive
  const sizeClass = compact ? 'px-2.5 py-1.5 text-xs' : 'px-3 py-2 text-xs'

  return (
    <div className="flex flex-col items-stretch gap-1.5">
      {subscribed ? (
        <Button
          type="button"
          variant="outline"
          disabled={busy}
          title="Уведомления о ДР включены"
          className={`gap-1.5 border-orange-200/80 bg-orange-50/80 text-orange-900 hover:bg-orange-100/90 dark:border-orange-900/50 dark:bg-orange-950/40 dark:text-orange-100 dark:hover:bg-orange-950/70 ${sizeClass}`}
          onClick={() => void unsubscribe()}
        >
          {busy ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : (
            <BellRing className="size-4" aria-hidden />
          )}
          {compact ? null : 'Уведомления вкл.'}
        </Button>
      ) : (
        <>
          <Button
            type="button"
            variant="primary"
            disabled={busy || blockSubscribe}
            title="Подписаться на уведомление о ДР"
            className={`gap-1.5 ${sizeClass}`}
            onClick={() => void subscribe()}
          >
            {busy ? (
              <Loader2 className="size-4 animate-spin" aria-hidden />
            ) : (
              <Bell className="size-4" aria-hidden />
            )}
            {compact ? null : 'Подписаться'}
          </Button>
          {blockSubscribe && !compact ? (
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
      {subscribed && !canReceive && !compact ? (
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
