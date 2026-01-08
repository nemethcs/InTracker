import { useEffect, useRef } from 'react'
import { useTodoStore } from '@/stores/todoStore'

export function useTodos(featureId?: string, elementId?: string, projectId?: string) {
  const {
    todos,
    isLoading,
    error,
    fetchTodos,
  } = useTodoStore()

  const lastFeatureId = useRef<string | undefined>(undefined)
  const lastElementId = useRef<string | undefined>(undefined)
  const lastProjectId = useRef<string | undefined>(undefined)

  useEffect(() => {
    // Only fetch if featureId, elementId, or projectId changed
    if (
      featureId !== lastFeatureId.current ||
      elementId !== lastElementId.current ||
      projectId !== lastProjectId.current
    ) {
      lastFeatureId.current = featureId
      lastElementId.current = elementId
      lastProjectId.current = projectId
      fetchTodos(featureId, elementId, projectId)
    }
  }, [featureId, elementId, projectId]) // Remove fetchTodos from dependencies

  return {
    todos,
    isLoading,
    error,
    refetch: () => fetchTodos(featureId, elementId, projectId),
  }
}
