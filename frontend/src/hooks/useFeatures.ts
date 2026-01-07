import { useEffect, useRef } from 'react'
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
  }, [projectId]) // Remove fetchFeatures from dependencies

  return {
    features,
    isLoading,
    error,
    refetch: () => fetchFeatures(projectId),
  }
}
