import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Check, Copy, RefreshCw, Shield, ShieldPlus } from 'lucide-react'

import { BotStartModal } from '@/components/bot/BotStartModal'
import { GroupSubscribeBell } from '@/components/birthday/GroupSubscribeBell'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import { buildInviteLink, groupErrorMessage, membersCountLabel } from '@/types/group'
import type { GroupDetail } from '@/types/group'
import type { TelegramDelivery } from '@/types/telegramDelivery'

function displayMemberName(m: { full_name: string | null; user_id: number }): string {
  return m.full_name?.trim() || `Участник #${m.user_id}`
}

function apiErrorDetail(e: unknown): unknown {
  return (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
}

export function GroupDetailPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const idNum = groupId ? Number.parseInt(groupId, 10) : NaN
  const { user: me } = useAuth()

  const [group, setGroup] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [savingSettings, setSavingSettings] = useState(false)
  const [notifyLeadDaysInput, setNotifyLeadDaysInput] = useState('7')
  const [promotingId, setPromotingId] = useState<number | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [delivery, setDelivery] = useState<TelegramDelivery | null>(null)
  const [botModalOpen, setBotModalOpen] = useState(false)

  const loadGroup = useCallback(async () => {
    if (Number.isNaN(idNum)) {
      setLoading(false)
      setError('Некорректная ссылка')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get<GroupDetail>(`/api/groups/${idNum}`)
      setGroup(data)
      setNotifyLeadDaysInput(String(data.notify_lead_days))
    } catch (e: unknown) {
      setGroup(null)
      setError(groupErrorMessage(apiErrorDetail(e)))
    } finally {
      setLoading(false)
    }
  }, [idNum])

  useEffect(() => {
    void loadGroup()
  }, [loadGroup])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data } = await api.get<TelegramDelivery>('/api/users/me/telegram-delivery')
        if (!cancelled) setDelivery(data)
      } catch {
        if (!cancelled) setDelivery({ can_receive_bot_messages: false, bot_username: null })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const isAdmin = group?.my_role === 'admin'

  const copyInvite = async () => {
    if (!group?.invite_token) return
    try {
      await navigator.clipboard.writeText(buildInviteLink(group.invite_token))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* ignore */
    }
  }

  const regenerateInvite = async () => {
    if (!group) return
    setRegenerating(true)
    setActionError(null)
    try {
      await api.post(`/api/groups/${group.id}/regenerate-invite`)
      await loadGroup()
    } catch (e: unknown) {
      setActionError(groupErrorMessage(apiErrorDetail(e)))
    } finally {
      setRegenerating(false)
    }
  }

  const saveSettings = async (
    overrides: { invite_visible_to_members?: boolean; notify_lead_days?: number },
  ) => {
    if (!group) return
    setSavingSettings(true)
    setActionError(null)
    try {
      const { data } = await api.patch<GroupDetail>(`/api/groups/${group.id}/settings`, {
        invite_visible_to_members: overrides.invite_visible_to_members ?? group.invite_visible_to_members,
        notify_lead_days: overrides.notify_lead_days ?? group.notify_lead_days,
      })
      setGroup((prev) => (prev ? { ...prev, ...data } : data))
    } catch (e: unknown) {
      setActionError(groupErrorMessage(apiErrorDetail(e)))
    } finally {
      setSavingSettings(false)
    }
  }

  const saveNotifyLeadDays = () => {
    const n = Number.parseInt(notifyLeadDaysInput, 10)
    if (!Number.isFinite(n) || n < 1 || n > 90) {
      setActionError('Укажите число от 1 до 90.')
      return
    }
    void saveSettings({ notify_lead_days: n })
  }

  const promote = async (targetUserId: number) => {
    if (!group) return
    setPromotingId(targetUserId)
    setActionError(null)
    try {
      await api.post(`/api/groups/${group.id}/members/${targetUserId}/promote`)
      await loadGroup()
    } catch (e: unknown) {
      setActionError(groupErrorMessage(apiErrorDetail(e)))
    } finally {
      setPromotingId(null)
    }
  }

  const setMemberSubscribed = (userId: number, subscribed: boolean) => {
    setGroup((prev) =>
      prev
        ? {
            ...prev,
            members: prev.members.map((m) => (m.user_id === userId ? { ...m, subscribed } : m)),
          }
        : prev,
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <BotStartModal
        open={botModalOpen}
        onClose={() => setBotModalOpen(false)}
        botUsername={delivery?.bot_username ?? null}
      />
      <Link
        to="/groups"
        className="inline-flex w-fit items-center gap-2 text-sm font-medium text-zinc-600 transition hover:text-orange-600 dark:text-zinc-400 dark:hover:text-orange-400"
      >
        <ArrowLeft className="size-4" aria-hidden />К группам
      </Link>

      {loading ? (
        <div className="h-10 w-64 animate-pulse rounded-lg bg-zinc-200/80 dark:bg-zinc-800" />
      ) : error || !group ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error ?? 'Не удалось загрузить группу'}
        </p>
      ) : (
        <>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
              {group.name}
            </h1>
            {isAdmin ? (
              <span className="flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-1 text-xs font-medium text-orange-700 dark:bg-orange-500/15 dark:text-orange-400">
                <Shield className="size-3.5" aria-hidden />
                admin
              </span>
            ) : null}
          </div>

          {actionError ? (
            <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
              {actionError}
            </p>
          ) : null}

          {group.invite_token ? (
            <Card>
              <CardHeader>
                <CardTitle>Приглашение</CardTitle>
                <CardDescription>
                  Отправьте эту ссылку, чтобы позвать в группу.
                </CardDescription>
              </CardHeader>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <code className="flex-1 truncate rounded-xl border border-zinc-200/80 bg-zinc-50/80 px-3 py-2.5 text-xs text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-300">
                  {buildInviteLink(group.invite_token)}
                </code>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => void copyInvite()} className="gap-1.5">
                    {copied ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
                    {copied ? 'Скопировано' : 'Копировать'}
                  </Button>
                  {isAdmin ? (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={regenerating}
                      onClick={() => void regenerateInvite()}
                      className="gap-1.5"
                      title="Старая ссылка перестанет работать"
                    >
                      <RefreshCw className={`size-4 ${regenerating ? 'animate-spin' : ''}`} aria-hidden />
                      Обновить
                    </Button>
                  ) : null}
                </div>
              </div>
              {isAdmin ? (
                <label className="mt-4 flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
                  <input
                    type="checkbox"
                    checked={group.invite_visible_to_members}
                    disabled={savingSettings}
                    onChange={() =>
                      void saveSettings({ invite_visible_to_members: !group.invite_visible_to_members })
                    }
                    className="size-4 rounded border-zinc-300 text-orange-600 focus:ring-orange-500 dark:border-zinc-700"
                  />
                  Разрешить участникам видеть и пересылать эту ссылку
                </label>
              ) : null}
            </Card>
          ) : null}

          {isAdmin ? (
            <Card>
              <CardHeader>
                <CardTitle>Уведомления о днях рождения</CardTitle>
                <CardDescription>
                  За сколько дней до ДР участника предупреждать админов группы
                </CardDescription>
              </CardHeader>
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="number"
                  min={1}
                  max={90}
                  value={notifyLeadDaysInput}
                  onChange={(e) => setNotifyLeadDaysInput(e.target.value)}
                  className="w-24 rounded-xl border border-zinc-300/80 bg-white/70 px-3 py-2 text-sm text-zinc-900 outline-none ring-orange-500/40 transition focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900/60 dark:text-zinc-100"
                />
                <span className="text-sm text-zinc-600 dark:text-zinc-400">дней</span>
                <Button
                  type="button"
                  variant="outline"
                  disabled={savingSettings || notifyLeadDaysInput === String(group.notify_lead_days)}
                  onClick={saveNotifyLeadDays}
                >
                  Сохранить
                </Button>
              </div>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Участники</CardTitle>
              <CardDescription>{membersCountLabel(group.member_count)}</CardDescription>
            </CardHeader>
            <ul className="flex flex-col divide-y divide-zinc-200/80 dark:divide-zinc-800">
              {group.members.map((m) => (
                <li key={m.user_id} className="flex items-center justify-between gap-3 py-3">
                  <div className="flex min-w-0 items-center gap-2">
                    <Link
                      to={`/users/${m.user_id}`}
                      className="truncate font-medium text-zinc-900 transition hover:text-orange-600 dark:text-zinc-100 dark:hover:text-orange-400"
                    >
                      {displayMemberName(m)}
                    </Link>
                    {m.role === 'admin' ? (
                      <span className="flex shrink-0 items-center gap-1 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700 dark:bg-orange-500/15 dark:text-orange-400">
                        <Shield className="size-3" aria-hidden />
                        admin
                      </span>
                    ) : null}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {me && me.id !== m.user_id ? (
                      <GroupSubscribeBell
                        targetUserId={m.user_id}
                        subscribed={m.subscribed}
                        canSubscribe
                        delivery={delivery}
                        isBotActive={me?.is_bot_active ?? false}
                        onSubscribedChange={(v) => setMemberSubscribed(m.user_id, v)}
                        onOpenBotHint={() => setBotModalOpen(true)}
                        compact
                      />
                    ) : null}
                    {isAdmin && m.role !== 'admin' ? (
                      <Button
                        type="button"
                        variant="ghost"
                        disabled={promotingId === m.user_id}
                        onClick={() => void promote(m.user_id)}
                        className="gap-1.5 text-xs"
                      >
                        <ShieldPlus className="size-3.5" aria-hidden />
                        Сделать админом
                      </Button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </div>
  )
}
