import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, FlaskConical, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/contexts/ToastContext'
import { api } from '@/lib/api'
import { wishlistPhotoUrl } from '@/lib/wishlistPhotoUrl'
import type { AdminUserDetail } from '@/types/admin'

export function AdminUserDetailPage() {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const idNum = userId ? Number.parseInt(userId, 10) : NaN

  const [data, setData] = useState<AdminUserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fullName, setFullName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [isBlocked, setIsBlocked] = useState(false)
  const [saving, setSaving] = useState(false)
  const [photoRev, setPhotoRev] = useState(0)

  const load = useCallback(async () => {
    if (Number.isNaN(idNum) || idNum < 1) {
      setError('Некорректный id')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data: d } = await api.get<AdminUserDetail>(`/api/admin/users/${idNum}`)
      setData(d)
      setFullName(d.full_name?.trim() ?? '')
      setBirthDate(d.birth_date ?? '')
      setIsBlocked(d.is_blocked)
    } catch {
      setData(null)
      setError('Пользователь не найден или нет доступа')
    } finally {
      setLoading(false)
    }
  }, [idNum])

  useEffect(() => {
    void load()
  }, [load])

  const save = async () => {
    if (!data || Number.isNaN(idNum)) return
    const patch: {
      full_name?: string
      birth_date?: string
      is_blocked?: boolean
    } = {}
    const nameTrim = fullName.trim().replace(/\s+/g, ' ')
    if (nameTrim !== (data.full_name?.trim() ?? '')) {
      patch.full_name = nameTrim
    }
    if (birthDate !== (data.birth_date ?? '')) {
      if (birthDate) {
        patch.birth_date = birthDate
      }
    }
    if (isBlocked !== data.is_blocked) {
      patch.is_blocked = isBlocked
    }
    if (Object.keys(patch).length === 0) {
      showToast('Нет изменений')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const { data: updated } = await api.patch<AdminUserDetail>(`/api/admin/users/${idNum}`, patch)
      setData(updated)
      setFullName(updated.full_name?.trim() ?? '')
      setBirthDate(updated.birth_date ?? '')
      setIsBlocked(updated.is_blocked)
      setPhotoRev((r) => r + 1)
      showToast('Сохранено')
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 422) {
        const det = e.response.data?.detail
        const msg = Array.isArray(det)
          ? det.map((x: { msg?: string }) => x.msg).filter(Boolean).join(' ')
          : typeof det === 'string'
            ? det
            : 'Проверьте данные'
        setError(msg)
      } else if (axios.isAxiosError(e) && e.response?.data?.detail === 'cannot_block_self') {
        setError('Нельзя заблокировать самого себя')
        setIsBlocked(false)
      } else {
        setError('Не удалось сохранить')
      }
    } finally {
      setSaving(false)
    }
  }

  const deleteWishlist = async (wishlistId: number) => {
    if (!data || !window.confirm('Удалить пункт вишлиста и фото?')) return
    try {
      await api.delete(`/api/admin/users/${data.id}/wishlists/${wishlistId}`)
      showToast('Пункт вишлиста удалён')
      void load()
    } catch {
      setError('Не удалось удалить пункт')
    }
  }

  if (Number.isNaN(idNum) || idNum < 1) {
    return (
      <p className="text-sm text-red-600 dark:text-red-400">
        Некорректная ссылка.{' '}
        <Link to="/admin/users" className="underline">
          К списку
        </Link>
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <button
          type="button"
          onClick={() => navigate('/admin/users')}
          className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-zinc-600 transition hover:text-orange-600 dark:text-zinc-400 dark:hover:text-orange-400"
        >
          <ArrowLeft className="size-4" aria-hidden />
          К списку пользователей
        </button>
        {loading ? (
          <div className="h-10 w-48 animate-pulse rounded-lg bg-zinc-200/80 dark:bg-zinc-800" />
        ) : data ? (
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
            Пользователь #{data.id}
          </h1>
        ) : (
          <h1 className="text-3xl font-semibold text-zinc-900 dark:text-white">Пользователь</h1>
        )}
      </div>

      {error && !loading ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      ) : null}

      {data && !loading ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Данные</CardTitle>
              <div className="flex flex-col gap-2 text-sm text-zinc-500 dark:text-zinc-400">
                {data.is_test ? (
                  <span className="flex w-fit items-center gap-1 rounded-full bg-violet-500/15 px-2 py-0.5 text-xs font-medium text-violet-800 dark:text-violet-300">
                    <FlaskConical className="size-3" aria-hidden />
                    Тестовый пользователь (вход через Telegram недоступен)
                  </span>
                ) : null}
                <p>
                  Telegram ID: <span className="font-mono">{data.telegram_id}</span> · Подписчиков на ДР:{' '}
                  {data.subscribers_count} · Подписок: {data.subscribing_count} · Бот:{' '}
                  {data.is_bot_active ? 'да' : 'нет'}
                </p>
              </div>
            </CardHeader>
            <div className="flex flex-col gap-4 px-6 pb-6">
              <div className="flex flex-wrap gap-6">
                <div className="relative h-28 w-28 shrink-0 overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800">
                  {data.has_avatar ? (
                    <img
                      src={`/api/users/${data.id}/avatar?v=${photoRev}`}
                      alt=""
                      className="size-full object-cover"
                    />
                  ) : (
                    <div className="flex size-full items-center justify-center text-xs text-zinc-400">
                      Нет фото
                    </div>
                  )}
                </div>
                <div className="min-w-[240px] flex-1 space-y-3">
                  <div>
                    <label htmlFor="adm-fn" className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
                      ФИО
                    </label>
                    <input
                      id="adm-fn"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full rounded-xl border border-zinc-200/80 bg-white/80 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
                    />
                  </div>
                  <div>
                    <label htmlFor="adm-bd" className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
                      Дата рождения
                    </label>
                    <input
                      id="adm-bd"
                      type="date"
                      value={birthDate}
                      onChange={(e) => setBirthDate(e.target.value)}
                      className="w-full rounded-xl border border-zinc-200/80 bg-white/80 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
                    />
                  </div>
                  <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-800 dark:text-zinc-200">
                    <input
                      type="checkbox"
                      checked={isBlocked}
                      onChange={(e) => setIsBlocked(e.target.checked)}
                      className="rounded border-zinc-300"
                    />
                    Заблокировать доступ к приложению
                  </label>
                </div>
              </div>
              <Button type="button" onClick={() => void save()} disabled={saving}>
                {saving ? 'Сохранение…' : 'Сохранить изменения'}
              </Button>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Вишлист</CardTitle>
              <CardDescription>Пункты пользователя — можно удалить</CardDescription>
            </CardHeader>
            <ul className="space-y-3 px-6 pb-6">
              {data.wishlists.length === 0 ? (
                <li className="text-sm text-zinc-500 dark:text-zinc-400">Пусто</li>
              ) : (
                data.wishlists.map((w) => (
                  <li
                    key={w.id}
                    className="flex items-center gap-3 rounded-xl border border-zinc-200/80 p-3 dark:border-zinc-800"
                  >
                    <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-zinc-200 dark:bg-zinc-700">
                      {w.has_photo ? (
                        <img
                          src={wishlistPhotoUrl(w.id, photoRev)}
                          alt=""
                          className="size-full object-cover"
                        />
                      ) : null}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-zinc-900 dark:text-zinc-100">{w.title}</p>
                      {w.description ? (
                        <p className="line-clamp-2 text-xs text-zinc-600 dark:text-zinc-400">{w.description}</p>
                      ) : null}
                    </div>
                    <button
                      type="button"
                      onClick={() => void deleteWishlist(w.id)}
                      className="shrink-0 rounded-lg p-2 text-zinc-400 transition hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400"
                      aria-label="Удалить пункт"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </li>
                ))
              )}
            </ul>
          </Card>
        </>
      ) : null}
    </div>
  )
}
