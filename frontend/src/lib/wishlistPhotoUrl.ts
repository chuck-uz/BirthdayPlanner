/** Защищённый URL фото пункта вишлиста (нужен JWT). */
export function wishlistPhotoUrl(itemId: number, cacheBust = 0): string {
  const q = cacheBust > 0 ? `?v=${cacheBust}` : ''
  return `/api/wishlists/${itemId}/photo${q}`
}
