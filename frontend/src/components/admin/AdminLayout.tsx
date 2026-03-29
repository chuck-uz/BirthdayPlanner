import { NavLink, Outlet } from 'react-router-dom'
import { Send, Shield, Users } from 'lucide-react'

const tabClass = ({ isActive }: { isActive: boolean }) =>
  `inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition ${
    isActive
      ? 'bg-orange-600 text-white shadow-md shadow-orange-500/30 dark:bg-orange-500'
      : 'bg-white/60 text-zinc-700 ring-1 ring-zinc-200/80 hover:bg-white dark:bg-zinc-900/60 dark:text-zinc-200 dark:ring-zinc-700'
  }`

export function AdminLayout() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-xl bg-orange-600/15 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300">
            <Shield className="size-6" aria-hidden />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-3xl">
              Админ-панель
            </h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">Рассылки и управление пользователями</p>
          </div>
        </div>
        <nav className="flex flex-wrap gap-2" aria-label="Разделы админки">
          <NavLink to="/admin/dashboard" end className={tabClass}>
            <Send className="size-4" aria-hidden />
            Рассылки
          </NavLink>
          <NavLink to="/admin/users" className={tabClass}>
            <Users className="size-4" aria-hidden />
            Пользователи
          </NavLink>
        </nav>
      </div>
      <Outlet />
    </div>
  )
}
