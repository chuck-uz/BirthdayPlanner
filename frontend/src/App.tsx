import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { SetupProfileRoute } from '@/components/auth/SetupProfileRoute'
import { AppShell } from '@/components/layout/AppShell'
import { AboutPage } from '@/pages/AboutPage'
import { GroupDetailPage } from '@/pages/GroupDetailPage'
import { GroupsPage } from '@/pages/GroupsPage'
import { HomePage } from '@/pages/HomePage'
import { JoinGroupPage } from '@/pages/JoinGroupPage'
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
          <Route path="/about" element={<AboutPage />} />
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
            path="/groups"
            element={
              <ProtectedRoute requireCompleteProfile>
                <GroupsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/groups/join"
            element={
              <ProtectedRoute requireCompleteProfile>
                <JoinGroupPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/groups/:groupId"
            element={
              <ProtectedRoute requireCompleteProfile>
                <GroupDetailPage />
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
