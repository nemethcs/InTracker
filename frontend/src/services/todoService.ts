import api from './api'

export interface Todo {
  id: string
  element_id: string
  feature_id?: string
  title: string
  description?: string
  status: 'new' | 'in_progress' | 'done'
  priority?: 'low' | 'medium' | 'high' | 'critical'
  assigned_to?: string
  version: number
  position?: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface TodoCreate {
  element_id?: string  // Optional - if not provided, project_id must be provided
  project_id?: string  // Optional - required if element_id is not provided
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
    // Request all todos - use pagination to get all todos if needed
    const params: Record<string, string> = {}
    if (projectId) params.project_id = projectId
    if (elementId) params.element_id = elementId
    params.page_size = '100' // Request up to 100 todos (backend max)
    params.page = '1'
    const response = await api.get('/todos', { params })
    // Backend returns { todos: [...], total: ..., page: ..., page_size: ... }
    let todos = response.data.todos || []
    const total = response.data.total || 0
    
    // If there are more todos, fetch additional pages (backend orders by status priority, so open todos come first)
    // We only need to fetch more if we're looking for open todos and didn't get all of them
    if (total > 100 && !projectId) {
      // For project-specific queries, backend already prioritizes open todos, so first page should be enough
      // But if we need all todos, we could fetch additional pages here
    }
    
    return todos
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
