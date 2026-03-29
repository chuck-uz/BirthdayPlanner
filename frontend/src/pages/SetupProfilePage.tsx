import { useState, type FormEvent } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { UserRound } from 'lucide-react'

import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'

function validateFullName(value: string): string | null {
  const v = value.trim().replace(/\s+/g, ' ')
  if (!v) return 'Укажите фамилию, имя и отчество'
  const parts = v.split(' ').filter(Boolean)
  if (parts.length < 2) return 'Нужно минимум два слова (фамилия и имя)'
  if (v.length < 4) return 'Слишком короткое ФИО'
  return null
}

function validateBirthDate(value: string): string | null {
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

export function SetupProfilePage() {
  const { refreshUser } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [errors, setErrors] = useState<{ fullName?: string; birthDate?: string; form?: string }>(
    {},
  )
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const fnErr = validateFullName(fullName)
    const bdErr = validateBirthDate(birthDate)
    setErrors({
      fullName: fnErr ?? undefined,
      birthDate: bdErr ?? undefined,
    })
    if (fnErr || bdErr) return

    setSubmitting(true)
    setErrors({})
    try {
      const normalized = fullName.trim().replace(/\s+/g, ' ')
      await api.patch('/api/users/me', {
        full_name: normalized,
        birth_date: birthDate,
      })
      await refreshUser()
      navigate('/', { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 422) {
        const detail = err.response.data?.detail
        const msg = Array.isArray(detail)
          ? detail.map((x: { msg?: string }) => x.msg).filter(Boolean).join(' ')
          : typeof detail === 'string'
            ? detail
            : 'Проверьте введённые данные'
        setErrors({ form: msg })
      } else {
        setErrors({ form: 'Не удалось сохранить. Попробуйте позже.' })
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative min-h-svh overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-200/50 via-zinc-50 to-zinc-100 dark:from-orange-950/40 dark:via-zinc-950 dark:to-black"
        aria-hidden
      />
      <div className="absolute right-4 top-4 z-10 sm:right-6 sm:top-6">
        <ThemeToggle />
      </div>
      <div className="flex min-h-svh items-center justify-center px-4 py-16">
        <Card className="w-full max-w-lg">
          <CardHeader className="text-center">
            <div className="mx-auto mb-3 flex size-14 items-center justify-center rounded-2xl bg-orange-600/10 text-orange-600 dark:bg-orange-500/15 dark:text-orange-400">
              <UserRound className="size-7" aria-hidden />
            </div>
            <CardTitle className="text-xl sm:text-2xl">Почти готово!</CardTitle>
            <CardDescription className="text-base leading-relaxed">
              Расскажите о себе, чтобы друзья не забыли вас поздравить
            </CardDescription>
          </CardHeader>

          <form onSubmit={(e) => void onSubmit(e)} className="flex flex-col gap-5">
            {errors.form ? (
              <p
                role="alert"
                className="rounded-xl border border-red-200/80 bg-red-50/90 px-3 py-2 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200"
              >
                {errors.form}
              </p>
            ) : null}

            <div className="flex flex-col gap-1.5">
              <label htmlFor="fullName" className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                Фамилия, имя, отчество
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Иванов Иван Иванович"
                className="rounded-xl border border-zinc-200/80 bg-white/70 px-3 py-2.5 text-sm text-zinc-900 shadow-inner outline-none ring-orange-500/25 placeholder:text-zinc-400 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-950/50 dark:text-zinc-100 dark:placeholder:text-zinc-500"
              />
              {errors.fullName ? (
                <p className="text-sm text-red-600 dark:text-red-400">{errors.fullName}</p>
              ) : null}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="birthDate" className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                Дата рождения
              </label>
              <input
                id="birthDate"
                name="birthDate"
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className="rounded-xl border border-zinc-200/80 bg-white/70 px-3 py-2.5 text-sm text-zinc-900 shadow-inner outline-none ring-orange-500/25 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-950/50 dark:text-zinc-100"
              />
              {errors.birthDate ? (
                <p className="text-sm text-red-600 dark:text-red-400">{errors.birthDate}</p>
              ) : null}
            </div>

            <Button type="submit" disabled={submitting} className="mt-1 w-full">
              {submitting ? 'Сохранение…' : 'Сохранить и продолжить'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}
