import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Mail, Copy, CheckCircle2 } from 'lucide-react'
import type { Invitation } from '@/services/adminService'

interface TeamInvitationsProps {
  invitations: Invitation[]
  copiedCode: string | null
  onSendInvitation: () => void
  onCreateCodeOnly: () => void
  onCopyCode: (code: string) => void
}

export function TeamInvitations({
  invitations,
  copiedCode,
  onSendInvitation,
  onCreateCodeOnly,
  onCopyCode,
}: TeamInvitationsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Invitations</CardTitle>
        <CardDescription>Create and manage team invitation codes</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={onSendInvitation}
            className="flex-1"
          >
            <Mail className="h-4 w-4 mr-2" />
            Send Member Invitation
          </Button>
          <Button
            onClick={onCreateCodeOnly}
            variant="outline"
          >
            Create Code Only
          </Button>
        </div>

        {invitations.length > 0 && (
          <div className="space-y-2">
            {invitations.map((inv) => (
              <div
                key={inv.code}
                className="flex items-center justify-between p-2 rounded border"
              >
                <div className="flex-1">
                  <code className="text-xs font-mono bg-muted px-2 py-1 rounded">
                    {inv.code}
                  </code>
                  <p className="text-xs text-muted-foreground mt-1">
                    {inv.expires_at
                      ? `Expires: ${new Date(inv.expires_at).toLocaleDateString()}`
                      : 'No expiration'}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onCopyCode(inv.code)}
                >
                  {copiedCode === inv.code ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
