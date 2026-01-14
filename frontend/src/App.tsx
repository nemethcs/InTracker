import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { MainLayout } from '@/components/layout/MainLayout'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Toaster } from '@/components/ui/toast'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { Dashboard } from '@/pages/Dashboard'
import { ProjectDetail } from '@/pages/ProjectDetail'
import { FeatureDetail } from '@/pages/FeatureDetail'
import { Todos } from '@/pages/Todos'
import { Documents } from '@/pages/Documents'
import { Settings } from '@/pages/Settings'
import { Ideas } from '@/pages/Ideas'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'
// AdminLogin and AdminDashboard removed - admin functions integrated into Teams and Settings
import { Teams } from '@/pages/Teams'
import { Onboarding } from '@/pages/Onboarding'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Admins skip onboarding - they automatically have setup_completed=true
  // For non-admin users, check if setup is completed - if not, redirect to onboarding
  if (user?.role !== 'admin' && !user?.setup_completed) {
    const currentPath = location.pathname
    const allowedPaths = ['/onboarding', '/settings', '/logout']
    if (!allowedPaths.includes(currentPath) && !currentPath.startsWith('/onboarding')) {
      return <Navigate to="/onboarding" replace />
    }
  }

  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Toaster />
        <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:projectId/features/:featureId"
          element={
            <ProtectedRoute>
              <MainLayout>
                <FeatureDetail />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ProjectDetail />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/todos"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Todos />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/documents"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Documents />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ideas"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Ideas />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Settings />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/teams"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Teams />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Catch-all route - only redirect if route doesn't match */}
        <Route path="*" element={
          <ProtectedRoute>
            <MainLayout>
              <div className="p-6">
                <h1 className="text-2xl font-bold">404 - Page Not Found</h1>
                <p className="text-muted-foreground mt-2">The page you're looking for doesn't exist.</p>
              </div>
            </MainLayout>
          </ProtectedRoute>
        } />
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App
