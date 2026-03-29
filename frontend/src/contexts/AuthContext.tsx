import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api } from '@/lib/api'
import { notifyAccountBlocked, setAccountBlockedHandler, setUnauthorizedHandler } from '@/lib/authSession'
import type { UserProfile } from '@/types/user'

type AuthContextValue = {
  user: UserProfile | null
  loading: boolean
  refreshUser: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const res = await api.get<UserProfile>('/api/users/me', {
        validateStatus: (s) => s === 200 || s === 401 || s === 403,
      })
      if (res.status === 401) {
        setUser(null)
      } else if (res.status === 403) {
        const d = (res.data as { detail?: string })?.detail
        if (d === 'account_blocked') {
          notifyAccountBlocked()
        }
        setUser(null)
      } else {
        setUser(res.data)
      }
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout')
    } catch {
      /* ignore */
    }
    setUser(null)
  }, [])

  useEffect(() => {
    void refreshUser()
  }, [refreshUser])

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        void refreshUser()
      }
    }
    const onFocus = () => {
      void refreshUser()
    }
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [refreshUser])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null)
      setLoading(false)
    })
    setAccountBlockedHandler(() => {
      setUser(null)
      setLoading(false)
    })
    return () => {
      setUnauthorizedHandler(null)
      setAccountBlockedHandler(null)
    }
  }, [])

  const value = useMemo(
    () => ({ user, loading, refreshUser, logout }),
    [user, loading, refreshUser, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
