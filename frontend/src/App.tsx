import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from '@/hooks/useAuth'
import { MainLayout } from '@/components/layout/MainLayout'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Toaster } from '@/components/ui/toast'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'

// Create a QueryClient instance with default options
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes - data is fresh for 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes - cache is kept for 10 minutes (formerly cacheTime)
      retry: 2, // Retry failed requests 2 times
      refetchOnWindowFocus: false, // Don't refetch on window focus
      refetchOnReconnect: true, // Refetch when network reconnects
    },
    mutations: {
      retry: 1, // Retry failed mutations once
    },
  },
})

// Eagerly loaded components (needed for initial render)
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'

// Helper function to lazy load named exports
const lazyNamed = <T extends React.ComponentType<any>>(
  importFn: () => Promise<{ [key: string]: T }>,
  exportName: string
) => {
  return lazy(async () => {
    const module = await importFn()
    return { default: module[exportName] as T }
  })
}

// Lazy loaded route components
const Dashboard = lazyNamed(() => import('@/pages/Dashboard'), 'Dashboard')
const ProjectDetail = lazyNamed(() => import('@/pages/ProjectDetail'), 'ProjectDetail')
const FeatureDetail = lazyNamed(() => import('@/pages/FeatureDetail'), 'FeatureDetail')
const Todos = lazyNamed(() => import('@/pages/Todos'), 'Todos')
const Documents = lazyNamed(() => import('@/pages/Documents'), 'Documents')
const Settings = lazyNamed(() => import('@/pages/Settings'), 'Settings')
const Ideas = lazyNamed(() => import('@/pages/Ideas'), 'Ideas')
const Teams = lazyNamed(() => import('@/pages/Teams'), 'Teams')
const Onboarding = lazyNamed(() => import('@/pages/Onboarding'), 'Onboarding')
const Users = lazyNamed(() => import('@/pages/Users'), 'Users')
const CursorGuide = lazyNamed(() => import('@/pages/CursorGuide'), 'CursorGuide')

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

function AdminOnlyRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  
  if (user?.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

// Loading fallback component for lazy loaded routes
function RouteLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <LoadingSpinner size="lg" />
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Toaster />
          <Suspense fallback={<RouteLoadingFallback />}>
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
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <AdminOnlyRoute>
                <MainLayout>
                  <Users />
                </MainLayout>
              </AdminOnlyRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/guide"
          element={
            <ProtectedRoute>
              <MainLayout>
                <CursorGuide />
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
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
