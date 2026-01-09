import api from './api'

export interface User {
  id: string
  email: string
  name?: string
  role: string
  is_active: boolean
  github_username?: string
  avatar_url?: string
  created_at: string
  last_login_at?: string
}

export interface Team {
  id: string
  name: string
  description?: string
  language?: string // 'hu' (Hungarian) or 'en' (English)
  created_by: string
  created_at: string
  updated_at: string
}

export interface Invitation {
  code: string
  type: string
  team_id?: string
  created_by: string
  expires_at?: string
  used_at?: string
  used_by?: string
  created_at: string
}

export interface UserListResponse {
  users: User[]
  total: number
  skip: number
  limit: number
}

export interface TeamListResponse {
  teams: Team[]
  total: number
}

export interface InvitationListResponse {
  invitations: Invitation[]
  total: number
  skip: number
  limit: number
}

export interface TeamMember {
  id: string
  team_id: string
  user_id: string
  role: string
  joined_at: string
}

export const adminService = {
  // User Management
  async getUsers(params?: { role?: string; search?: string; skip?: number; limit?: number }): Promise<UserListResponse> {
    const response = await api.get('/admin/users', { params })
    return response.data
  },

  async getUser(userId: string): Promise<User> {
    const response = await api.get(`/admin/users/${userId}`)
    return response.data
  },

  async updateUser(userId: string, data: { name?: string; email?: string; is_active?: boolean }): Promise<User> {
    const response = await api.put(`/admin/users/${userId}`, data)
    return response.data.user
  },

  async updateUserRole(userId: string, role: string): Promise<User> {
    const response = await api.put(`/admin/users/${userId}/role`, null, { params: { role } })
    return response.data.user
  },

  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/admin/users/${userId}`)
  },

  async createUser(data: { email: string; password: string; name?: string }): Promise<User> {
    const response = await api.post('/admin/create-user', null, { params: data })
    return response.data.user
  },

  // Team Management (via teams endpoint, but admin sees all)
  async getTeams(skip?: number, limit?: number): Promise<TeamListResponse> {
    const response = await api.get('/teams', { params: { skip, limit } })
    return response.data
  },

  async getTeam(teamId: string): Promise<Team> {
    const response = await api.get(`/teams/${teamId}`)
    return response.data
  },

  async createTeam(data: { name: string; description?: string }): Promise<Team> {
    const response = await api.post('/teams', data)
    return response.data
  },

  async updateTeam(teamId: string, data: { name?: string; description?: string }): Promise<Team> {
    const response = await api.put(`/teams/${teamId}`, data)
    return response.data
  },

  async deleteTeam(teamId: string): Promise<void> {
    await api.delete(`/teams/${teamId}`)
  },

  async getTeamMembers(teamId: string): Promise<TeamMember[]> {
    const response = await api.get(`/teams/${teamId}/members`)
    return response.data
  },

  async addTeamMember(teamId: string, userId: string, role: string = 'member'): Promise<TeamMember> {
    const response = await api.post(`/teams/${teamId}/members`, null, { params: { user_id: userId, role } })
    return response.data
  },

  async removeTeamMember(teamId: string, userId: string): Promise<void> {
    await api.delete(`/teams/${teamId}/members/${userId}`)
  },

  async updateTeamMemberRole(teamId: string, userId: string, role: string): Promise<TeamMember> {
    const response = await api.put(`/teams/${teamId}/members/${userId}/role`, null, { params: { role } })
    return response.data
  },

  async createTeamInvitation(teamId: string, expiresInDays?: number): Promise<Invitation> {
    const response = await api.post(`/teams/${teamId}/invitations`, null, { params: { expires_in_days: expiresInDays || 7 } })
    return response.data
  },

  // Invitation Management
  async getInvitations(params?: { type?: string; used?: boolean; skip?: number; limit?: number }): Promise<InvitationListResponse> {
    const response = await api.get('/admin/invitations', { params })
    return response.data
  },

  async getInvitation(code: string): Promise<Invitation> {
    const response = await api.get(`/admin/invitations/${code}`)
    return response.data
  },

  async createAdminInvitation(expiresInDays?: number): Promise<Invitation> {
    const response = await api.post('/admin/invitations/admin', null, { params: { expires_in_days: expiresInDays || 30 } })
    return response.data.invitation
  },

  async deleteInvitation(code: string): Promise<void> {
    await api.delete(`/admin/invitations/${code}`)
  },
}
