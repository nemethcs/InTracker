import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Mail } from 'lucide-react'

interface TeamLeaderInviteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  email: string
  onEmailChange: (email: string) => void
  onSubmit: () => Promise<void>
}

export function TeamLeaderInviteDialog({
  open,
  onOpenChange,
  email,
  onEmailChange,
  onSubmit,
}: TeamLeaderInviteDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(open) => {
      onOpenChange(open)
      if (!open) {
        onEmailChange('')
      }
    }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send Team Leader Invitation</DialogTitle>
          <DialogDescription>
            Create an invitation for a new team leader. They will register with team_leader role and get their own team automatically created.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="team-leader-invite-email">Email Address (Optional)</Label>
            <Input
              id="team-leader-invite-email"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => onEmailChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onSubmit()
                }
              }}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              If provided, an invitation email will be sent. Otherwise, you'll get an invitation code to share manually.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => {
            onOpenChange(false)
            onEmailChange('')
          }}>Cancel</Button>
          <Button onClick={onSubmit}>
            <Mail className="h-4 w-4 mr-2" />
            {email.trim() ? 'Send Invitation' : 'Create Invitation Code'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
