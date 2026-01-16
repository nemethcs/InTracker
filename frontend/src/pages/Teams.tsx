import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { adminService, type Team, type Invitation, type TeamMember, type User } from '@/services/adminService'
import { Mail } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { useToast } from '@/hooks/useToast'
import { TeamsList } from '@/components/teams/TeamsList'
import { TeamInfo } from '@/components/teams/TeamInfo'
import { TeamMembers } from '@/components/teams/TeamMembers'
import { TeamInvitations } from '@/components/teams/TeamInvitations'
import { EditTeamDialog } from '@/components/teams/EditTeamDialog'
import { AddMemberDialog } from '@/components/teams/AddMemberDialog'
import { InviteEmailDialog } from '@/components/teams/InviteEmailDialog'
import { TeamLeaderInviteDialog } from '@/components/teams/TeamLeaderInviteDialog'

export function Teams() {
  const { user } = useAuth()
  const toast = useToast()
  const [teams, setTeams] = useState<Team[]>([])
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null)
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [teamInvitations, setTeamInvitations] = useState<Invitation[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  
  // Dialog states
  const [editTeamOpen, setEditTeamOpen] = useState(false)
  const [addMemberOpen, setAddMemberOpen] = useState(false)
  const [inviteEmailOpen, setInviteEmailOpen] = useState(false)
  const [teamLeaderInviteOpen, setTeamLeaderInviteOpen] = useState(false)
  const [teamForm, setTeamForm] = useState({ name: '', description: '' })
  const [selectedUserId, setSelectedUserId] = useState('')
  const [selectedMemberRole, setSelectedMemberRole] = useState('member')
  const [inviteEmail, setInviteEmail] = useState('')
  const [teamLeaderInviteEmail, setTeamLeaderInviteEmail] = useState('')

  // Check if user is admin or team leader
  const isAdmin = user?.role === 'admin'
  const isTeamLeader = user?.role === 'team_leader' || isAdmin
  const isRegularUser = user?.role !== 'admin' && user?.role !== 'team_leader'
  
  // Check if current user is team leader of selected team
  const isTeamLeaderOfSelectedTeam = selectedTeam && teamMembers.length > 0 && user
    ? teamMembers.some(m => m.user_id === user.id && m.role === 'team_leader')
    : false

  useEffect(() => {
    loadTeams()
    if (isAdmin) {
      loadAllUsers()
    }
  }, [isAdmin])

  const loadTeams = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await adminService.getTeams()
      // Backend already filters: admins see all, others see only their teams
      setTeams(response.teams)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load teams')
    } finally {
      setIsLoading(false)
    }
  }

  const loadAllUsers = async () => {
    try {
      const response = await adminService.getUsers()
      setAllUsers(response.users)
    } catch (err) {
      console.error('Failed to load users:', err)
    }
  }

  const loadTeamDetails = async (teamId: string) => {
    try {
      // Load team members
      const members = await adminService.getTeamMembers(teamId)
      setTeamMembers(members)

      // Load team invitations - only admins can access the admin invitations endpoint
      // For team leaders, we'll skip loading invitations if not admin
      // Team leaders can create invitations but don't need to see all invitations via admin endpoint
      if (isAdmin) {
        try {
          const allInvitations = await adminService.getInvitations({ type: 'team' })
          const teamInvites = allInvitations.invitations.filter(inv => inv.team_id === teamId)
          setTeamInvitations(teamInvites)
        } catch (invErr) {
          // If user is not admin, silently fail - invitations will be empty
          // Team leaders can still create new invitations
          console.log('Could not load invitations (admin only):', invErr)
          setTeamInvitations([])
        }
      } else {
        // For non-admin users, set empty invitations array
        // They can still create new invitations if they are team leaders
        setTeamInvitations([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load team details')
    }
  }

  const handleSelectTeam = (team: Team) => {
    setSelectedTeam(team)
    loadTeamDetails(team.id)
  }

  const handleEditTeam = (team: Team) => {
    setSelectedTeam(team)
    setEditTeamOpen(true)
  }

  const handleUpdateTeam = async (name: string, description: string) => {
    if (!selectedTeam || !name.trim()) {
      setError('Team name is required')
      throw new Error('Team name is required')
    }
    try {
      await adminService.updateTeam(selectedTeam.id, { name, description })
      setEditTeamOpen(false)
      loadTeams()
      if (selectedTeam) {
        loadTeamDetails(selectedTeam.id)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update team'
      setError(errorMessage)
      throw err
    }
  }

  const handleAddMember = (team: Team) => {
    setSelectedTeam(team)
    // If user is admin, show user selection dialog
    // If user is team leader (not admin), show email invitation dialog
    if (isAdmin) {
      setSelectedUserId('')
      setSelectedMemberRole('member')
      setAddMemberOpen(true)
    } else {
      // Team leader: open email invitation dialog
      setInviteEmail('')
      setSelectedMemberRole('member')
      setInviteEmailOpen(true)
    }
  }

  const handleAddMemberSubmit = async () => {
    if (!selectedTeam || !selectedUserId) {
      setError('Please select a user')
      return
    }
    try {
      await adminService.addTeamMember(selectedTeam.id, selectedUserId, selectedMemberRole)
      setAddMemberOpen(false)
      setSelectedUserId('')
      if (selectedTeam) {
        loadTeamDetails(selectedTeam.id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add member')
    }
  }

  const handleRemoveMember = async (teamId: string, userId: string) => {
    if (!confirm('Are you sure you want to remove this member from the team?')) return
    try {
      await adminService.removeTeamMember(teamId, userId)
      loadTeamDetails(teamId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member')
    }
  }

  const handleUpdateMemberRole = async (teamId: string, userId: string, newRole: string) => {
    try {
      await adminService.updateTeamMemberRole(teamId, userId, newRole)
      loadTeamDetails(teamId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update member role')
    }
  }

  const handleCreateTeamInvitation = async (teamId: string, email?: string, memberRole: string = 'member') => {
    try {
      const invitation = await adminService.createTeamInvitation(teamId, 7, email, memberRole)
      
      // Check if user was added directly (code starts with "DIRECT_ADD:")
      if (invitation.code && invitation.code.startsWith('DIRECT_ADD:')) {
        // User was added directly, reload team members
        loadTeamDetails(teamId)
        if (email) {
          setInviteEmailOpen(false)
          setInviteEmail('')
        }
        toast.success('Member added', `User with email ${email} has been added directly to the team.`)
      } else {
        // Regular invitation created
        setTeamInvitations([...teamInvitations, invitation])
        loadTeamDetails(teamId)
        if (email) {
          setInviteEmailOpen(false)
          setInviteEmail('')
        }
        toast.success('Invitation created', 'Team invitation has been created successfully.')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create invitation'
      setError(errorMessage)
      toast.error('Failed to create invitation', errorMessage)
    }
  }

  const handleCreateTeamLeaderInvitation = async (email?: string) => {
    try {
      const invitation = await adminService.createAdminInvitation(30, email)
      setTeamLeaderInviteOpen(false)
      setTeamLeaderInviteEmail('')
      if (email) {
        toast.success('Team Leader Invitation sent', `Invitation email has been sent to ${email}`)
      } else {
        toast.success('Team Leader Invitation created', `Invitation code: ${invitation.code}`)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create team leader invitation'
      setError(errorMessage)
      toast.error('Failed to create team leader invitation', errorMessage)
    }
  }

  const handleTeamLeaderInviteEmailSubmit = async () => {
    if (!teamLeaderInviteEmail.trim()) {
      setError('Please enter an email address')
      return
    }
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(teamLeaderInviteEmail)) {
      setError('Please enter a valid email address')
      return
    }
    await handleCreateTeamLeaderInvitation(teamLeaderInviteEmail.trim())
  }

  const handleInviteEmailSubmit = async () => {
    if (!selectedTeam || !inviteEmail.trim()) {
      setError('Please enter an email address')
      return
    }
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(inviteEmail)) {
      setError('Please enter a valid email address')
      return
    }
    
    // Check if email was already sent to this address for this team
    const emailLower = inviteEmail.trim().toLowerCase()
    const alreadySent = teamInvitations.some(
      inv => inv.email_sent_to && inv.email_sent_to.toLowerCase() === emailLower
    )
    if (alreadySent) {
      setError('Invitation email has already been sent to this address')
      return
    }
    
    const memberRole = selectedMemberRole === 'team_leader' ? 'team_leader' : 'member'
    await handleCreateTeamInvitation(selectedTeam.id, inviteEmail.trim(), memberRole)
    // Reset role to member after sending
    setSelectedMemberRole('member')
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const handleSetTeamLanguage = async (teamId: string, language: string) => {
    if (!selectedTeam) return
    try {
      const updatedTeam = await adminService.setTeamLanguage(teamId, language)
      // Update the selected team and teams list
      setSelectedTeam(updatedTeam)
      setTeams(teams.map(t => t.id === teamId ? updatedTeam : t))
      toast.success('Team language updated', 'The team language has been set successfully.')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to set team language'
      setError(errorMessage)
      toast.error('Failed to set team language', errorMessage)
    }
  }

  // Get users not in team (for admin only)
  const getAvailableUsers = (teamId: string) => {
    if (!isAdmin) return []
    const memberUserIds = new Set(teamMembers.map(m => m.user_id))
    return allUsers.filter(user => !memberUserIds.has(user.id))
  }

  // Get user info for member
  const getUserInfo = (userId: string) => {
    return allUsers.find(u => u.id === userId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teams"
        description="Manage your teams and members"
      />

      {/* Global Team Leader Invitation - Only for admins */}
      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Team Leader Invitation</CardTitle>
            <CardDescription>Create an invitation for a new team leader who will get their own team</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => setTeamLeaderInviteOpen(true)}
              className="w-full sm:w-auto"
            >
              <Mail className="h-4 w-4 mr-2" />
              Send Team Leader Invitation
            </Button>
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Teams List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">My Teams</h2>
          <TeamsList
            teams={teams}
            selectedTeam={selectedTeam}
            onSelectTeam={handleSelectTeam}
          />
        </div>

        {/* Team Details */}
        {selectedTeam && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">{selectedTeam.name}</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedTeam(null)}
              >
                Close
              </Button>
            </div>

            <TeamInfo
              team={selectedTeam}
              isTeamLeader={isTeamLeaderOfSelectedTeam}
              onEdit={() => handleEditTeam(selectedTeam)}
              onSetLanguage={(language) => handleSetTeamLanguage(selectedTeam.id, language)}
            />

            <TeamMembers
              teamId={selectedTeam.id}
              members={teamMembers}
              allUsers={allUsers}
              isTeamLeader={isTeamLeaderOfSelectedTeam}
              isAdmin={isAdmin}
              onAddMember={() => handleAddMember(selectedTeam)}
              onRemoveMember={(userId) => handleRemoveMember(selectedTeam.id, userId)}
              onUpdateRole={(userId, newRole) => handleUpdateMemberRole(selectedTeam.id, userId, newRole)}
              getAvailableUsers={() => getAvailableUsers(selectedTeam.id)}
              getUserInfo={getUserInfo}
            />

            {(isTeamLeaderOfSelectedTeam || isAdmin) && (
              <TeamInvitations
                invitations={teamInvitations}
                copiedCode={copiedCode}
                onSendInvitation={() => setInviteEmailOpen(true)}
                onCreateCodeOnly={() => handleCreateTeamInvitation(selectedTeam.id)}
                onCopyCode={handleCopyCode}
              />
            )}

            <EditTeamDialog
              open={editTeamOpen}
              onOpenChange={setEditTeamOpen}
              team={selectedTeam}
              onUpdate={handleUpdateTeam}
            />

            <AddMemberDialog
              open={addMemberOpen}
              onOpenChange={setAddMemberOpen}
              team={selectedTeam}
              availableUsers={selectedTeam ? getAvailableUsers(selectedTeam.id) : []}
              selectedUserId={selectedUserId}
              selectedRole={selectedMemberRole}
              onUserIdChange={setSelectedUserId}
              onRoleChange={setSelectedMemberRole}
              onSubmit={handleAddMemberSubmit}
            />

            <InviteEmailDialog
              open={inviteEmailOpen}
              onOpenChange={setInviteEmailOpen}
              team={selectedTeam}
              email={inviteEmail}
              onEmailChange={setInviteEmail}
              invitations={teamInvitations}
              onSubmit={handleInviteEmailSubmit}
            />

          </div>
        )}
      </div>

      {isAdmin && (
        <TeamLeaderInviteDialog
          open={teamLeaderInviteOpen}
          onOpenChange={(open) => {
            setTeamLeaderInviteOpen(open)
            if (open) {
              setTeamLeaderInviteEmail(user?.email || '')
            } else {
              setTeamLeaderInviteEmail('')
            }
          }}
          email={teamLeaderInviteEmail}
          onEmailChange={setTeamLeaderInviteEmail}
          onSubmit={handleTeamLeaderInviteEmailSubmit}
        />
      )}
    </div>
  )
}
