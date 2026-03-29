/** Подпись вида «3 апреля» по дате рождения (ISO YYYY-MM-DD), без года. */
export function formatAnnualBirthdayRu(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number)
  if (!y || !m || !d) return isoDate
  const date = new Date(y, m - 1, d)
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(date)
}

/** Полная дата рождения для карточки профиля */
export function formatBirthDateLongRu(isoDate: string | null | undefined): string {
  if (!isoDate) return '—'
  const [y, m, d] = isoDate.split('-').map(Number)
  if (!y || !m || !d) return isoDate
  const date = new Date(y, m - 1, d)
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

export function daysUntilLabelRu(days: number): string {
  if (days === 0) return 'сегодня'
  const m10 = days % 10
  const m100 = days % 100
  let word: string
  if (m100 >= 11 && m100 <= 14) word = 'дней'
  else if (m10 === 1) word = 'день'
  else if (m10 >= 2 && m10 <= 4) word = 'дня'
  else word = 'дней'
  return `через ${days} ${word}`
}
