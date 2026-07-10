export type UserProfile = {
  id: number
  telegram_id: number
  full_name: string | null
  birth_date: string | null
  is_profile_complete: boolean
  has_avatar?: boolean
  avatar_url?: string | null
  /** Пользователь нажал /start у бота (или getChat доступен). */
  is_bot_active?: boolean
}
