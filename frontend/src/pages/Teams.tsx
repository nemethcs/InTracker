import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { adminService, type Team, type Invitation, type TeamMember, type User } from '@/services/adminService'
import { UsersRound, Mail, Plus, Edit, Trash2, Copy, CheckCircle2, XCircle, UserPlus, UserMinus } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/useToast'

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
  const [teamForm, setTeamForm] = useState({ name: '', description: '' })
  const [selectedUserId, setSelectedUserId] = useState('')
  const [selectedMemberRole, setSelectedMemberRole] = useState('member')
  const [inviteEmail, setInviteEmail] = useState('')

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
    setTeamForm({ name: team.name, description: team.description || '' })
    setEditTeamOpen(true)
  }

  const handleUpdateTeam = async () => {
    if (!selectedTeam || !teamForm.name.trim()) {
      setError('Team name is required')
      return
    }
    try {
      await adminService.updateTeam(selectedTeam.id, teamForm)
      setEditTeamOpen(false)
      setTeamForm({ name: '', description: '' })
      loadTeams()
      if (selectedTeam) {
        loadTeamDetails(selectedTeam.id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update team')
    }
  }

  const handleAddMember = (team: Team) => {
    setSelectedTeam(team)
    setSelectedUserId('')
    setSelectedMemberRole('member')
    setAddMemberOpen(true)
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
      setTeamInvitations([...teamInvitations, invitation])
      loadTeamDetails(teamId)
      if (email) {
        setInviteEmailOpen(false)
        setInviteEmail('')
      }
      toast.success(
        memberRole === 'team_leader' ? 'Team leader invitation created' : 'Invitation created',
        memberRole === 'team_leader' 
          ? 'Team leader invitation has been created successfully.'
          : 'Team invitation has been created successfully.'
      )
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create invitation'
      setError(errorMessage)
      toast.error('Failed to create invitation', errorMessage)
    }
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

      {error && (
        <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Teams List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">My Teams</h2>
          {teams.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                No teams found
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {teams.map((team) => (
                <Card
                  key={team.id}
                  className={`cursor-pointer transition-colors ${
                    selectedTeam?.id === team.id ? 'border-primary bg-accent' : ''
                  }`}
                  onClick={() => handleSelectTeam(team)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold">{team.name}</h3>
                        {team.description && (
                          <p className="text-sm text-muted-foreground mt-1">{team.description}</p>
                        )}
                      </div>
                      <UsersRound className="h-5 w-5 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
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

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Team Information</CardTitle>
                    <CardDescription>{selectedTeam.description || 'No description'}</CardDescription>
                  </div>
                  {isTeamLeaderOfSelectedTeam && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditTeam(selectedTeam)}
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Team Name</Label>
                  <p className="text-sm font-medium">{selectedTeam.name}</p>
                </div>
                <div>
                  <Label>Language</Label>
                  {selectedTeam.language ? (
                    <p className="text-sm font-medium">
                      {selectedTeam.language === 'hu' ? 'Hungarian (Magyar)' : selectedTeam.language === 'en' ? 'English' : selectedTeam.language}
                    </p>
                  ) : isTeamLeaderOfSelectedTeam ? (
                    <div className="space-y-2">
                      <Select
                        value=""
                        onValueChange={(value) => handleSetTeamLanguage(selectedTeam.id, value)}
                      >
                        <SelectTrigger className="w-full sm:w-[200px]">
                          <SelectValue placeholder="Select language" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hu">Hungarian (Magyar)</SelectItem>
                          <SelectItem value="en">English</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Set the team language. This can only be set once and cannot be changed later.
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Not set</p>
                  )}
                </div>
                <div>
                  <Label>Created</Label>
                  <p className="text-sm text-muted-foreground">
                    {new Date(selectedTeam.created_at).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Team Members */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Members</CardTitle>
                    <CardDescription>Team members and their roles</CardDescription>
                  </div>
                  {isTeamLeaderOfSelectedTeam && (
                    <Button
                      size="sm"
                      onClick={() => handleAddMember(selectedTeam)}
                      disabled={getAvailableUsers(selectedTeam.id).length === 0}
                    >
                      <UserPlus className="h-4 w-4 mr-1" />
                      Add Member
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {teamMembers.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No members yet</p>
                ) : (
                  <div className="space-y-2">
                    {teamMembers.map((member) => {
                      // Use user_name and user_email from backend response, fallback to getUserInfo for backwards compatibility
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
                            {isTeamLeaderOfSelectedTeam && (
                              <>
                                <select
                                  value={member.role}
                                  onChange={(e) => handleUpdateMemberRole(selectedTeam.id, member.user_id, e.target.value)}
                                  className="h-8 rounded-md border border-input bg-background px-2 py-1 text-sm"
                                >
                                  <option value="member">Member</option>
                                  <option value="team_leader">Team Leader</option>
                                </select>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleRemoveMember(selectedTeam.id, member.user_id)}
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

            {/* Team Invitations - Only visible to team leaders */}
            {isTeamLeaderOfSelectedTeam && (
              <Card>
                <CardHeader>
                  <CardTitle>Invitations</CardTitle>
                  <CardDescription>Create and manage team invitation codes</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Button
                      onClick={() => setInviteEmailOpen(true)}
                      className="flex-1"
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Send Member Invitation
                    </Button>
                    {isAdmin && (
                      <Button
                        onClick={() => {
                          setInviteEmailOpen(true)
                          setSelectedMemberRole('team_leader')
                        }}
                        variant="default"
                        className="flex-1"
                      >
                        <Mail className="h-4 w-4 mr-2" />
                        Send Team Leader Invitation
                      </Button>
                    )}
                    <Button
                      onClick={() => handleCreateTeamInvitation(selectedTeam.id)}
                      variant="outline"
                    >
                      Create Code Only
                    </Button>
                    {isAdmin && (
                      <Button
                        onClick={() => handleCreateTeamInvitation(selectedTeam.id, undefined, 'team_leader')}
                        variant="outline"
                      >
                        Create Team Leader Code
                      </Button>
                    )}
                  </div>

                {teamInvitations.length > 0 && (
                  <div className="space-y-2">
                    {teamInvitations.map((inv) => (
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
                          onClick={() => handleCopyCode(inv.code)}
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
            )}

            {/* Edit Team Dialog */}
            <Dialog open={editTeamOpen} onOpenChange={setEditTeamOpen}>
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
                  <Button variant="outline" onClick={() => setEditTeamOpen(false)}>Cancel</Button>
                  <Button onClick={handleUpdateTeam}>Update Team</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Add Member Dialog */}
            <Dialog open={addMemberOpen} onOpenChange={setAddMemberOpen}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Member to Team</DialogTitle>
                  <DialogDescription>Select a user to add to {selectedTeam?.name}.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="user-select">User *</Label>
                    <select
                      id="user-select"
                      value={selectedUserId}
                      onChange={(e) => setSelectedUserId(e.target.value)}
                      className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="">Select a user...</option>
                      {selectedTeam && getAvailableUsers(selectedTeam.id).map((user) => (
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
                      value={selectedMemberRole}
                      onChange={(e) => setSelectedMemberRole(e.target.value)}
                      className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="member">Member</option>
                      <option value="team_leader">Team Leader</option>
                    </select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setAddMemberOpen(false)}>Cancel</Button>
                  <Button onClick={handleAddMemberSubmit} disabled={!selectedUserId}>Add Member</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Send Invitation Email Dialog */}
            <Dialog open={inviteEmailOpen} onOpenChange={(open) => {
              setInviteEmailOpen(open)
              if (!open) {
                setInviteEmail('')
                setSelectedMemberRole('member')
              }
            }}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>
                    {selectedMemberRole === 'team_leader' ? 'Send Team Leader Invitation' : 'Send Team Invitation'}
                  </DialogTitle>
                  <DialogDescription>
                    Send an invitation email to join {selectedTeam?.name} as {selectedMemberRole === 'team_leader' ? 'team leader' : 'member'}.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="invite-email">Email Address *</Label>
                    <Input
                      id="invite-email"
                      type="email"
                      placeholder="user@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && inviteEmail.trim()) {
                          handleInviteEmailSubmit()
                        }
                      }}
                    />
                    <p className="text-xs text-muted-foreground">
                      An invitation email will be sent to this address with a link to join the team.
                    </p>
                  </div>
                  {isAdmin && (
                    <div className="space-y-2">
                      <Label htmlFor="invite-role">Invitation Role *</Label>
                      <Select value={selectedMemberRole} onValueChange={setSelectedMemberRole}>
                        <SelectTrigger id="invite-role">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="member">Member</SelectItem>
                          <SelectItem value="team_leader">Team Leader</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Only admins can send team leader invitations.
                      </p>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => {
                    setInviteEmailOpen(false)
                    setInviteEmail('')
                    setSelectedMemberRole('member')
                  }}>Cancel</Button>
                  <Button onClick={handleInviteEmailSubmit} disabled={!inviteEmail.trim()}>
                    <Mail className="h-4 w-4 mr-2" />
                    Send Invitation
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>
    </div>
  )
}
