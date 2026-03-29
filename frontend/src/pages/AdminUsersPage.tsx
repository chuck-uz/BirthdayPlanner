import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Ban, FlaskConical, LockOpen, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/contexts/ToastContext'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import type {
  AdminDeleteAllTestUsersOut,
  AdminUserListItem,
} from '@/types/admin'

export function AdminUsersPage() {
  const { user: me } = useAuth()
  const { showToast } = useToast()
  const [rows, setRows] = useState<AdminUserListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [deletingTests, setDeletingTests] = useState(false)
  const [testCount, setTestCount] = useState(1)
  const [togglingId, setTogglingId] = useState<number | null>(null)
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data } = await api.get<AdminUserListItem[]>('/api/admin/users')
        if (!cancelled) {
          setRows(data)
          setError(null)
        }
      } catch {
        if (!cancelled) {
          setRows(null)
          setError('Не удалось загрузить список (нужны права администратора).')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const loadUsers = async () => {
    try {
      const { data } = await api.get<AdminUserListItem[]>('/api/admin/users')
      setRows(data)
      setError(null)
    } catch {
      setError('Не удалось обновить список.')
    }
  }

  const toggleBlocked = async (u: AdminUserListItem) => {
    if (me && u.id === me.id) {
      showToast('Нельзя заблокировать самого себя')
      return
    }
    setTogglingId(u.id)
    try {
      const next = !u.is_blocked
      await api.patch(`/api/admin/users/${u.id}`, {
        is_blocked: next,
      })
      await loadUsers()
      showToast(next ? 'Пользователь заблокирован' : 'Пользователь разблокирован')
      setError(null)
    } catch {
      showToast('Не удалось изменить статус')
    } finally {
      setTogglingId(null)
    }
  }

  const deleteAllTestUsers = async () => {
    if (
      !window.confirm(
        'Удалить всех тестовых пользователей (is_test)? Подписки и связанные данные будут удалены.',
      )
    ) {
      return
    }
    setDeletingTests(true)
    try {
      const { data } = await api.delete<AdminDeleteAllTestUsersOut>('/api/admin/users/test')
      showToast(`Удалено тестовых пользователей: ${data.deleted_count}`)
      await loadUsers()
      setError(null)
    } catch {
      showToast('Не удалось удалить тестовых пользователей')
    } finally {
      setDeletingTests(false)
    }
  }

  const createTestUsers = async () => {
    setCreating(true)
    try {
      const { data } = await api.post<AdminUserListItem[]>('/api/admin/users/test', {
        count: testCount,
      })
      setRows((prev) => (prev ? [...data, ...prev] : data))
      setError(null)
    } catch {
      setError('Не удалось создать тестовых пользователей.')
    } finally {
      setCreating(false)
    }
  }

  const deleteUser = async (u: AdminUserListItem) => {
    if (me && u.id === me.id) {
      showToast('Нельзя удалить самого себя')
      return
    }
    if (!window.confirm(`Удалить пользователя "${u.full_name ?? `#${u.id}`}"?`)) return
    setDeletingUserId(u.id)
    try {
      await api.delete(`/api/admin/users/${u.id}`)
      showToast('Пользователь удалён')
      await loadUsers()
      setError(null)
    } catch {
      showToast('Не удалось удалить пользователя')
    } finally {
      setDeletingUserId(null)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">Пользователи</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Блокировка, карточка пользователя и тестовые записи.
        </p>
      </div>

      <div className="flex flex-col gap-3 rounded-2xl border border-dashed border-zinc-300/80 bg-zinc-50/50 p-4 dark:border-zinc-700 dark:bg-zinc-900/30">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-lg bg-violet-500/15 text-violet-700 dark:bg-violet-500/20 dark:text-violet-300">
            <FlaskConical className="size-5" aria-hidden />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">Тестовые пользователи</p>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              Создаются записи с вымышленным Telegram ID — войти через Telegram Login нельзя. Удобно для
              проверки подписок и сценариев.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-zinc-600 dark:text-zinc-400">
            Количество
            <input
              type="number"
              min={1}
              max={20}
              value={testCount}
              onChange={(e) => {
                const n = Number.parseInt(e.target.value, 10)
                if (Number.isNaN(n)) {
                  setTestCount(1)
                  return
                }
                setTestCount(Math.min(20, Math.max(1, n)))
              }}
              className="w-24 rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
            />
          </label>
          <Button type="button" disabled={creating} onClick={() => void createTestUsers()}>
            {creating ? 'Создание…' : 'Создать тестовых'}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={deletingTests}
            onClick={() => void deleteAllTestUsers()}
            className="border-red-300 text-red-800 hover:bg-red-50 dark:border-red-900 dark:text-red-200 dark:hover:bg-red-950/40"
          >
            {deletingTests ? 'Удаление…' : 'Удалить всех тестовых'}
          </Button>
          <button
            type="button"
            className="text-xs text-zinc-500 underline hover:text-zinc-700 dark:hover:text-zinc-300"
            onClick={() => void loadUsers()}
          >
            Обновить список
          </button>
        </div>
      </div>

      {error ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      ) : null}

      {rows === null && !error ? (
        <div className="h-48 animate-pulse rounded-2xl bg-zinc-200/60 dark:bg-zinc-800/60" />
      ) : rows && rows.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Пользователей пока нет.</p>
      ) : rows ? (
        <div className="overflow-x-auto rounded-2xl border border-zinc-200/80 bg-white/60 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/50">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-zinc-200/80 bg-zinc-50/80 text-xs font-medium uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-400">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Telegram</th>
                <th className="px-4 py-3">ФИО</th>
                <th className="px-4 py-3">Дата рождения</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3">Тип</th>
                <th className="px-4 py-3 text-right">Блокировка</th>
                <th className="px-4 py-3 text-right">Удаление</th>
                <th className="px-4 py-3 text-right">Карточка</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {rows.map((u) => (
                <tr key={u.id} className="transition hover:bg-zinc-50/80 dark:hover:bg-zinc-900/40">
                  <td className="px-4 py-3 font-mono text-zinc-600 dark:text-zinc-400">{u.id}</td>
                  <td className="px-4 py-3 font-mono text-xs text-zinc-700 dark:text-zinc-300">
                    {u.telegram_id}
                  </td>
                  <td className="max-w-[200px] truncate px-4 py-3 text-zinc-900 dark:text-zinc-100">
                    {u.full_name ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                    {u.birth_date ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    {u.is_blocked ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-800 dark:text-red-300">
                        <Ban className="size-3" aria-hidden />
                        Заблокирован
                      </span>
                    ) : (
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">Активен</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {u.is_test ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/15 px-2 py-0.5 text-xs font-medium text-violet-800 dark:text-violet-300">
                        <FlaskConical className="size-3" aria-hidden />
                        Тест
                      </span>
                    ) : (
                      <span className="text-xs text-zinc-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      variant="outline"
                      className="gap-1.5 py-1.5 text-xs"
                      disabled={togglingId === u.id || (me !== null && u.id === me.id)}
                      onClick={() => void toggleBlocked(u)}
                    >
                      {u.is_blocked ? (
                        <>
                          <LockOpen className="size-3.5" aria-hidden />
                          Разблокировать
                        </>
                      ) : (
                        <>
                          <Ban className="size-3.5" aria-hidden />
                          Заблокировать
                        </>
                      )}
                    </Button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      variant="outline"
                      className="gap-1.5 py-1.5 text-xs border-red-300 text-red-800 hover:bg-red-50 dark:border-red-900 dark:text-red-200 dark:hover:bg-red-950/40"
                      disabled={deletingUserId === u.id || (me !== null && u.id === me.id)}
                      onClick={() => void deleteUser(u)}
                    >
                      <Trash2 className="size-3.5" aria-hidden />
                      {deletingUserId === u.id ? 'Удаление…' : 'Удалить'}
                    </Button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/admin/users/${u.id}`}
                      className="font-medium text-orange-600 hover:underline dark:text-orange-400"
                    >
                      Открыть
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
