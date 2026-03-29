import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ListPlus, Trash2, Upload, UserRound } from 'lucide-react'

import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import type { WishlistItem } from '@/types/publicUser'

function mapAvatarUploadError(detail: unknown): string {
  const code =
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail) && detail[0] && typeof detail[0] === 'object' && 'msg' in detail[0]
        ? String((detail[0] as { msg?: string }).msg)
        : ''
  const messages: Record<string, string> = {
    invalid_file_type: 'Нужен файл в формате JPEG или PNG.',
    file_too_large: 'Размер файла не больше 5 МБ.',
    empty_file: 'Файл пустой — выберите другое изображение.',
    invalid_image_payload: 'Файл не похож на корректное изображение JPEG или PNG.',
    content_type_mismatch: 'Тип файла не совпадает с содержимым.',
  }
  return messages[code] ?? 'Не удалось загрузить фото. Попробуйте другой файл.'
}

export function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const avatarInputRef = useRef<HTMLInputElement>(null)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [avatarError, setAvatarError] = useState<string | null>(null)
  const [avatarBust, setAvatarBust] = useState(0)
  const [avatarImgFailed, setAvatarImgFailed] = useState(false)
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

  useEffect(() => {
    setAvatarImgFailed(false)
  }, [user?.has_avatar, user?.id, avatarBust])

  const openAvatarPicker = () => {
    setAvatarError(null)
    avatarInputRef.current?.click()
  }

  const onAvatarFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !user) return
    setAvatarError(null)
    setAvatarUploading(true)
    try {
      const body = new FormData()
      body.append('file', file)
      const res = await fetch('/api/users/me/avatar', {
        method: 'PATCH',
        credentials: 'include',
        body,
      })
      if (!res.ok) {
        let detail: unknown
        try {
          detail = (await res.json()) as { detail?: unknown }
          detail = (detail as { detail?: unknown }).detail
        } catch {
          detail = undefined
        }
        setAvatarError(mapAvatarUploadError(detail))
        return
      }
      await refreshUser()
      setAvatarBust((n) => n + 1)
    } catch {
      setAvatarError('Сеть недоступна или сервер не ответил.')
    } finally {
      setAvatarUploading(false)
    }
  }

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
          </CardHeader>
          <div className="border-b border-zinc-200/80 pb-6 dark:border-zinc-800">
            <input
              ref={avatarInputRef}
              type="file"
              accept="image/jpeg,image/png,.jpg,.jpeg,.png"
              className="sr-only"
              aria-label="Выбор файла аватарки"
              onChange={(ev) => void onAvatarFile(ev)}
              disabled={avatarUploading}
            />
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
              <div className="relative shrink-0">
                {user?.has_avatar && !avatarImgFailed ? (
                  <img
                    src={`/api/users/${user.id}/avatar?v=${avatarBust}`}
                    alt=""
                    className="size-24 rounded-2xl border border-zinc-200/80 object-cover shadow-sm dark:border-zinc-700"
                    onError={() => setAvatarImgFailed(true)}
                  />
                ) : (
                  <div
                    className="flex size-24 items-center justify-center rounded-2xl border border-dashed border-zinc-300 bg-zinc-100/80 text-zinc-400 dark:border-zinc-600 dark:bg-zinc-900/50 dark:text-zinc-500"
                    aria-hidden
                  >
                    <UserRound className="size-12" strokeWidth={1.25} />
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1 space-y-2">
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  Выберите файл с устройства: <strong className="font-medium text-zinc-800 dark:text-zinc-200">JPEG или PNG</strong>, не больше{' '}
                  <strong className="font-medium text-zinc-800 dark:text-zinc-200">5 МБ</strong>. Аватарка не подтягивается из Telegram автоматически.
                </p>
                <Button
                  type="button"
                  variant="outline"
                  className="gap-2 py-2 text-xs"
                  onClick={openAvatarPicker}
                  disabled={avatarUploading}
                >
                  <Upload className="size-4" aria-hidden />
                  {user?.has_avatar ? 'Сменить фото' : 'Загрузить фото'}
                </Button>
                {avatarUploading ? (
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Загрузка…</p>
                ) : null}
                {avatarError ? (
                  <p className="text-sm text-red-600 dark:text-red-400" role="alert">
                    {avatarError}
                  </p>
                ) : null}
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Имя и дату рождения можно изменить на{' '}
                  <Link
                    to="/setup-profile"
                    className="font-medium text-orange-600 underline-offset-2 hover:underline dark:text-orange-400"
                  >
                    странице настройки профиля
                  </Link>
                  .
                </p>
              </div>
            </div>
          </div>
          <dl className="space-y-3 pt-4 text-sm">
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
