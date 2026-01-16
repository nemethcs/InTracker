import { useEffect, useRef } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { useAuthStore } from '@/stores/authStore'

export function useAuth() {
  const { user, isAuthenticated, isLoading, checkAuth, login, register, logout } = useAuthStore(
    useShallow((state) => ({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
      isLoading: state.isLoading,
      checkAuth: state.checkAuth,
      login: state.login,
      register: state.register,
      logout: state.logout,
    }))
  )
  const hasChecked = useRef(false)

  useEffect(() => {
    if (!hasChecked.current) {
      hasChecked.current = true
      checkAuth()
    }
  }, []) // Only run once on mount

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
  }
}
