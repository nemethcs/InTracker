import { useShallow } from 'zustand/react/shallow'
import { useAuthStore } from '@/stores/authStore'
import { PageHeader } from '@/components/layout/PageHeader'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { UserManagement } from '@/components/admin/UserManagement'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { UserSettings } from '@/components/settings/UserSettings'
import { McpKeySettings } from '@/components/settings/McpKeySettings'
import { GitHubSettings } from '@/components/settings/GitHubSettings'

export function Settings() {
  const { user: authUser } = useAuth()
  const { user, logout } = useAuthStore(
    useShallow((state) => ({
      user: state.user,
      logout: state.logout,
    }))
  )
  const navigate = useNavigate()
  const isAdmin = authUser?.role === 'admin'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your account and preferences"
      />

      <Tabs defaultValue="general" className="w-full">
        <TabsList className={isAdmin ? "grid w-full max-w-md grid-cols-2" : "grid w-full max-w-md grid-cols-1"}>
          <TabsTrigger value="general">General</TabsTrigger>
          {isAdmin && <TabsTrigger value="users">Users</TabsTrigger>}
        </TabsList>

        <TabsContent value="general" className="space-y-6 mt-6">
          <UserSettings user={user} onLogout={handleLogout} />
          <McpKeySettings />
          <GitHubSettings />
        </TabsContent>

        {isAdmin && (
          <TabsContent value="users" className="mt-6">
            <UserManagement />
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}
