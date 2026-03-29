import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { SetupProfileRoute } from '@/components/auth/SetupProfileRoute'
import { AppShell } from '@/components/layout/AppShell'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { SetupProfilePage } from '@/pages/SetupProfilePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/setup-profile"
          element={
            <SetupProfileRoute>
              <SetupProfilePage />
            </SetupProfileRoute>
          }
        />
        <Route element={<AppShell />}>
          <Route
            path="/"
            element={
              <ProtectedRoute requireCompleteProfile>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute requireCompleteProfile>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
