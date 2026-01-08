import { create } from 'zustand'
import { ideaService, type Idea, type IdeaCreate, type IdeaUpdate, type IdeaConvertRequest } from '@/services/ideaService'

interface IdeaState {
  ideas: Idea[]
  isLoading: boolean
  error: string | null
  fetchIdeas: (status?: string, teamId?: string) => Promise<void>
  fetchIdea: (id: string) => Promise<Idea>
  createIdea: (data: IdeaCreate) => Promise<Idea>
  updateIdea: (id: string, data: IdeaUpdate) => Promise<void>
  deleteIdea: (id: string) => Promise<void>
  convertIdeaToProject: (id: string, data: IdeaConvertRequest) => Promise<any>
}

export const useIdeaStore = create<IdeaState>((set, get) => ({
  ideas: [],
  isLoading: false,
  error: null,

  fetchIdeas: async (status?: string, teamId?: string) => {
    // Prevent duplicate requests
    const currentState = get()
    if (currentState.isLoading) {
      return
    }
    set({ isLoading: true, error: null })
    try {
      const ideas = await ideaService.listIdeas(status, teamId)
      set({ ideas, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch ideas:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to fetch ideas', isLoading: false })
    }
  },

  fetchIdea: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const idea = await ideaService.getIdea(id)
      set(state => {
        const index = state.ideas.findIndex(i => i.id === id)
        if (index >= 0) {
          const ideas = [...state.ideas]
          ideas[index] = idea
          return { ideas, isLoading: false }
        }
        return { ideas: [...state.ideas, idea], isLoading: false }
      })
      return idea
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch idea', isLoading: false })
      throw error
    }
  },

  createIdea: async (data: IdeaCreate) => {
    set({ isLoading: true, error: null })
    try {
      const idea = await ideaService.createIdea(data)
      set(state => ({ 
        ideas: [...state.ideas, idea], 
        isLoading: false 
      }))
      return idea
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create idea', isLoading: false })
      throw error
    }
  },

  updateIdea: async (id: string, data: IdeaUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const idea = await ideaService.updateIdea(id, data)
      set(state => ({
        ideas: state.ideas.map(i => i.id === id ? idea : i),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update idea', isLoading: false })
      throw error
    }
  },

  deleteIdea: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await ideaService.deleteIdea(id)
      set(state => ({
        ideas: state.ideas.filter(i => i.id !== id),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete idea', isLoading: false })
      throw error
    }
  },

  convertIdeaToProject: async (id: string, data: IdeaConvertRequest) => {
    set({ isLoading: true, error: null })
    try {
      const project = await ideaService.convertIdeaToProject(id, data)
      set(state => ({
        ideas: state.ideas.map(i => i.id === id ? { ...i, converted_to_project_id: project.id } : i),
        isLoading: false
      }))
      return project
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to convert idea to project', isLoading: false })
      throw error
    }
  },
}))
