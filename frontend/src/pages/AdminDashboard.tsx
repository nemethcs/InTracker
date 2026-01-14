import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { adminService, type User, type Team, type Invitation, type TeamMember } from '@/services/adminService'
import { Users, UsersRound, Mail, Shield, Trash2, Edit, Plus, Copy, CheckCircle2, XCircle, UserPlus, UserMinus, ChevronDown, ChevronUp } from 'lucide-react'
import { useToast } from '@/hooks/useToast'
import { iconSize } from '@/components/ui/Icon'
import { PageHeader } from '@/components/layout/PageHeader'

type Tab = 'users' | 'teams' | 'invitations'

export function AdminDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('users')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check if user is admin
  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/')
    }
  }, [user, navigate])

  if (!user || user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>You need admin privileges to access this page.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin Dashboard"
        description="Manage users, teams, and invitations"
      />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as Tab)} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="users" className="flex items-center gap-2">
            <Users className={iconSize('sm')} />
            Users
          </TabsTrigger>
          <TabsTrigger value="teams" className="flex items-center gap-2">
            <UsersRound className={iconSize('sm')} />
            Teams
          </TabsTrigger>
          <TabsTrigger value="invitations" className="flex items-center gap-2">
            <Mail className={iconSize('sm')} />
            Invitations
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        <TabsContent value="users" className="mt-6">
          <UsersTab />
        </TabsContent>
        <TabsContent value="teams" className="mt-6">
          <TeamsTab />
        </TabsContent>
        <TabsContent value="invitations" className="mt-6">
          <InvitationsTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}

