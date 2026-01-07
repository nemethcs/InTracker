import { useEffect, useRef, useCallback } from 'react'
import { useFeatureStore } from '@/stores/featureStore'

export function useFeatures(projectId?: string) {
  const {
    features,
    isLoading,
    error,
    fetchFeatures,
  } = useFeatureStore()

  const lastProjectId = useRef<string | undefined>(undefined)

  useEffect(() => {
    // Only fetch if projectId changed
    if (projectId !== lastProjectId.current) {
      lastProjectId.current = projectId
      if (projectId) {
        fetchFeatures(projectId)
      }
    }
  }, [projectId, fetchFeatures])

  // Use useCallback to create a stable refetch function
  const refetch = useCallback(() => {
    if (projectId) {
      fetchFeatures(projectId)
    }
  }, [projectId, fetchFeatures])

  return {
    features,
    isLoading,
    error,
    refetch,
  }
}
