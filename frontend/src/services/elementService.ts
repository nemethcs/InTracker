import api from './api'

export interface Element {
  id: string
  project_id: string
  parent_id?: string
  type: 'milestone' | 'module' | 'component' | 'task'
  title: string
  description?: string
  status: 'new' | 'in_progress' | 'tested' | 'done'
  position?: number
  definition_of_done?: string
  github_issue_number?: number
  github_issue_url?: string
  created_at: string
  updated_at: string
  todos_count?: number
  todos_done_count?: number
  features_count?: number
  linked_features?: string[]
  children?: Element[]
}

export interface ElementTree {
  project_id: string
  elements: Element[]
}

export interface ElementCreate {
  project_id: string
  type: Element['type']
  title: string
  description?: string
  status?: Element['status']
  parent_id?: string
  position?: number
  definition_of_done?: string
}

export interface ElementUpdate {
  title?: string
  description?: string
  status?: Element['status']
  parent_id?: string
  position?: number
  definition_of_done?: string
}

export const elementService = {
  async getProjectTree(projectId: string): Promise<ElementTree> {
    const response = await api.get(`/elements/project/${projectId}/tree`)
    return response.data
  },

  async getElement(id: string): Promise<Element> {
    const response = await api.get(`/elements/${id}`)
    return response.data
  },

  async createElement(data: ElementCreate): Promise<Element> {
    const response = await api.post('/elements', data)
    return response.data
  },

  async updateElement(id: string, data: ElementUpdate): Promise<Element> {
    const response = await api.put(`/elements/${id}`, data)
    return response.data
  },

  async deleteElement(id: string): Promise<void> {
    await api.delete(`/elements/${id}`)
  },
}
