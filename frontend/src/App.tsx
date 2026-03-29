import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AdminRoute } from '@/components/admin/AdminRoute'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { SetupProfileRoute } from '@/components/auth/SetupProfileRoute'
import { AppShell } from '@/components/layout/AppShell'
import { AdminUserDetailPage } from '@/pages/AdminUserDetailPage'
import { AdminUsersPage } from '@/pages/AdminUsersPage'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { ProfileSettingsPage } from '@/pages/ProfileSettingsPage'
import { SetupProfilePage } from '@/pages/SetupProfilePage'
import { UserProfilePage } from '@/pages/UserProfilePage'

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
          <Route
            path="/profile/settings"
            element={
              <ProtectedRoute requireCompleteProfile>
                <ProfileSettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireCompleteProfile>
                <AdminRoute>
                  <AdminUsersPage />
                </AdminRoute>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users/:userId"
            element={
              <ProtectedRoute requireCompleteProfile>
                <AdminRoute>
                  <AdminUserDetailPage />
                </AdminRoute>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users/:userId"
            element={
              <ProtectedRoute requireCompleteProfile>
                <UserProfilePage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
