import api from './api'

export interface Feature {
  id: string
  project_id: string
  name: string
  description?: string
  status: 'new' | 'in_progress' | 'tested' | 'done'
  progress_percentage: number
  total_todos: number
  completed_todos: number
  created_at: string
  updated_at: string
}

export interface FeatureCreate {
  project_id: string
  name: string
  description?: string
  element_ids?: string[]
}

export interface FeatureUpdate {
  name?: string
  description?: string
  status?: Feature['status']
}

export const featureService = {
  async listFeatures(projectId?: string): Promise<Feature[]> {
    if (!projectId) {
      return []
    }
    // Backend endpoint: GET /features/project/{project_id}
    const response = await api.get(`/features/project/${projectId}`)
    // Backend returns { features: [...], total: ... }
    return response.data.features || response.data || []
  },

  async getFeature(id: string): Promise<Feature> {
    const response = await api.get(`/features/${id}`)
    return response.data
  },

  async createFeature(data: FeatureCreate): Promise<Feature> {
    const response = await api.post('/features', data)
    return response.data
  },

  async updateFeature(id: string, data: FeatureUpdate): Promise<Feature> {
    const response = await api.put(`/features/${id}`, data)
    return response.data
  },

  async deleteFeature(id: string): Promise<void> {
    await api.delete(`/features/${id}`)
  },
}
