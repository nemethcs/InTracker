import { useEffect, useRef, useCallback } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { useFeatureStore } from '@/stores/featureStore'

export function useFeatures(projectId?: string, sort: string = 'updated_at_desc') {
  const {
    features,
    isLoading,
    error,
    fetchFeatures,
  } = useFeatureStore(
    useShallow((state) => ({
      features: state.features,
      isLoading: state.isLoading,
      error: state.error,
      fetchFeatures: state.fetchFeatures,
    }))
  )

  const lastProjectId = useRef<string | undefined>(undefined)
  const lastSort = useRef<string | undefined>(undefined)

  useEffect(() => {
    // Only fetch if projectId or sort changed
    if (projectId !== lastProjectId.current || sort !== lastSort.current) {
      lastProjectId.current = projectId
      lastSort.current = sort
      if (projectId) {
        fetchFeatures(projectId, sort)
      }
    }
  }, [projectId, sort, fetchFeatures])

  // Use useCallback to create a stable refetch function
  const refetch = useCallback(() => {
    if (projectId) {
      fetchFeatures(projectId, sort)
    }
  }, [projectId, sort, fetchFeatures])

  return {
    features,
    isLoading,
    error,
    refetch,
  }
}
