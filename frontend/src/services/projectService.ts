import api from './api'

export interface Project {
  id: string
  name: string
  description?: string
  status: 'active' | 'paused' | 'blocked' | 'completed' | 'archived'
  tags?: string[]
  technology_tags?: string[]
  created_at: string
  updated_at: string
  last_session_at?: string
  resume_context?: {
    last?: string
    now?: string
    next?: string
    blockers?: string[]
    constraints?: string[]
  }
  cursor_instructions?: string
  github_repo_url?: string
  github_repo_id?: string
}

export interface ProjectCreate {
  name: string
  description?: string
  tags?: string[]
  technology_tags?: string[]
  cursor_instructions?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  status?: Project['status']
  tags?: string[]
  technology_tags?: string[]
  cursor_instructions?: string
}

export const projectService = {
  async listProjects(): Promise<Project[]> {
    const response = await api.get('/projects')
    // Backend returns { projects: [...], total, page, page_size }
    return response.data.projects || response.data || []
  },

  async getProject(id: string): Promise<Project> {
    const response = await api.get(`/projects/${id}`)
    return response.data
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await api.post('/projects', data)
    return response.data
  },

  async updateProject(id: string, data: ProjectUpdate): Promise<Project> {
    const response = await api.put(`/projects/${id}`, data)
    return response.data
  },

  async deleteProject(id: string): Promise<void> {
    await api.delete(`/projects/${id}`)
  },
}
