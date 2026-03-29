import { useCallback, useEffect, useState } from 'react'
import { ListPlus, Trash2 } from 'lucide-react'

import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import type { WishlistItem } from '@/types/publicUser'

export function ProfilePage() {
  const { user } = useAuth()
  const [items, setItems] = useState<WishlistItem[]>([])
  const [wishLoading, setWishLoading] = useState(true)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)

  const loadWishlists = useCallback(async () => {
    setWishLoading(true)
    try {
      const { data } = await api.get<WishlistItem[]>('/api/users/me/wishlists')
      setItems(data)
    } catch {
      setItems([])
    } finally {
      setWishLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadWishlists()
  }, [loadWishlists])

  const addItem = async () => {
    const title = draft.trim()
    if (!title || saving) return
    setSaving(true)
    try {
      const { data } = await api.post<WishlistItem>('/api/users/me/wishlists', { title })
      setItems((prev) => [data, ...prev])
      setDraft('')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id: number) => {
    try {
      await api.delete(`/api/users/me/wishlists/${id}`)
      setItems((prev) => prev.filter((x) => x.id !== id))
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
          Личный кабинет
        </h1>
        <p className="mt-1 text-zinc-600 dark:text-zinc-400">
          Профиль из сессии и вишлист — его видят другие участники в вашем профиле.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Профиль</CardTitle>
            <CardDescription>Данные из Telegram и учётной записи</CardDescription>
          </CardHeader>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-4 border-b border-zinc-200/80 py-2 dark:border-zinc-800">
              <dt className="text-zinc-500 dark:text-zinc-400">Имя</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                {user?.full_name ?? '—'}
              </dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-zinc-200/80 py-2 dark:border-zinc-800">
              <dt className="text-zinc-500 dark:text-zinc-400">Telegram ID</dt>
              <dd className="font-mono text-zinc-800 dark:text-zinc-200">
                {user?.telegram_id ?? '—'}
              </dd>
            </div>
            <div className="flex justify-between gap-4 py-2">
              <dt className="text-zinc-500 dark:text-zinc-400">Дата рождения</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                {user?.birth_date ?? 'Не указана'}
              </dd>
            </div>
          </dl>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Вишлист</CardTitle>
            <CardDescription>Желания для друзей</CardDescription>
          </CardHeader>
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && void addItem()}
                placeholder="Новый пункт…"
                disabled={saving}
                className="flex-1 rounded-xl border border-zinc-200/80 bg-white/60 px-3 py-2 text-sm text-zinc-900 shadow-inner outline-none ring-orange-500/25 placeholder:text-zinc-400 focus:border-orange-500 focus:ring-2 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950/40 dark:text-zinc-100 dark:placeholder:text-zinc-500"
              />
              <Button
                type="button"
                onClick={() => void addItem()}
                disabled={saving}
                className="shrink-0 gap-1"
              >
                <ListPlus className="size-4" aria-hidden />
                Добавить
              </Button>
            </div>
            {wishLoading ? (
              <div className="rounded-xl border border-zinc-200/60 py-10 text-center text-sm text-zinc-500 dark:border-zinc-800">
                Загрузка…
              </div>
            ) : (
              <ul className="space-y-2">
                {items.length === 0 ? (
                  <li className="rounded-xl border border-dashed border-zinc-300/80 py-8 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
                    Пока пусто — добавьте первый пункт.
                  </li>
                ) : (
                  items.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center justify-between gap-2 rounded-xl border border-white/40 bg-white/40 px-3 py-2.5 text-sm dark:border-white/10 dark:bg-zinc-950/30"
                    >
                      <span className="text-zinc-800 dark:text-zinc-200">{item.title}</span>
                      <button
                        type="button"
                        onClick={() => void remove(item.id)}
                        className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400"
                        aria-label="Удалить"
                      >
                        <Trash2 className="size-4" />
                      </button>
                    </li>
                  ))
                )}
              </ul>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
