import { create } from 'zustand'
import { featureService, type Feature, type FeatureCreate, type FeatureUpdate } from '@/services/featureService'
import { signalrService } from '@/services/signalrService'

interface FeatureState {
  features: Feature[]
  isLoading: boolean
  error: string | null
  fetchFeatures: (projectId?: string, sort?: string) => Promise<void>
  fetchFeature: (id: string) => Promise<Feature>
  createFeature: (data: FeatureCreate) => Promise<Feature>
  updateFeature: (id: string, data: FeatureUpdate) => Promise<void>
  deleteFeature: (id: string) => Promise<void>
}

export const useFeatureStore = create<FeatureState>((set, get) => {
  // Subscribe to SignalR feature updates
  signalrService.on('featureUpdated', (data: { featureId: string; projectId: string; progress: number; status?: string }) => {
    const { features } = get()
    const featureIndex = features.findIndex(f => f.id === data.featureId)
    
    if (featureIndex >= 0) {
      // Update existing feature with new progress and status
      const updatedFeatures = [...features]
      updatedFeatures[featureIndex] = {
        ...updatedFeatures[featureIndex],
        progress_percentage: data.progress,
        ...(data.status && { status: data.status }),
      }
      set({ features: updatedFeatures })
      
      // Optionally fetch full feature data to ensure we have latest info
      featureService.getFeature(data.featureId).then(feature => {
        const { features } = get()
        const index = features.findIndex(f => f.id === feature.id)
        if (index >= 0) {
          const updatedFeatures = [...features]
          updatedFeatures[index] = feature
          set({ features: updatedFeatures })
        }
      }).catch(() => {
        // Feature might not exist or we don't have access, ignore
      })
    }
  })

  return {
    features: [],
    isLoading: false,
    error: null,

  fetchFeatures: async (projectId?: string, sort: string = 'updated_at_desc') => {
    set({ isLoading: true, error: null })
    try {
      const features = await featureService.listFeatures(projectId, sort)
      set({ features, isLoading: false })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch features', isLoading: false })
    }
  },

  fetchFeature: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const feature = await featureService.getFeature(id)
      set(state => {
        const index = state.features.findIndex(f => f.id === id)
        if (index >= 0) {
          const features = [...state.features]
          features[index] = feature
          return { features, isLoading: false }
        }
        return { features: [...state.features, feature], isLoading: false }
      })
      return feature
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch feature', isLoading: false })
      throw error
    }
  },

  createFeature: async (data: FeatureCreate) => {
    set({ isLoading: true, error: null })
    try {
      const feature = await featureService.createFeature(data)
      set(state => ({ 
        features: [...state.features, feature], 
        isLoading: false 
      }))
      return feature
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create feature', isLoading: false })
      throw error
    }
  },

  updateFeature: async (id: string, data: FeatureUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const feature = await featureService.updateFeature(id, data)
      set(state => ({
        features: state.features.map(f => f.id === id ? feature : f),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update feature', isLoading: false })
      throw error
    }
  },

  deleteFeature: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await featureService.deleteFeature(id)
      set(state => ({
        features: state.features.filter(f => f.id !== id),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete feature', isLoading: false })
      throw error
    }
  },
  }
})
