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

export function Teams() {
  const { user } = useAuth()
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
  const [teamForm, setTeamForm] = useState({ name: '', description: '' })
  const [selectedUserId, setSelectedUserId] = useState('')
  const [selectedMemberRole, setSelectedMemberRole] = useState('member')

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

  const handleCreateTeamInvitation = async (teamId: string) => {
    try {
      const invitation = await adminService.createTeamInvitation(teamId, 7)
      setTeamInvitations([...teamInvitations, invitation])
      loadTeamDetails(teamId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invitation')
    }
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
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
      <div>
        <h1 className="text-3xl font-bold">Teams</h1>
        <p className="text-muted-foreground">Manage your teams and members</p>
      </div>

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
                {selectedTeam.language && (
                  <div>
                    <Label>Language</Label>
                    <p className="text-sm font-medium">
                      {selectedTeam.language === 'hu' ? 'Hungarian (Magyar)' : selectedTeam.language === 'en' ? 'English' : selectedTeam.language}
                    </p>
                  </div>
                )}
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
                      const memberUser = getUserInfo(member.user_id)
                      return (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-2 rounded border"
                        >
                          <div className="flex-1">
                            <p className="text-sm font-medium">
                              {memberUser?.name || memberUser?.email || `User ${member.user_id.slice(0, 8)}...`}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {memberUser?.email && memberUser.name ? memberUser.email : ''}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {member.role} • Joined {new Date(member.joined_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {member.role === 'team_leader' && (
                              <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
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
                  <Button
                    onClick={() => handleCreateTeamInvitation(selectedTeam.id)}
                    className="w-full"
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Create Team Invitation
                  </Button>

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
          </div>
        )}
      </div>
    </div>
  )
}
