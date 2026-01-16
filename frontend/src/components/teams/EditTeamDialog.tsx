import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Team } from '@/services/adminService'

interface EditTeamDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  team: Team | null
  onUpdate: (name: string, description: string) => Promise<void>
}

export function EditTeamDialog({ open, onOpenChange, team, onUpdate }: EditTeamDialogProps) {
  const [teamForm, setTeamForm] = useState({ name: '', description: '' })
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    if (team) {
      setTeamForm({ name: team.name, description: team.description || '' })
    } else {
      setTeamForm({ name: '', description: '' })
    }
  }, [team, open])

  const handleUpdate = async () => {
    if (!teamForm.name.trim()) {
      return
    }
    try {
      setIsUpdating(true)
      await onUpdate(teamForm.name, teamForm.description)
      onOpenChange(false)
    } catch (error) {
      // Error handling is done in parent
      throw error
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Team</DialogTitle>
          <DialogDescription>Update team name and description.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="edit-team-name">Team Name *</Label>
            <Input
              id="edit-team-name"
              value={teamForm.name}
              onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
              placeholder="Enter team name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-team-description">Description</Label>
            <Input
              id="edit-team-description"
              value={teamForm.description}
              onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
              placeholder="Enter team description (optional)"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleUpdate} disabled={isUpdating || !teamForm.name.trim()}>
            {isUpdating ? 'Updating...' : 'Update Team'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
