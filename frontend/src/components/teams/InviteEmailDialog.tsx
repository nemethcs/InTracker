import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Mail } from 'lucide-react'
import type { Team, Invitation } from '@/services/adminService'

interface InviteEmailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  team: Team | null
  email: string
  onEmailChange: (email: string) => void
  invitations: Invitation[]
  onSubmit: () => Promise<void>
}

export function InviteEmailDialog({
  open,
  onOpenChange,
  team,
  email,
  onEmailChange,
  invitations,
  onSubmit,
}: InviteEmailDialogProps) {
  const emailAlreadySent = invitations.some(
    inv => inv.email_sent_to && inv.email_sent_to.toLowerCase() === email.trim().toLowerCase()
  )

  return (
    <Dialog open={open} onOpenChange={(open) => {
      onOpenChange(open)
      if (!open) {
        onEmailChange('')
      }
    }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send Team Invitation</DialogTitle>
          <DialogDescription>
            Send an invitation email to join {team?.name} as a member.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="invite-email">Email Address *</Label>
            <Input
              id="invite-email"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => onEmailChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && email.trim() && !emailAlreadySent) {
                  onSubmit()
                }
              }}
            />
            <p className="text-xs text-muted-foreground">
              An invitation email will be sent to this address with a link to join the team.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => {
            onOpenChange(false)
            onEmailChange('')
          }}>Cancel</Button>
          <Button 
            onClick={onSubmit} 
            disabled={!email.trim() || emailAlreadySent}
          >
            <Mail className="h-4 w-4 mr-2" />
            {emailAlreadySent ? 'Email Already Sent' : 'Send Invitation'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
