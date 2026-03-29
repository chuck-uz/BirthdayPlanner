export type WishlistItem = {
  id: number
  title: string
  description: string | null
  link_url: string | null
  has_photo: boolean
  created_at: string
}

export type UserPublicProfile = {
  id: number
  full_name: string | null
  birth_date: string | null
  wishlists: WishlistItem[]
}
