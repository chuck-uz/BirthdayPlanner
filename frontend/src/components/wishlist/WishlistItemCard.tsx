import { useState } from 'react'
import { ExternalLink, Gift, Pencil, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { wishlistPhotoUrl } from '@/lib/wishlistPhotoUrl'
import type { WishlistItem } from '@/types/publicUser'

type WishlistItemCardProps = {
  item: WishlistItem
  /** Сброс кеша после загрузки / смены фото */
  photoRev?: number
  variant: 'public' | 'owner'
  onEdit?: (item: WishlistItem) => void
  onDelete?: (id: number) => void
}

export function WishlistItemCard({
  item,
  photoRev = 0,
  variant,
  onEdit,
  onDelete,
}: WishlistItemCardProps) {
  const [imgFailed, setImgFailed] = useState(false)
  const showPhoto = item.has_photo && !imgFailed
  const href = item.link_url?.trim() ?? ''
  const hasLink = href.length > 0

  return (
    <article className="flex min-h-[300px] flex-col overflow-hidden rounded-2xl border border-zinc-200/90 bg-white shadow-sm dark:border-zinc-700 dark:bg-zinc-950/80">
      <div className="relative min-h-[140px] flex-1 basis-0 bg-zinc-200 dark:bg-zinc-800">
        {showPhoto ? (
          <img
            src={wishlistPhotoUrl(item.id, photoRev)}
            alt=""
            className="absolute inset-0 h-full w-full object-cover"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-zinc-400 dark:text-zinc-500">
            <Gift className="size-14" strokeWidth={1.25} aria-hidden />
          </div>
        )}
        {variant === 'owner' ? (
          <div className="absolute right-2 top-2 flex gap-1">
            {onEdit ? (
              <button
                type="button"
                onClick={() => onEdit(item)}
                className="rounded-lg bg-black/45 p-2 text-white backdrop-blur-sm transition hover:bg-black/60"
                aria-label="Изменить"
              >
                <Pencil className="size-4" />
              </button>
            ) : null}
            {onDelete ? (
              <button
                type="button"
                onClick={() => onDelete(item.id)}
                className="rounded-lg bg-black/45 p-2 text-white backdrop-blur-sm transition hover:bg-red-600/90"
                aria-label="Удалить"
              >
                <Trash2 className="size-4" />
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      <div className="flex flex-1 basis-0 flex-col gap-2 border-t border-zinc-100 p-3 dark:border-zinc-800">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-zinc-900 dark:text-zinc-50">
          {item.title}
        </h3>
        {item.description ? (
          <p className="line-clamp-3 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
            {item.description}
          </p>
        ) : null}
        {hasLink ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-orange-600 px-3 py-2 text-center text-xs font-medium text-white shadow-sm transition hover:bg-orange-500 dark:bg-orange-500 dark:hover:bg-orange-400"
          >
            <ExternalLink className="size-3.5 shrink-0" aria-hidden />
            Где купить
          </a>
        ) : (
          <Button
            type="button"
            disabled
            variant="outline"
            className="mt-auto cursor-not-allowed py-2 text-xs opacity-60"
          >
            Где купить
          </Button>
        )}
      </div>
    </article>
  )
}
