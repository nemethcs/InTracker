import { useEffect } from 'react'
import { useTodoStore } from '@/stores/todoStore'

export function useTodos(featureId?: string, elementId?: string) {
  const {
    todos,
    isLoading,
    error,
    fetchTodos,
  } = useTodoStore()

  useEffect(() => {
    fetchTodos(featureId, elementId)
  }, [featureId, elementId, fetchTodos])

  return {
    todos,
    isLoading,
    error,
    refetch: () => fetchTodos(featureId, elementId),
  }
}
