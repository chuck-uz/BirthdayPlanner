import { Cake, LogOut, Settings, Shield, UserRound } from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { useAuth } from '@/contexts/AuthContext'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive
      ? 'bg-white/70 text-orange-700 shadow-sm dark:bg-white/10 dark:text-orange-400'
      : 'text-zinc-600 hover:bg-white/50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-white/5 dark:hover:text-zinc-100'
  }`

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="relative min-h-svh overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-200/50 via-zinc-50 to-zinc-100 dark:from-orange-950/40 dark:via-zinc-950 dark:to-black"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-32 top-24 -z-10 h-96 w-96 rounded-full bg-orange-400/25 blur-3xl dark:bg-orange-600/20"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -left-24 bottom-0 -z-10 h-80 w-80 rounded-full bg-zinc-900/10 blur-3xl dark:bg-zinc-800/40"
        aria-hidden
      />

      <header className="sticky top-0 z-20 border-b border-white/30 bg-white/30 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/40">
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
            <NavLink to="/profile/settings" className={navClass} title="Настройки">
              <Settings className="mr-1 inline size-4" aria-hidden />
              Настройки
            </NavLink>
            {user?.is_admin ? (
              <NavLink to="/admin" className={navClass}>
                <Shield className="mr-1 inline size-4" aria-hidden />
                Админ
              </NavLink>
            ) : null}
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
        <nav className="flex border-t border-white/20 px-4 py-2 backdrop-blur-md dark:border-white/5 sm:hidden">
          <NavLink to="/" end className={navClass}>
            Главная
          </NavLink>
          <NavLink to="/profile" className={navClass}>
            <UserRound className="mr-1 inline size-4" aria-hidden />
            Профиль
          </NavLink>
          <NavLink to="/profile/settings" className={navClass}>
            <Settings className="mr-1 inline size-4" aria-hidden />
            Настройки
          </NavLink>
          {user?.is_admin ? (
            <NavLink to="/admin" className={navClass}>
              <Shield className="mr-1 inline size-4" aria-hidden />
              Админ
            </NavLink>
          ) : null}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>
    </div>
  )
}
