/** Общие правила для первичной настройки (/setup-profile) и добровольного редактирования (/profile/settings). */

export function validateFullName(value: string): string | null {
  const v = value.trim().replace(/\s+/g, ' ')
  if (!v) return 'Укажите фамилию, имя и отчество'
  const parts = v.split(' ').filter(Boolean)
  if (parts.length < 2) return 'Нужно минимум два слова (фамилия и имя)'
  if (v.length < 4) return 'Слишком короткое ФИО'
  return null
}

export function validateBirthDate(value: string): string | null {
  if (!value) return 'Выберите дату рождения'
  const d = new Date(value + 'T12:00:00')
  if (Number.isNaN(d.getTime())) return 'Некорректная дата'
  const today = new Date()
  today.setHours(23, 59, 59, 999)
  if (d > today) return 'Дата не может быть в будущем'
  const oldest = new Date()
  oldest.setFullYear(oldest.getFullYear() - 120)
  if (d < oldest) return 'Некорректная дата рождения'
  return null
}
