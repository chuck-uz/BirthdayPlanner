import { useEffect, useState, type FormEvent } from 'react'
import axios from 'axios'
import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { api } from '@/lib/api'
import { validateBirthDate, validateFullName } from '@/lib/profileValidation'

export function ProfileSettingsPage() {
  const { user, refreshUser } = useAuth()
  const { showToast } = useToast()
  const [fullName, setFullName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [errors, setErrors] = useState<{ fullName?: string; birthDate?: string; form?: string }>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!user) return
    setFullName(user.full_name?.trim() ?? '')
    setBirthDate(user.birth_date ?? '')
  }, [user?.id, user?.full_name, user?.birth_date])

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
      showToast('Данные обновлены')
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
    <div className="flex flex-col gap-8">
      <div>
        <Link
          to="/"
          className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-zinc-600 transition hover:text-orange-600 dark:text-zinc-400 dark:hover:text-orange-400"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Назад на главную
        </Link>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
          Настройки профиля
        </h1>
        <p className="mt-1 text-zinc-600 dark:text-zinc-400">
          Изменение ФИО и даты рождения. Фото профиля меняется в разделе «Профиль».
        </p>
      </div>

      <Card className="max-w-lg">
        <CardHeader>
          <CardTitle>Личные данные</CardTitle>
          <CardDescription>Эти поля видны другим участникам в списке дней рождения.</CardDescription>
        </CardHeader>
        <form onSubmit={(e) => void onSubmit(e)} className="flex flex-col gap-5 px-6 pb-6">
          {errors.form ? (
            <p
              role="alert"
              className="rounded-xl border border-red-200/80 bg-red-50/90 px-3 py-2 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200"
            >
              {errors.form}
            </p>
          ) : null}

          <div className="flex flex-col gap-1.5">
            <label htmlFor="settings-fullName" className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              Фамилия, имя, отчество
            </label>
            <input
              id="settings-fullName"
              name="fullName"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Иванов Иван Иванович"
              className="rounded-xl border border-zinc-200/80 bg-white/80 px-3 py-2.5 text-sm text-zinc-900 shadow-inner outline-none ring-orange-500/25 placeholder:text-zinc-400 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-950/50 dark:text-zinc-100 dark:placeholder:text-zinc-500"
            />
            {errors.fullName ? (
              <p className="text-sm text-red-600 dark:text-red-400">{errors.fullName}</p>
            ) : null}
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="settings-birthDate" className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              Дата рождения
            </label>
            <input
              id="settings-birthDate"
              name="birthDate"
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              className="rounded-xl border border-zinc-200/80 bg-white/80 px-3 py-2.5 text-sm text-zinc-900 shadow-inner outline-none ring-orange-500/25 focus:border-orange-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-950/50 dark:text-zinc-100"
            />
            {errors.birthDate ? (
              <p className="text-sm text-red-600 dark:text-red-400">{errors.birthDate}</p>
            ) : null}
          </div>

          <Button type="submit" disabled={submitting} className="w-full sm:w-auto">
            {submitting ? 'Сохранение…' : 'Сохранить изменения'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
