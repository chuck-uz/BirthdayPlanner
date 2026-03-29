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

export type AdminBirthdayDashboardItem = {
  id: number
  full_name: string | null
  birth_date: string
  subscribers_count: number
  days_until_birthday: number
  celebration_date: string
  status: string
  is_sent: boolean
}

export type AdminBroadcastLinkIn = {
  target_user_id: number
  group_link: string
}

export type AdminBroadcastLinkOut = {
  target_user_id: number
  sent_count: number
  skipped_count: number
  celebration_date: string
}
