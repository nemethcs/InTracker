import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { UserPlus, UserMinus } from 'lucide-react'
import type { TeamMember } from '@/services/adminService'
import type { User } from '@/services/adminService'

interface TeamMembersProps {
  teamId: string
  members: TeamMember[]
  allUsers: User[]
  isTeamLeader: boolean
  isAdmin: boolean
  onAddMember: () => void
  onRemoveMember: (userId: string) => void
  onUpdateRole: (userId: string, newRole: string) => void
  getAvailableUsers: () => User[]
  getUserInfo: (userId: string) => User | undefined
}

export function TeamMembers({
  teamId,
  members,
  allUsers,
  isTeamLeader,
  isAdmin,
  onAddMember,
  onRemoveMember,
  onUpdateRole,
  getAvailableUsers,
  getUserInfo,
}: TeamMembersProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Members</CardTitle>
            <CardDescription>Team members and their roles</CardDescription>
          </div>
          {isTeamLeader && (
            <Button
              size="sm"
              onClick={onAddMember}
              disabled={isAdmin && getAvailableUsers().length === 0}
            >
              <UserPlus className="h-4 w-4 mr-1" />
              Add Member
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {members.length === 0 ? (
          <p className="text-sm text-muted-foreground">No members yet</p>
        ) : (
          <div className="space-y-2">
            {members.map((member) => {
              const displayName = member.user_name || member.user_email || getUserInfo(member.user_id)?.name || getUserInfo(member.user_id)?.email || `User ${member.user_id.slice(0, 8)}...`
              const displayEmail = member.user_email || getUserInfo(member.user_id)?.email || ''
              return (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-2 rounded border"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      {displayName}
                    </p>
                    {displayEmail && displayEmail !== displayName && (
                      <p className="text-xs text-muted-foreground">
                        {displayEmail}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {member.role} • Joined {new Date(member.joined_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {member.role === 'team_leader' && (
                      <span className="px-2 py-1 rounded text-xs bg-primary/10 text-primary dark:bg-primary/20">
                        Leader
                      </span>
                    )}
                    {(isTeamLeader || isAdmin) && (
                      <>
                        <select
                          value={member.role}
                          onChange={(e) => onUpdateRole(member.user_id, e.target.value)}
                          className="h-8 rounded-md border border-input bg-background px-2 py-1 text-sm"
                          disabled={!isAdmin && member.role === 'team_leader' && !isTeamLeader}
                        >
                          <option value="member">Member</option>
                          <option value="team_leader">Team Leader</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onRemoveMember(member.user_id)}
                          aria-label={`Remove member ${displayName} from team`}
                        >
                          <UserMinus className="h-4 w-4 text-destructive" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
