import { useEffect } from 'react'
import { useFeatureStore } from '@/stores/featureStore'

export function useFeatures(projectId?: string) {
  const {
    features,
    isLoading,
    error,
    fetchFeatures,
  } = useFeatureStore()

  useEffect(() => {
    fetchFeatures(projectId)
  }, [projectId, fetchFeatures])

  return {
    features,
    isLoading,
    error,
    refetch: () => fetchFeatures(projectId),
  }
}