// Users Tab Component
function UsersTab() {
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')

  useEffect(() => {
    loadUsers()
  }, [roleFilter, search])

  const loadUsers = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await adminService.getUsers({
        role: roleFilter || undefined,
        search: search || undefined,
      })
      setUsers(response.users)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return
    try {
      await adminService.deleteUser(userId)
      loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user')
    }
  }

  const handleUpdateRole = async (userId: string, newRole: string) => {
    try {
      await adminService.updateUserRole(userId, newRole)
      loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user role')
    }
  }

  if (isLoading) {
    return <LoadingState variant="combined" size="md" skeletonCount={5} />
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search by email or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="h-10 rounded-md border border-input bg-background px-3 py-2"
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="team_leader">Team Leader</option>
          <option value="member">Member</option>
        </select>
      </div>

      {/* Users Table */}
      {users.length === 0 ? (
        <EmptyState
          icon={<Users className={iconSize('lg')} />}
          title="No users found"
          description="No users match your search criteria"
          variant="compact"
        />
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.email}</TableCell>
                  <TableCell>{user.name || '-'}</TableCell>
                  <TableCell>
                    <select
                      value={user.role}
                      onChange={(e) => handleUpdateRole(user.id, e.target.value)}
                      className="h-8 rounded-md border border-input bg-background px-2 py-1 text-sm"
                    >
                      <option value="member">Member</option>
                      <option value="team_leader">Team Leader</option>
                      <option value="admin">Admin</option>
                    </select>
                  </TableCell>
                  <TableCell>
                    {!user.is_active && (
                      <span className="px-2 py-1 rounded text-xs bg-muted text-muted-foreground">
                        Inactive
                      </span>
                    )}
                    {user.is_active && (
                      <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        Active
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(user.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteUser(user.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

// Teams Tab Component
function TeamsTab() {
  const toast = useToast()
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set())
  const [teamMembers, setTeamMembers] = useState<Record<string, TeamMember[]>>({})
  const [teamInvitations, setTeamInvitations] = useState<Record<string, Invitation[]>>({})
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  
  // Dialog states
  const [createTeamOpen, setCreateTeamOpen] = useState(false)
  const [editTeamOpen, setEditTeamOpen] = useState(false)
  const [addMemberOpen, setAddMemberOpen] = useState(false)
  const [inviteEmailOpen, setInviteEmailOpen] = useState(false)
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null)
  const [teamForm, setTeamForm] = useState({ name: '', description: '' })
  const [selectedUserId, setSelectedUserId] = useState('')
  const [selectedMemberRole, setSelectedMemberRole] = useState('member')
  const [inviteEmail, setInviteEmail] = useState('')

  useEffect(() => {
    loadTeams()
    loadAllUsers()
  }, [])

  const loadTeams = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await adminService.getTeams()
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

  const loadTeamMembers = async (teamId: string) => {
    try {
      const members = await adminService.getTeamMembers(teamId)
      setTeamMembers(prev => ({ ...prev, [teamId]: members }))
    } catch (err) {
      console.error('Failed to load team members:', err)
    }
  }

  const toggleTeamExpanded = (teamId: string) => {
    const newExpanded = new Set(expandedTeams)
    if (newExpanded.has(teamId)) {
      newExpanded.delete(teamId)
    } else {
      newExpanded.add(teamId)
      if (!teamMembers[teamId]) {
        loadTeamMembers(teamId)
      }
      if (!teamInvitations[teamId]) {
        loadTeamInvitations(teamId)
      }
    }
    setExpandedTeams(newExpanded)
  }

  const loadTeamInvitations = async (teamId: string) => {
    try {
      const response = await adminService.getInvitations({ type: 'team' })
      const teamInvites = response.invitations.filter(inv => inv.team_id === teamId)
      setTeamInvitations(prev => ({ ...prev, [teamId]: teamInvites }))
    } catch (err) {
      console.error('Failed to load team invitations:', err)
      setTeamInvitations(prev => ({ ...prev, [teamId]: [] }))
    }
  }

  const handleCreateTeamInvitation = async (teamId: string, email?: string) => {
    try {
      const invitation = await adminService.createTeamInvitation(teamId, 7, email)
      setTeamInvitations(prev => ({
        ...prev,
        [teamId]: [...(prev[teamId] || []), invitation]
      }))
      if (email) {
        setInviteEmailOpen(false)
        setInviteEmail('')
        toast.success('Invitation sent', 'Team invitation email has been sent successfully.')
      } else {
        toast.success('Invitation created', 'Team invitation code has been created successfully.')
      }
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
    await handleCreateTeamInvitation(selectedTeam.id, inviteEmail.trim())
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
    toast.success('Code copied', 'Invitation code has been copied to clipboard.')
  }

  const handleCreateTeam = async () => {
    if (!teamForm.name.trim()) {
      setError('Team name is required')
      return
    }
    try {
      await adminService.createTeam(teamForm)
      setCreateTeamOpen(false)
      setTeamForm({ name: '', description: '' })
      loadTeams()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create team')
    }
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
      setSelectedTeam(null)
      setTeamForm({ name: '', description: '' })
      loadTeams()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update team')
    }
  }

  const handleDeleteTeam = async (teamId: string) => {
    if (!confirm('Are you sure you want to delete this team?')) return
    try {
      await adminService.deleteTeam(teamId)
      loadTeams()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete team')
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
      setSelectedTeam(null)
      setSelectedUserId('')
      if (expandedTeams.has(selectedTeam.id)) {
        loadTeamMembers(selectedTeam.id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add member')
    }
  }

  const handleRemoveMember = async (teamId: string, userId: string) => {
    if (!confirm('Are you sure you want to remove this member from the team?')) return
    try {
      await adminService.removeTeamMember(teamId, userId)
      loadTeamMembers(teamId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member')
    }
  }

  const handleUpdateMemberRole = async (teamId: string, userId: string, newRole: string) => {
    try {
      await adminService.updateTeamMemberRole(teamId, userId, newRole)
      loadTeamMembers(teamId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update member role')
    }
  }

  // Get users not in team
  const getAvailableUsers = (teamId: string) => {
    const memberUserIds = new Set(teamMembers[teamId]?.map(m => m.user_id) || [])
    return allUsers.filter(user => !memberUserIds.has(user.id))
  }

  if (isLoading) {
    return <LoadingState variant="combined" size="md" skeletonCount={5} />
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      <div className="flex justify-end">
        <Button onClick={() => setCreateTeamOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Team
        </Button>
      </div>

      <div className="grid gap-4">
        {teams.map((team) => {
          const isExpanded = expandedTeams.has(team.id)
          const members = teamMembers[team.id] || []
          const availableUsers = getAvailableUsers(team.id)
          
          return (
            <Card key={team.id}>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold">{team.name}</h3>
                      {team.description && (
                        <p className="text-sm text-muted-foreground mt-1">{team.description}</p>
                      )}
                      <p className="text-sm text-muted-foreground mt-1">
                        Created: {new Date(team.created_at).toLocaleDateString()}
                        {members.length > 0 && (
                          <> • {members.length} member{members.length !== 1 ? 's' : ''}</>
                        )}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleTeamExpanded(team.id)}
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="h-4 w-4 mr-1" />
                            Hide Members
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-4 w-4 mr-1" />
                            Show Members
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditTeam(team)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteTeam(team.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t pt-4 space-y-4">
                      {/* Team Members Section */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">Team Members</h4>
                          <Button
                            size="sm"
                            onClick={() => handleAddMember(team)}
                            disabled={availableUsers.length === 0}
                          >
                            <UserPlus className="h-4 w-4 mr-1" />
                            Add Member
                          </Button>
                        </div>
                        
                        {members.length === 0 ? (
                          <p className="text-sm text-muted-foreground">No members yet</p>
                        ) : (
                          <div className="space-y-2">
                            {members.map((member) => {
                              const user = allUsers.find(u => u.id === member.user_id)
                              return (
                                <div key={member.id} className="flex items-center justify-between p-2 border rounded">
                                  <div className="flex-1">
                                    <p className="font-medium">{user?.name || user?.email || 'Unknown'}</p>
                                    <p className="text-sm text-muted-foreground">{user?.email}</p>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <select
                                      value={member.role}
                                      onChange={(e) => handleUpdateMemberRole(team.id, member.user_id, e.target.value)}
                                      className="h-8 rounded-md border border-input bg-background px-2 py-1 text-sm"
                                    >
                                      <option value="member">Member</option>
                                      <option value="team_leader">Team Leader</option>
                                    </select>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleRemoveMember(team.id, member.user_id)}
                                    >
                                      <UserMinus className="h-4 w-4 text-destructive" />
                                    </Button>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>

                      {/* Team Invitations Section */}
                      <div className="border-t pt-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium">Team Invitations</h4>
                            <p className="text-sm text-muted-foreground">Create and manage team invitation codes</p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => {
                                setSelectedTeam(team)
                                setInviteEmailOpen(true)
                              }}
                            >
                              <Mail className="h-4 w-4 mr-1" />
                              Send Email
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleCreateTeamInvitation(team.id)}
                            >
                              <Plus className="h-4 w-4 mr-1" />
                              Create Code
                            </Button>
                          </div>
                        </div>

                        {teamInvitations[team.id] && teamInvitations[team.id].length > 0 ? (
                          <div className="space-y-2">
                            {teamInvitations[team.id].map((inv) => (
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
                                    {inv.used_at && (
                                      <> • Used: {new Date(inv.used_at).toLocaleDateString()}</>
                                    )}
                                  </p>
                                </div>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleCopyCode(inv.code)}
                                  disabled={!!inv.used_at}
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
                        ) : (
                          <p className="text-sm text-muted-foreground">No invitations yet</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
        {teams.length === 0 && (
          <EmptyState
            icon={<UsersRound className={iconSize('lg')} />}
            title="No teams found"
            description="Create your first team to get started"
            variant="compact"
          />
        )}
      </div>

      {/* Create Team Dialog */}
      <Dialog open={createTeamOpen} onOpenChange={setCreateTeamOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Team</DialogTitle>
            <DialogDescription>Create a new team with a name and optional description.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="team-name">Team Name *</Label>
              <Input
                id="team-name"
                value={teamForm.name}
                onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
                placeholder="Enter team name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="team-description">Description</Label>
              <Input
                id="team-description"
                value={teamForm.description}
                onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
                placeholder="Enter team description (optional)"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateTeamOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateTeam}>Create Team</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
      <Dialog open={inviteEmailOpen} onOpenChange={setInviteEmailOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Team Invitation</DialogTitle>
            <DialogDescription>Send an invitation email to join {selectedTeam?.name}.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="invite-email">Email Address *</Label>
              <Input
                id="invite-email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="Enter email address"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setInviteEmailOpen(false)
              setInviteEmail('')
            }}>Cancel</Button>
            <Button onClick={handleInviteEmailSubmit} disabled={!inviteEmail.trim()}>
              Send Invitation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Invitations Tab Component
function InvitationsTab() {
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  useEffect(() => {
    loadInvitations()
  }, [])

  const loadInvitations = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await adminService.getInvitations()
      setInvitations(response.invitations)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load invitations')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateAdminInvitation = async () => {
    try {
      await adminService.createAdminInvitation(30)
      loadInvitations()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invitation')
    }
  }

  const handleDeleteInvitation = async (code: string) => {
    if (!confirm('Are you sure you want to delete this invitation?')) return
    try {
      await adminService.deleteInvitation(code)
      loadInvitations()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete invitation')
    }
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  if (isLoading) {
    return <LoadingState variant="combined" size="md" skeletonCount={5} />
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      <div className="flex justify-end">
        <Button onClick={handleCreateAdminInvitation}>
          <Plus className="h-4 w-4 mr-2" />
          Create Admin Invitation
        </Button>
      </div>

      {invitations.length === 0 ? (
        <EmptyState
          icon={<Mail className={iconSize('lg')} />}
          title="No invitations found"
          description="Create an invitation to allow new users to join"
          variant="compact"
        />
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invitations.map((inv) => (
                <TableRow key={inv.code}>
                  <TableCell>
                    <code className="text-sm font-mono bg-muted px-2 py-1 rounded">
                      {inv.code}
                    </code>
                  </TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded text-xs ${
                      inv.type === 'admin' ? 'bg-destructive/10 text-destructive dark:bg-destructive/20' : 'bg-primary/10 text-primary dark:bg-primary/20'
                    }`}>
                      {inv.type}
                    </span>
                  </TableCell>
                  <TableCell>
                    {inv.used_at ? (
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <CheckCircle2 className="h-3 w-3" />
                        Used
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <XCircle className="h-3 w-3" />
                        Unused
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(inv.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {inv.expires_at ? new Date(inv.expires_at).toLocaleDateString() : '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
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
                      {!inv.used_at && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteInvitation(inv.code)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
