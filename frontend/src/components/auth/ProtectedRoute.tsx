import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '@/contexts/AuthContext'

function AuthSpinner() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
    </div>
  )
}

type ProtectedRouteProps = {
  children: ReactNode
  /** Если true — без заполненного профиля редирект на /setup-profile */
  requireCompleteProfile?: boolean
}

export function ProtectedRoute({
  children,
  requireCompleteProfile = false,
}: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <AuthSpinner />
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }

  if (requireCompleteProfile && !user.is_profile_complete) {
    return <Navigate to="/setup-profile" replace />
  }

  return <>{children}</>
}
