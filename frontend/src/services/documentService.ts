import api from './api'

export interface Document {
  id: string
  project_id: string
  element_id?: string
  type: 'architecture' | 'adr' | 'notes'
  title: string
  content: string
  tags: string[]
  version: number
  created_at: string
  updated_at: string
}

export interface DocumentCreate {
  project_id: string
  element_id?: string
  type: Document['type']
  title: string
  content: string
  tags?: string[]
}

export interface DocumentUpdate {
  title?: string
  content?: string
  tags?: string[]
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  page_size: number
}

export const documentService = {
  async listDocuments(projectId: string, type?: string, elementId?: string): Promise<Document[]> {
    const params: Record<string, string> = {}
    if (type) params.type = type
    if (elementId) params.element_id = elementId

    const response = await api.get(`/documents/project/${projectId}`, { params })
    // Backend returns { documents: [...], total, page, page_size }
    return response.data.documents || []
  },

  async getDocument(id: string): Promise<Document> {
    const response = await api.get(`/documents/${id}`)
    return response.data
  },

  async getDocumentContent(id: string): Promise<{ id: string; title: string; type: string; content: string; version: number }> {
    const response = await api.get(`/documents/${id}/content`)
    return response.data
  },

  async createDocument(data: DocumentCreate): Promise<Document> {
    const response = await api.post('/documents', data)
    return response.data
  },

  async updateDocument(id: string, data: DocumentUpdate): Promise<Document> {
    const response = await api.put(`/documents/${id}`, data)
    return response.data
  },

  async deleteDocument(id: string): Promise<void> {
    await api.delete(`/documents/${id}`)
  },
}
