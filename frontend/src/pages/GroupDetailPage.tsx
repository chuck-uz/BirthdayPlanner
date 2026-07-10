import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Check, Copy, RefreshCw, Shield, ShieldPlus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { buildInviteLink, groupErrorMessage, membersCountLabel } from '@/types/group'
import type { GroupDetail } from '@/types/group'

function displayMemberName(m: { full_name: string | null; user_id: number }): string {
  return m.full_name?.trim() || `Участник #${m.user_id}`
}

function apiErrorDetail(e: unknown): unknown {
  return (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
}

export function GroupDetailPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const idNum = groupId ? Number.parseInt(groupId, 10) : NaN

  const [group, setGroup] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [togglingVisibility, setTogglingVisibility] = useState(false)
  const [promotingId, setPromotingId] = useState<number | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

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

  const toggleVisibility = async () => {
    if (!group) return
    setTogglingVisibility(true)
    setActionError(null)
    try {
      const { data } = await api.patch<GroupDetail>(`/api/groups/${group.id}/settings`, {
        invite_visible_to_members: !group.invite_visible_to_members,
      })
      setGroup((prev) => (prev ? { ...prev, ...data } : data))
    } catch (e: unknown) {
      setActionError(groupErrorMessage(apiErrorDetail(e)))
    } finally {
      setTogglingVisibility(false)
    }
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

  return (
    <div className="flex flex-col gap-8">
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
                    disabled={togglingVisibility}
                    onChange={() => void toggleVisibility()}
                    className="size-4 rounded border-zinc-300 text-orange-600 focus:ring-orange-500 dark:border-zinc-700"
                  />
                  Разрешить участникам видеть и пересылать эту ссылку
                </label>
              ) : null}
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
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {displayMemberName(m)}
                    </span>
                    {m.role === 'admin' ? (
                      <span className="flex items-center gap-1 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700 dark:bg-orange-500/15 dark:text-orange-400">
                        <Shield className="size-3" aria-hidden />
                        admin
                      </span>
                    ) : null}
                  </div>
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
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </div>
  )
}
