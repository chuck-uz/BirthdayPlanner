import type { WishlistItem } from '@/types/publicUser'

export type AdminUserListItem = {
  id: number
  telegram_id: number
  full_name: string | null
  birth_date: string | null
  is_blocked: boolean
  is_test: boolean
  is_profile_complete: boolean
  has_avatar: boolean
  is_bot_active: boolean
  created_at: string
}

export type AdminUserDetail = AdminUserListItem & {
  wishlists: WishlistItem[]
  subscribers_count: number
  subscribing_count: number
}
