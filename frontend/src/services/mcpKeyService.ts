import api from './api'

export interface McpApiKey {
  id: string
  user_id: string
  name?: string | null
  last_used_at?: string | null
  expires_at?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface McpApiKeyCreate {
  name?: string
  expires_in_days?: number
}

export interface McpApiKeyCreateResponse {
  key: McpApiKey
  plain_text_key: string
}

export const mcpKeyService = {
  async getCurrentKey(): Promise<McpApiKey> {
    const response = await api.get('/mcp-keys/current')
    return response.data
  },

  async regenerateKey(data: McpApiKeyCreate = {}): Promise<McpApiKeyCreateResponse> {
    const response = await api.post('/mcp-keys/regenerate', data)
    return response.data
  },
}
