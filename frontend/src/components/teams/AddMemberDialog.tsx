import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import type { Team, User } from '@/services/adminService'

interface AddMemberDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  team: Team | null
  availableUsers: User[]
  selectedUserId: string
  selectedRole: string
  onUserIdChange: (userId: string) => void
  onRoleChange: (role: string) => void
  onSubmit: () => Promise<void>
}

export function AddMemberDialog({
  open,
  onOpenChange,
  team,
  availableUsers,
  selectedUserId,
  selectedRole,
  onUserIdChange,
  onRoleChange,
  onSubmit,
}: AddMemberDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Member to Team</DialogTitle>
          <DialogDescription>Select a user to add to {team?.name}.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="user-select">User *</Label>
            <select
              id="user-select"
              value={selectedUserId}
              onChange={(e) => onUserIdChange(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Select a user...</option>
              {availableUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name || user.email} ({user.email})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="member-role">Role *</Label>
            <select
              id="member-role"
              value={selectedRole}
              onChange={(e) => onRoleChange(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="member">Member</option>
              <option value="team_leader">Team Leader</option>
            </select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onSubmit} disabled={!selectedUserId}>Add Member</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
