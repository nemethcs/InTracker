import api from './api'

export interface ActiveUser {
  id: string
  email: string
  name: string | null
  avatarUrl: string | null
}

export interface ActiveUsersResponse {
  projectId: string
  activeUsers: ActiveUser[]
  count: number
}

export const collaborationService = {
  /**
   * Get active users for a project
   */
  async getActiveUsers(projectId: string): Promise<ActiveUsersResponse> {
    const response = await api.get<ActiveUsersResponse>(`/signalr/hub/projects/${projectId}/active-users`)
    return response.data
  },
}
