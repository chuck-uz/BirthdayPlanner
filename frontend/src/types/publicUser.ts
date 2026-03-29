export type WishlistItem = {
  id: number
  title: string
  created_at: string
}

export type UserPublicProfile = {
  id: number
  full_name: string | null
  birth_date: string | null
  wishlists: WishlistItem[]
}
