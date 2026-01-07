import { useEffect, useRef } from 'react'
import { useTodoStore } from '@/stores/todoStore'

export function useTodos(featureId?: string, elementId?: string) {
  const {
    todos,
    isLoading,
    error,
    fetchTodos,
  } = useTodoStore()

  const lastFeatureId = useRef<string | undefined>(undefined)
  const lastElementId = useRef<string | undefined>(undefined)

  useEffect(() => {
    // Only fetch if featureId or elementId changed
    if (featureId !== lastFeatureId.current || elementId !== lastElementId.current) {
      lastFeatureId.current = featureId
      lastElementId.current = elementId
      fetchTodos(featureId, elementId)
    }
  }, [featureId, elementId]) // Remove fetchTodos from dependencies

  return {
    todos,
    isLoading,
    error,
    refetch: () => fetchTodos(featureId, elementId),
  }
}
