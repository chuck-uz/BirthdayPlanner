import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '@/contexts/AuthContext'

export function AdminRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="py-20 text-center text-sm text-zinc-500 dark:text-zinc-400">Загрузка…</div>
    )
  }
  if (!user?.is_admin) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
