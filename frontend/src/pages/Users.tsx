import { UserManagement } from '@/components/admin/UserManagement'
import { PageHeader } from '@/components/layout/PageHeader'

export function Users() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Manage all users in the system"
      />
      <UserManagement />
    </div>
  )
}
