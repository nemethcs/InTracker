import api from './api'

export interface Todo {
  id: string
  element_id: string
  feature_id?: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'blocked' | 'done'
  estimated_effort?: number
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
  estimated_effort?: number
}

export interface TodoUpdate {
  title?: string
  description?: string
  status?: Todo['status']
  estimated_effort?: number
  assigned_to?: string
  expected_version?: number
}

export const todoService = {
  async listTodos(featureId?: string, elementId?: string): Promise<Todo[]> {
    const params: Record<string, string> = {}
    if (featureId) params.feature_id = featureId
    if (elementId) params.element_id = elementId
    const response = await api.get('/todos', { params })
    return response.data
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
    const response = await api.put(`/todos/${id}`, data)
    return response.data
  },

  async deleteTodo(id: string): Promise<void> {
    await api.delete(`/todos/${id}`)
  },
}
