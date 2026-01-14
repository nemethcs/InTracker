import api from './api'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  name?: string
  invitation_code: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface User {
  id: string
  email: string
  name?: string
  role?: string
  github_username?: string
  avatar_url?: string
  github_connected_at?: string
  github_token_expires_at?: string
  onboarding_step?: number
  mcp_verified_at?: string
  setup_completed?: boolean
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  async register(data: RegisterData): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Even if logout endpoint fails, we should still clear tokens
      console.warn('Logout endpoint failed, clearing tokens anyway:', error)
    }
    // Always clear tokens, regardless of endpoint response
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me')
    return response.data
  },

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data.tokens
  },
}
