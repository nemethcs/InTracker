import { create } from 'zustand'
import { authService, type User, type AuthTokens } from '@/services/authService'
import { signalrService } from '@/services/signalrService'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: User | null) => void
  setTokens: (tokens: AuthTokens) => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email: string, password: string) => {
    const { tokens, user } = await authService.login({ email, password })
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    set({ user, isAuthenticated: true, isLoading: false })
    // Connect to SignalR after login
    try {
      await signalrService.connect(tokens.access_token)
    } catch (error) {
      console.error('Failed to connect to SignalR:', error)
    }
  },

  register: async (email: string, password: string, name?: string) => {
    const { tokens, user } = await authService.register({ email, password, name })
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    set({ user, isAuthenticated: true, isLoading: false })
    // Connect to SignalR after registration
    try {
      await signalrService.connect(tokens.access_token)
    } catch (error) {
      console.error('Failed to connect to SignalR:', error)
    }
  },

  logout: async () => {
    // Disconnect SignalR before logout
    await signalrService.disconnect()
    await authService.logout()
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user })
  },

  setTokens: (tokens: AuthTokens) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  },

  checkAuth: async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        set({ isAuthenticated: false, isLoading: false })
        return
      }
      const user = await authService.getCurrentUser()
      set({ user, isAuthenticated: true, isLoading: false })
      // Connect to SignalR if authenticated
      try {
        await signalrService.connect(token)
      } catch (error) {
        console.error('Failed to connect to SignalR:', error)
      }
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
