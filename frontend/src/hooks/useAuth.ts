import { useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/authStore'

export function useAuth() {
  const { user, isAuthenticated, isLoading, checkAuth, login, register, logout } = useAuthStore()
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
