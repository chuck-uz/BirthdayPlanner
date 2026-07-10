export type GroupRole = 'admin' | 'member'

export type GroupMember = {
  user_id: number
  full_name: string | null
  role: GroupRole
  joined_at: string
}

export type Group = {
  id: number
  name: string
  my_role: GroupRole
  member_count: number
  invite_visible_to_members: boolean
  invite_token: string | null
  created_at: string
}

export type GroupDetail = Group & {
  members: GroupMember[]
}

export type GroupBirthdayMember = {
  user_id: number
  full_name: string | null
  birth_date: string
  days_until: number
  has_avatar: boolean
}

export type GroupBirthdaySection = {
  group_id: number
  group_name: string
  members: GroupBirthdayMember[]
}

export function buildInviteLink(token: string): string {
  return `${window.location.origin}/groups/join?token=${encodeURIComponent(token)}`
}

export function membersCountLabel(count: number): string {
  const mod10 = count % 10
  const mod100 = count % 100
  let word = 'участников'
  if (mod10 === 1 && mod100 !== 11) {
    word = 'участник'
  } else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    word = 'участника'
  }
  return `${count} ${word}`
}

const GROUP_ERROR_MESSAGES: Record<string, string> = {
  group_not_found: 'Группа не найдена или ссылка больше не действует.',
  not_a_member: 'Вы не состоите в этой группе.',
  admin_required: 'Это действие доступно только администраторам группы.',
  target_not_member: 'Этот пользователь не состоит в группе.',
  invalid_token: 'Ссылка-приглашение не указана.',
  invalid_name: 'Укажите название группы.',
}

export function groupErrorMessage(code: unknown): string {
  const key = typeof code === 'string' ? code : ''
  return GROUP_ERROR_MESSAGES[key] ?? 'Не удалось выполнить действие. Попробуйте ещё раз.'
}
