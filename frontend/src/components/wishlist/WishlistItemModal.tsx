import { useEffect, useId, useRef, useState } from 'react'
import { X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { wishlistPhotoUrl } from '@/lib/wishlistPhotoUrl'
import type { WishlistItem } from '@/types/publicUser'

function mapUploadError(detail: unknown): string {
  const code =
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail) && detail[0] && typeof detail[0] === 'object' && 'msg' in detail[0]
        ? String((detail[0] as { msg?: string }).msg)
        : ''
  const messages: Record<string, string> = {
    invalid_file_type: 'Нужен файл в формате JPEG или PNG.',
    file_too_large: 'Размер файла не больше 5 МБ.',
    empty_file: 'Пустой файл.',
    invalid_image_payload: 'Файл не похож на изображение JPEG или PNG.',
    content_type_mismatch: 'Тип файла не совпадает с содержимым.',
    invalid_link_url: 'Некорректная ссылка (нужен полный URL, например https://…).',
    empty_title: 'Укажите название.',
  }
  return messages[code] ?? 'Не удалось сохранить. Проверьте данные и попробуйте снова.'
}

type WishlistItemModalProps = {
  open: boolean
  mode: 'create' | 'edit'
  initial: WishlistItem | null
  photoRev: number
  onClose: () => void
  onSaved: (item: WishlistItem, mode: 'create' | 'edit') => void
}

export function WishlistItemModal({
  open,
  mode,
  initial,
  photoRev,
  onClose,
  onSaved,
}: WishlistItemModalProps) {
  const titleId = useId()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [linkUrl, setLinkUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  /** Только локальный blob-превью; картинка с API не хранится здесь */
  const [blobPreview, setBlobPreview] = useState<string | null>(null)
  const [clearPhoto, setClearPhoto] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setError(null)
    setFile(null)
    setClearPhoto(false)
    setBlobPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return null
    })
    if (mode === 'edit' && initial) {
      setTitle(initial.title)
      setDescription(initial.description ?? '')
      setLinkUrl(initial.link_url ?? '')
    } else {
      setTitle('')
      setDescription('')
      setLinkUrl('')
    }
  }, [open, mode, initial?.id])

  useEffect(() => {
    if (!file) {
      setBlobPreview(null)
      return
    }
    const url = URL.createObjectURL(file)
    setBlobPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  if (!open) return null

  const displayPreview =
    blobPreview ??
    (mode === 'edit' && initial?.has_photo && !clearPhoto
      ? wishlistPhotoUrl(initial.id, photoRev)
      : null)

  const onPickFile = () => fileInputRef.current?.click()

  const submit = async () => {
    setError(null)
    const t = title.trim()
    if (!t) {
      setError('Укажите название.')
      return
    }
    setSaving(true)
    try {
      const fd = new FormData()
      fd.append('title', t)
      fd.append('description', description.trim())
      if (linkUrl.trim()) fd.append('link_url', linkUrl.trim())
      if (file) fd.append('file', file)
      if (mode === 'edit') {
        fd.append('clear_photo', clearPhoto ? 'true' : 'false')
      }
      const url =
        mode === 'create'
          ? '/api/users/me/wishlists'
          : `/api/users/me/wishlists/${initial!.id}`
      const res = await fetch(url, {
        method: mode === 'create' ? 'POST' : 'PATCH',
        credentials: 'include',
        body: fd,
      })
      if (!res.ok) {
        let detail: unknown
        try {
          const j = (await res.json()) as { detail?: unknown }
          detail = j.detail
        } catch {
          detail = undefined
        }
        setError(mapUploadError(detail))
        return
      }
      const item = (await res.json()) as WishlistItem
      onSaved(item, mode)
      onClose()
    } catch {
      setError('Сеть недоступна или сервер не ответил.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="max-h-[min(90vh,720px)] w-full max-w-lg overflow-y-auto rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-950">
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id={titleId} className="text-lg font-semibold text-zinc-900 dark:text-white">
            {mode === 'create' ? 'Новый подарок' : 'Редактировать подарок'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-800 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
            aria-label="Закрыть"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <label htmlFor={`${titleId}-name`} className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
              Название *
            </label>
            <input
              id={`${titleId}-name`}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-xl border border-zinc-200/80 bg-white px-3 py-2 text-sm text-zinc-900 outline-none ring-orange-500/25 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              placeholder="Например, набор для кофе"
            />
          </div>
          <div>
            <label htmlFor={`${titleId}-desc`} className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
              Описание
            </label>
            <textarea
              id={`${titleId}-desc`}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full resize-y rounded-xl border border-zinc-200/80 bg-white px-3 py-2 text-sm text-zinc-900 outline-none ring-orange-500/25 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              placeholder="Пожелания по цвету, размеру…"
            />
          </div>
          <div>
            <label htmlFor={`${titleId}-link`} className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
              Ссылка на магазин
            </label>
            <input
              id={`${titleId}-link`}
              type="url"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              className="w-full rounded-xl border border-zinc-200/80 bg-white px-3 py-2 text-sm text-zinc-900 outline-none ring-orange-500/25 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              placeholder="https://…"
            />
          </div>

          <div>
            <span className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Фото референса</span>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,.jpg,.jpeg,.png"
              className="sr-only"
              aria-label="Файл изображения"
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null
                e.target.value = ''
                setFile(f)
                if (f) setClearPhoto(false)
              }}
            />
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start">
              <div className="relative h-32 w-full max-w-[200px] shrink-0 overflow-hidden rounded-xl border border-zinc-200 bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800">
                {displayPreview ? (
                  <img src={displayPreview} alt="" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-xs text-zinc-400">Нет фото</div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Button type="button" variant="outline" className="w-fit py-2 text-xs" onClick={onPickFile}>
                  Выбрать файл
                </Button>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">JPEG или PNG, до 5 МБ. На сервере сожмём до 800px.</p>
                {mode === 'edit' && initial?.has_photo ? (
                  <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400">
                    <input
                      type="checkbox"
                      checked={clearPhoto}
                      onChange={(e) => {
                        setClearPhoto(e.target.checked)
                        if (e.target.checked) setFile(null)
                      }}
                      className="rounded border-zinc-300"
                    />
                    Удалить текущее фото
                  </label>
                ) : null}
              </div>
            </div>
          </div>

          {error ? (
            <p className="text-sm text-red-600 dark:text-red-400" role="alert">
              {error}
            </p>
          ) : null}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose} disabled={saving}>
              Отмена
            </Button>
            <Button type="button" onClick={() => void submit()} disabled={saving}>
              {saving ? 'Сохранение…' : 'Сохранить'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
