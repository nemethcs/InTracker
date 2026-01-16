import api from './api'

export interface Idea {
  id: string
  title: string
  description?: string
  status: 'draft' | 'active' | 'archived'
  team_id: string
  tags?: string[]
  converted_to_project_id?: string
  created_at: string
  updated_at: string
}

export interface IdeaCreate {
  title: string
  team_id: string
  description?: string
  status?: Idea['status']
  tags?: string[]
}

export interface IdeaUpdate {
  title?: string
  description?: string
  status?: Idea['status']
  tags?: string[]
}

export interface IdeaConvertRequest {
  project_name?: string
  project_description?: string
  project_status?: 'active' | 'paused' | 'blocked' | 'completed' | 'archived'
  project_tags?: string[]
  technology_tags?: string[]
}

export const ideaService = {
  async listIdeas(status?: string, teamId?: string): Promise<Idea[]> {
    const params: Record<string, string> = {}
    if (status) params.status = status
    if (teamId) params.team_id = teamId
    const response = await api.get('/ideas', { params })
    // Backend returns { ideas: [...], total: ... }
    return response.data.ideas || response.data || []
  },

  async getIdea(id: string): Promise<Idea> {
    const response = await api.get(`/ideas/${id}`)
    return response.data
  },

  async createIdea(data: IdeaCreate): Promise<Idea> {
    const response = await api.post('/ideas', data)
    return response.data
  },

  async updateIdea(id: string, data: IdeaUpdate): Promise<Idea> {
    const response = await api.put(`/ideas/${id}`, data)
    return response.data
  },

  async deleteIdea(id: string): Promise<void> {
    await api.delete(`/ideas/${id}`)
  },

  async convertIdeaToProject(id: string, data: IdeaConvertRequest): Promise<{ id: string; name: string }> {
    const response = await api.post(`/ideas/${id}/convert`, data)
    return response.data
  },
}
