import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '@/contexts/AuthContext'

function AuthSpinner() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
    </div>
  )
}

/**
 * Доступно только авторизованным с незаполненным профилем.
 * При полном профиле — на главную.
 */
export function SetupProfileRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <AuthSpinner />
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: '/setup-profile' }} />
  }

  if (user.is_profile_complete) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
