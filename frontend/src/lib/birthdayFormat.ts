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

/** Следующий календарный день рождения (год — ближайшее наступление), для Google Calendar. */
function nextBirthdayDateParts(isoBirthDate: string): { y: number; m: number; d: number } | null {
  const parts = isoBirthDate.split('-').map(Number)
  const [by, bm, bd] = parts
  if (!by || !bm || !bd) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  let y = today.getFullYear()
  let dt = safeBirthdayInYear(y, bm, bd)
  if (dt < today) {
    y += 1
    dt = safeBirthdayInYear(y, bm, bd)
  }
  return { y: dt.getFullYear(), m: dt.getMonth() + 1, d: dt.getDate() }
}

function safeBirthdayInYear(year: number, month: number, day: number): Date {
  const dt = new Date(year, month - 1, day)
  if (dt.getMonth() !== month - 1) {
    return new Date(year, 1, 28)
  }
  return dt
}

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

/** Пара YYYYMMDD/YYYYMMDD для all-day в Google Calendar (конец — следующий день). */
export function nextBirthdayGoogleDates(isoBirthDate: string): string | null {
  const p = nextBirthdayDateParts(isoBirthDate)
  if (!p) return null
  const start = new Date(p.y, p.m - 1, p.d)
  const end = new Date(start)
  end.setDate(end.getDate() + 1)
  const a = `${start.getFullYear()}${pad2(start.getMonth() + 1)}${pad2(start.getDate())}`
  const b = `${end.getFullYear()}${pad2(end.getMonth() + 1)}${pad2(end.getDate())}`
  return `${a}/${b}`
}

/** Ссылка «Добавить в Google Календарь» для дня рождения. */
export function buildGoogleCalendarBirthdayUrl(fullName: string, isoBirthDate: string): string | null {
  const dates = nextBirthdayGoogleDates(isoBirthDate)
  if (!dates) return null
  const name = fullName.trim() || 'Участник'
  const text = `День рождения ${name}`
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text,
    dates,
  })
  return `https://www.google.com/calendar/render?${params.toString()}`
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
