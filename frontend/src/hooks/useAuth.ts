import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'

export function useAuth() {
  const { user, isAuthenticated, isLoading, checkAuth, login, register, logout } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
  }
}
