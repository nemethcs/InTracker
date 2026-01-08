import api from './api'

export interface ActiveUser {
  id: string
  email: string
  name: string | null
  avatar_url: string | null
}

export interface ActiveUsersResponse {
  active_users: ActiveUser[]
  count: number
}

export const collaborationService = {
  /**
   * Get active users for a project (users with open MCP sessions on project todos).
   * Active user = user with open session (ended_at IS NULL) on the project.
   * If no open sessions, returns empty array.
   */
  async getActiveUsers(projectId: string): Promise<ActiveUsersResponse> {
    const response = await api.get<ActiveUsersResponse>(`/projects/${projectId}/active-users`)
    // Backend returns { active_users: [...], count: ... }
    // Map avatar_url to avatarUrl for backward compatibility
    const data = response.data
    if (data.active_users) {
      data.active_users = data.active_users.map(user => ({
        ...user,
        avatarUrl: user.avatar_url,
      }))
    }
    return {
      activeUsers: data.active_users || [],
      count: data.count || 0,
    } as any
  },
}
