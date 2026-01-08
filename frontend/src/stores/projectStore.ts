import { create } from 'zustand'
import { projectService, type Project, type ProjectCreate, type ProjectUpdate } from '@/services/projectService'

interface ProjectState {
  projects: Project[]
  currentProject: Project | null
  isLoading: boolean
  error: string | null
  fetchProjects: (teamId?: string, status?: string) => Promise<void>
  fetchProject: (id: string) => Promise<void>
  createProject: (data: ProjectCreate) => Promise<Project>
  updateProject: (id: string, data: ProjectUpdate) => Promise<void>
  deleteProject: (id: string) => Promise<void>
  setCurrentProject: (project: Project | null) => void
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,

  fetchProjects: async (teamId?: string, status?: string) => {
    // Prevent duplicate requests
    const currentState = get()
    if (currentState.isLoading) {
      return
    }
    set({ isLoading: true, error: null })
    try {
      const projects = await projectService.listProjects(teamId, status)
      set({ projects, isLoading: false })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch projects', isLoading: false })
    }
  },

  fetchProject: async (id: string) => {
    // Prevent duplicate requests
    const currentState = get()
    if (currentState.isLoading && currentState.currentProject?.id === id) {
      return
    }
    set({ isLoading: true, error: null })
    try {
      const project = await projectService.getProject(id)
      set({ currentProject: project, isLoading: false })
      // Update in projects list if exists
      const projects = get().projects
      const index = projects.findIndex(p => p.id === id)
      if (index >= 0) {
        projects[index] = project
        set({ projects: [...projects] })
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch project', isLoading: false })
    }
  },

  createProject: async (data: ProjectCreate) => {
    set({ isLoading: true, error: null })
    try {
      const project = await projectService.createProject(data)
      set(state => ({ 
        projects: [...state.projects, project], 
        isLoading: false 
      }))
      return project
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create project', isLoading: false })
      throw error
    }
  },

  updateProject: async (id: string, data: ProjectUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const project = await projectService.updateProject(id, data)
      set(state => ({
        projects: state.projects.map(p => p.id === id ? project : p),
        currentProject: state.currentProject?.id === id ? project : state.currentProject,
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update project', isLoading: false })
      throw error
    }
  },

  deleteProject: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await projectService.deleteProject(id)
      set(state => ({
        projects: state.projects.filter(p => p.id !== id),
        currentProject: state.currentProject?.id === id ? null : state.currentProject,
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete project', isLoading: false })
      throw error
    }
  },

  setCurrentProject: (project: Project | null) => {
    set({ currentProject: project })
  },
}))
