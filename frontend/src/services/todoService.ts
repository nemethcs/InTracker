import api from './api'

export interface Todo {
  id: string
  element_id: string
  feature_id?: string
  title: string
  description?: string
  status: 'new' | 'in_progress' | 'tested' | 'done'
  priority?: 'low' | 'medium' | 'high' | 'critical'
  assigned_to?: string
  version: number
  created_at: string
  updated_at: string
}

export interface TodoCreate {
  element_id: string
  title: string
  description?: string
  feature_id?: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
}

export interface TodoUpdate {
  title?: string
  description?: string
  status?: Todo['status']
  priority?: 'low' | 'medium' | 'high' | 'critical'
  assigned_to?: string
  expected_version?: number
}

export const todoService = {
  async listTodos(featureId?: string, elementId?: string, projectId?: string): Promise<Todo[]> {
    // If featureId is provided, use the feature-specific endpoint
    if (featureId) {
      const response = await api.get(`/features/${featureId}/todos`)
      // Backend returns { todos: [...], count: ... }
      return response.data.todos || []
    }
    
    // Otherwise, use the general todos endpoint
    const params: Record<string, string> = {}
    if (projectId) params.project_id = projectId
    if (elementId) params.element_id = elementId
    const response = await api.get('/todos', { params })
    // Backend returns { todos: [...], total: ... }
    return response.data.todos || response.data || []
  },

  async getTodo(id: string): Promise<Todo> {
    const response = await api.get(`/todos/${id}`)
    return response.data
  },

  async createTodo(data: TodoCreate): Promise<Todo> {
    const response = await api.post('/todos', data)
    return response.data
  },

  async updateTodo(id: string, data: TodoUpdate): Promise<Todo> {
    try {
      const response = await api.put(`/todos/${id}`, data)
      return response.data
    } catch (error: any) {
      // Handle conflict (409) - optimistic locking failure
      if (error.response?.status === 409) {
        const conflictError = new Error(error.response?.data?.detail || 'Todo was modified by another user. Please refresh and try again.')
        ;(conflictError as any).isConflict = true
        ;(conflictError as any).currentVersion = error.response?.data?.current_version
        throw conflictError
      }
      throw error
    }
  },

  async deleteTodo(id: string): Promise<void> {
    await api.delete(`/todos/${id}`)
  },
}
