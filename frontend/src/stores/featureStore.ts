import { create } from 'zustand'
import { featureService, type Feature, type FeatureCreate, type FeatureUpdate } from '@/services/featureService'

interface FeatureState {
  features: Feature[]
  isLoading: boolean
  error: string | null
  fetchFeatures: (projectId?: string) => Promise<void>
  fetchFeature: (id: string) => Promise<Feature>
  createFeature: (data: FeatureCreate) => Promise<Feature>
  updateFeature: (id: string, data: FeatureUpdate) => Promise<void>
  deleteFeature: (id: string) => Promise<void>
}

export const useFeatureStore = create<FeatureState>((set) => ({
  features: [],
  isLoading: false,
  error: null,

  fetchFeatures: async (projectId?: string) => {
    set({ isLoading: true, error: null })
    try {
      const features = await featureService.listFeatures(projectId)
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
}))
