import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Camera, Gift, Plus, UserRound } from 'lucide-react'

import { WishlistItemCard } from '@/components/wishlist/WishlistItemCard'
import { WishlistItemModal } from '@/components/wishlist/WishlistItemModal'
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
  const [wishPhotoRev, setWishPhotoRev] = useState(0)
  const [wishModalOpen, setWishModalOpen] = useState(false)
  const [wishModalMode, setWishModalMode] = useState<'create' | 'edit'>('create')
  const [wishModalItem, setWishModalItem] = useState<WishlistItem | null>(null)

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

  const openCreateWishlist = () => {
    setWishModalMode('create')
    setWishModalItem(null)
    setWishModalOpen(true)
  }

  const openEditWishlist = (item: WishlistItem) => {
    setWishModalMode('edit')
    setWishModalItem(item)
    setWishModalOpen(true)
  }

  const onWishSaved = (item: WishlistItem, mode: 'create' | 'edit') => {
    if (mode === 'create') {
      setItems((prev) => [item, ...prev])
    } else {
      setItems((prev) => prev.map((x) => (x.id === item.id ? item : x)))
    }
    setWishPhotoRev((r) => r + 1)
  }

  const removeWishlist = async (id: number) => {
    try {
      await api.delete(`/api/users/me/wishlists/${id}`)
      setItems((prev) => prev.filter((x) => x.id !== id))
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <WishlistItemModal
        open={wishModalOpen}
        mode={wishModalMode}
        initial={wishModalItem}
        photoRev={wishPhotoRev}
        onClose={() => setWishModalOpen(false)}
        onSaved={onWishSaved}
      />
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
          Личный кабинет
        </h1>
        <p className="mt-1 text-zinc-600 dark:text-zinc-400">
          Профиль из сессии и вишлист — его видят другие участники в вашем профиле.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 lg:grid-rows-[auto_auto]">
        <Card className="lg:row-start-1">
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
                    className="size-28 rounded-2xl border border-zinc-200/80 object-cover shadow-sm dark:border-zinc-700"
                    onError={() => setAvatarImgFailed(true)}
                  />
                ) : (
                  <div
                    className="flex size-28 items-center justify-center rounded-2xl border border-dashed border-zinc-300 bg-zinc-100/80 text-zinc-400 dark:border-zinc-600 dark:bg-zinc-900/50 dark:text-zinc-500"
                    aria-hidden
                  >
                    <UserRound className="size-14" strokeWidth={1.25} />
                  </div>
                )}
                <button
                  type="button"
                  onClick={openAvatarPicker}
                  disabled={avatarUploading}
                  title={user?.has_avatar ? 'Сменить фото' : 'Загрузить фото'}
                  className="absolute -bottom-1 -right-1 flex size-9 items-center justify-center rounded-full border-2 border-white bg-orange-600 text-white shadow-md transition hover:bg-orange-500 disabled:opacity-50 dark:border-zinc-900 dark:bg-orange-500 dark:hover:bg-orange-400"
                  aria-label={user?.has_avatar ? 'Сменить фото профиля' : 'Загрузить фото профиля'}
                >
                  <Camera className="size-4" aria-hidden />
                </button>
              </div>
              <div className="min-w-0 flex-1 space-y-2">
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  Нажмите на иконку камеры, чтобы выбрать фото: <strong className="font-medium text-zinc-800 dark:text-zinc-200">JPEG или PNG</strong>, до{' '}
                  <strong className="font-medium text-zinc-800 dark:text-zinc-200">5 МБ</strong>.
                </p>
                {avatarUploading ? (
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Загрузка…</p>
                ) : null}
                {avatarError ? (
                  <p className="text-sm text-red-600 dark:text-red-400" role="alert">
                    {avatarError}
                  </p>
                ) : null}
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  ФИО и дату рождения — в{' '}
                  <Link
                    to="/profile/settings"
                    className="font-medium text-orange-600 underline-offset-2 hover:underline dark:text-orange-400"
                  >
                    настройках профиля
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

        <Card className="lg:col-span-2 lg:row-start-2">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>Вишлист</CardTitle>
              <CardDescription>Желания для друзей — с фото и ссылкой на магазин</CardDescription>
            </div>
            <Button type="button" onClick={openCreateWishlist} className="shrink-0 gap-1.5 self-start sm:self-auto">
              <Plus className="size-4" aria-hidden />
              Добавить подарок
            </Button>
          </CardHeader>
          {wishLoading ? (
            <div className="px-6 pb-8">
              <div className="rounded-xl border border-zinc-200/60 py-10 text-center text-sm text-zinc-500 dark:border-zinc-800">
                Загрузка…
              </div>
            </div>
          ) : items.length === 0 ? (
            <div className="px-6 pb-8">
              <div className="flex flex-col items-center rounded-2xl border border-dashed border-zinc-300/90 py-14 text-center dark:border-zinc-700">
                <Gift className="mb-3 size-10 text-zinc-400 dark:text-zinc-500" aria-hidden />
                <p className="text-sm text-zinc-600 dark:text-zinc-400">Пока пусто — добавьте первый подарок.</p>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 px-6 pb-8 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((item) => (
                <WishlistItemCard
                  key={item.id}
                  item={item}
                  photoRev={wishPhotoRev}
                  variant="owner"
                  onEdit={openEditWishlist}
                  onDelete={(id) => void removeWishlist(id)}
                />
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
