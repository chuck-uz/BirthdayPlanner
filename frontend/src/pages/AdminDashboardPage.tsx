import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Send } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/contexts/ToastContext'
import { api } from '@/lib/api'
import type {
  AdminBirthdayDashboardItem,
  AdminBroadcastLinkOut,
} from '@/types/admin'

function isValidTelegramLink(v: string): boolean {
  return /^https:\/\/t\.me\/\S+$/i.test(v.trim())
}

export function AdminDashboardPage() {
  const [rows, setRows] = useState<AdminBirthdayDashboardItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [modalRow, setModalRow] = useState<AdminBirthdayDashboardItem | null>(null)
  const [link, setLink] = useState('')
  const [sending, setSending] = useState(false)
  const [linkError, setLinkError] = useState<string | null>(null)
  const { showToast } = useToast()

  const load = async () => {
    try {
      const { data } = await api.get<AdminBirthdayDashboardItem[]>('/api/admin/birthdays')
      setRows(data)
      setError(null)
    } catch {
      setRows(null)
      setError('Не удалось загрузить список (доступ только для администратора).')
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const sendTitle = useMemo(() => {
    if (!modalRow) return ''
    return modalRow.full_name?.trim() || `Участник #${modalRow.id}`
  }, [modalRow])

  const submit = async () => {
    if (!modalRow) return
    const trimmed = link.trim()
    if (!isValidTelegramLink(trimmed)) {
      setLinkError('Нужна ссылка формата https://t.me/...')
      return
    }
    setSending(true)
    setLinkError(null)
    try {
      const { data } = await api.post<AdminBroadcastLinkOut>('/api/admin/broadcast-link', {
        target_user_id: modalRow.id,
        group_link: trimmed,
      })
      showToast(`✅ Ссылка разослана ${data.sent_count} пользователям.`)
      setModalRow(null)
      setLink('')
      await load()
    } catch {
      setLinkError('Не удалось выполнить рассылку.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">Рассылки ссылок</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Выберите именинника и разошлите ссылку всем его подписчикам.
        </p>
      </div>

      {error ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      ) : null}

      {rows === null && !error ? (
        <div className="h-44 animate-pulse rounded-2xl bg-zinc-200/60 dark:bg-zinc-800/60" />
      ) : rows ? (
        <div className="overflow-x-auto rounded-2xl border border-zinc-200/80 bg-white/60 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/50">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-zinc-200/80 bg-zinc-50/80 text-xs font-medium uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-400">
              <tr>
                <th className="px-4 py-3">Именинник</th>
                <th className="px-4 py-3">Дата</th>
                <th className="px-4 py-3">Через</th>
                <th className="px-4 py-3">Подписчики</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3 text-right">Действие</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {rows.map((r) => (
                <tr key={r.id} className={r.is_sent ? 'bg-emerald-50/30 dark:bg-emerald-950/10' : ''}>
                  <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">{r.full_name ?? `Участник #${r.id}`}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{r.birth_date}</td>
                  <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">{r.days_until_birthday} дн.</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{r.subscribers_count}</td>
                  <td className="px-4 py-3">
                    {r.is_sent ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:text-emerald-300">
                        <CheckCircle2 className="size-3" aria-hidden />
                        Отправлено
                      </span>
                    ) : (
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">Не отправлено</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      variant="outline"
                      className="gap-1.5 py-2 text-xs"
                      onClick={() => {
                        setModalRow(r)
                        setLink('')
                        setLinkError(null)
                      }}
                    >
                      <Send className="size-3.5" aria-hidden />
                      Подготовить группу
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {modalRow ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setModalRow(null)
          }}
        >
          <div className="w-full max-w-lg rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-950">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">
              Рассылка ссылки для подписчиков {sendTitle}
            </h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Введите ссылку на группу Telegram. Сообщение уйдет всем подписчикам, кроме именинника.
            </p>
            <div className="mt-4">
              <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Ссылка на группу</label>
              <input
                type="url"
                value={link}
                onChange={(e) => setLink(e.target.value)}
                placeholder="https://t.me/..."
                className="w-full rounded-xl border border-zinc-200/80 bg-white px-3 py-2 text-sm text-zinc-900 outline-none ring-orange-500/25 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </div>
            {linkError ? <p className="mt-2 text-sm text-red-600 dark:text-red-400">{linkError}</p> : null}
            <div className="mt-5 flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setModalRow(null)} disabled={sending}>
                Отмена
              </Button>
              <Button type="button" onClick={() => void submit()} disabled={sending}>
                {sending
                  ? 'Рассылаю...'
                  : `Разослать всем (${modalRow.subscribers_count} чел.)`}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

