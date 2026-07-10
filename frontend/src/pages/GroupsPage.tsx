import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Shield, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { groupErrorMessage, membersCountLabel } from '@/types/group'
import type { Group } from '@/types/group'

export function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loadGroups = async () => {
    setLoading(true)
    try {
      const { data } = await api.get<Group[]>('/api/groups')
      setGroups(data)
    } catch {
      setGroups([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadGroups()
  }, [])

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    setCreating(true)
    setError(null)
    try {
      const { data } = await api.post<Group>('/api/groups', { name: trimmed })
      setGroups((prev) => [data, ...prev])
      setName('')
      setShowForm(false)
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      setError(groupErrorMessage(detail))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
            Группы
          </h1>
          <p className="mt-1 text-zinc-600 dark:text-zinc-400">
            Приватные группы для совместной организации подарков и поздравлений.
          </p>
        </div>
        <Button type="button" onClick={() => setShowForm((v) => !v)} className="gap-1.5 self-start sm:self-auto">
          <Plus className="size-4" aria-hidden />
          Создать группу
        </Button>
      </div>

      {showForm ? (
        <Card>
          <form onSubmit={(e) => void onCreate(e)} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="flex-1">
              <span className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Название группы
              </span>
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Например, Семья"
                className="w-full rounded-xl border border-zinc-300/80 bg-white/70 px-3 py-2.5 text-sm text-zinc-900 outline-none ring-orange-500/40 transition focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900/60 dark:text-zinc-100"
              />
            </label>
            <Button type="submit" disabled={creating || !name.trim()}>
              {creating ? 'Создаём…' : 'Создать'}
            </Button>
          </form>
          {error ? (
            <p className="mt-3 text-sm text-red-600 dark:text-red-400" role="alert">
              {error}
            </p>
          ) : null}
        </Card>
      ) : null}

      {loading ? (
        <div className="rounded-xl border border-zinc-200/60 py-10 text-center text-sm text-zinc-500 dark:border-zinc-800">
          Загрузка…
        </div>
      ) : groups.length === 0 ? (
        <div className="flex flex-col items-center rounded-2xl border border-dashed border-zinc-300/90 py-14 text-center dark:border-zinc-700">
          <Users className="mb-3 size-10 text-zinc-400 dark:text-zinc-500" aria-hidden />
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Пока нет групп — создайте первую или вступите по приглашению.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((g) => (
            <Link key={g.id} to={`/groups/${g.id}`}>
              <Card className="h-full transition hover:bg-white/70 dark:hover:bg-black/50">
                <CardHeader className="flex-row items-center justify-between gap-2">
                  <div>
                    <CardTitle>{g.name}</CardTitle>
                    <CardDescription>{membersCountLabel(g.member_count)}</CardDescription>
                  </div>
                  {g.my_role === 'admin' ? (
                    <span
                      title="Вы администратор"
                      className="flex size-8 shrink-0 items-center justify-center rounded-full bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400"
                    >
                      <Shield className="size-4" aria-hidden />
                    </span>
                  ) : null}
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
