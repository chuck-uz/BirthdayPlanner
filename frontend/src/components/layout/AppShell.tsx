import { Cake, Info, LogOut, Settings, Users, UserRound } from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { useAuth } from '@/contexts/AuthContext'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive
      ? 'bg-orange-50 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400'
      : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100'
  }`

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="min-h-svh bg-white dark:bg-zinc-950">
      <header className="sticky top-0 z-20 border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            to="/"
            className="flex items-center gap-2 font-semibold tracking-tight text-zinc-900 dark:text-white"
          >
            <span className="flex size-9 items-center justify-center rounded-xl bg-orange-600 text-white shadow-lg shadow-orange-500/35 dark:bg-orange-500">
              <Cake className="size-5" aria-hidden />
            </span>
            <span>BirthdayPlanner</span>
          </Link>

          <nav className="hidden items-center gap-1 sm:flex">
            <NavLink to="/" end className={navClass}>
              Главная
            </NavLink>
            <NavLink to="/profile" className={navClass}>
              Профиль
            </NavLink>
            <NavLink to="/groups" className={navClass}>
              <Users className="mr-1 inline size-4" aria-hidden />
              Группы
            </NavLink>
            <NavLink to="/profile/settings" className={navClass} title="Настройки">
              <Settings className="mr-1 inline size-4" aria-hidden />
              Настройки
            </NavLink>
            <NavLink to="/about" className={navClass}>
              <Info className="mr-1 inline size-4" aria-hidden />
              О проекте
            </NavLink>
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {user ? (
              <Button variant="outline" className="gap-2" onClick={() => void logout()}>
                <LogOut className="size-4" aria-hidden />
                <span className="hidden sm:inline">Выйти</span>
              </Button>
            ) : (
              <Button
                variant="primary"
                className="hidden sm:inline-flex"
                onClick={() => navigate('/login')}
              >
                Войти
              </Button>
            )}
          </div>
        </div>
        <nav className="flex border-t border-zinc-200 px-4 py-2 dark:border-zinc-800 sm:hidden">
          <NavLink to="/" end className={navClass}>
            Главная
          </NavLink>
          <NavLink to="/profile" className={navClass}>
            <UserRound className="mr-1 inline size-4" aria-hidden />
            Профиль
          </NavLink>
          <NavLink to="/groups" className={navClass}>
            <Users className="mr-1 inline size-4" aria-hidden />
            Группы
          </NavLink>
          <NavLink to="/profile/settings" className={navClass}>
            <Settings className="mr-1 inline size-4" aria-hidden />
            Настройки
          </NavLink>
          <NavLink to="/about" className={navClass}>
            <Info className="mr-1 inline size-4" aria-hidden />
            О проекте
          </NavLink>
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>
    </div>
  )
}
