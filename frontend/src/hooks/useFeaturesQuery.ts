import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { featureService, type Feature, type FeatureCreate, type FeatureUpdate } from '@/services/featureService'

// Query keys for React Query
export const featureKeys = {
  all: ['features'] as const,
  lists: () => [...featureKeys.all, 'list'] as const,
  list: (projectId?: string, sort?: string) => [...featureKeys.lists(), projectId, sort] as const,
  details: () => [...featureKeys.all, 'detail'] as const,
  detail: (id: string) => [...featureKeys.details(), id] as const,
}

/**
 * Hook to fetch features for a project
 */
export function useFeaturesQuery(projectId?: string, sort: string = 'updated_at_desc') {
  return useQuery({
    queryKey: featureKeys.list(projectId, sort),
    queryFn: () => featureService.listFeatures(projectId, sort),
    enabled: !!projectId, // Only fetch if projectId is provided
    staleTime: 1000 * 60 * 2, // 2 minutes - features are fresh for 2 minutes
  })
}

/**
 * Hook to fetch a single feature
 */
export function useFeatureQuery(featureId: string) {
  return useQuery({
    queryKey: featureKeys.detail(featureId),
    queryFn: () => featureService.getFeature(featureId),
    enabled: !!featureId,
  })
}

/**
 * Hook to create a feature
 */
export function useCreateFeature() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: FeatureCreate) => featureService.createFeature(data),
    onSuccess: (newFeature) => {
      // Invalidate and refetch features list for the project
      queryClient.invalidateQueries({ queryKey: featureKeys.lists() })
      // Optionally, set the new feature in cache
      queryClient.setQueryData(featureKeys.detail(newFeature.id), newFeature)
    },
  })
}

/**
 * Hook to update a feature
 */
export function useUpdateFeature() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FeatureUpdate }) =>
      featureService.updateFeature(id, data),
    onSuccess: (updatedFeature) => {
      // Update the feature in cache
      queryClient.setQueryData(featureKeys.detail(updatedFeature.id), updatedFeature)
      // Invalidate features list to ensure consistency
      queryClient.invalidateQueries({ queryKey: featureKeys.lists() })
    },
  })
}

/**
 * Hook to delete a feature
 */
export function useDeleteFeature() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => featureService.deleteFeature(id),
    onSuccess: (_, deletedId) => {
      // Remove the feature from cache
      queryClient.removeQueries({ queryKey: featureKeys.detail(deletedId) })
      // Invalidate features list
      queryClient.invalidateQueries({ queryKey: featureKeys.lists() })
    },
  })
}
