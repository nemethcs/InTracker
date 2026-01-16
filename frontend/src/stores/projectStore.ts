import { create } from 'zustand'
import { projectService, type Project, type ProjectCreate, type ProjectUpdate } from '@/services/projectService'
import { signalrService } from '@/services/signalrService'
import type { ProjectUpdateData } from '@/types/signalr'

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

export const useProjectStore = create<ProjectState>((set, get) => {
  // Subscribe to SignalR project updates
  signalrService.on('projectUpdated', (data: ProjectUpdateData) => {
    const { projects, currentProject } = get()
    
    // Handle different update actions
    if (data.changes?.action === 'created') {
      // New project created - fetch it silently if not already in store
      const existingIndex = projects.findIndex(p => p.id === data.projectId)
      if (existingIndex === -1) {
        // Project not in store, fetch it silently (without loading state)
        projectService.getProject(data.projectId).then(project => {
          const { projects } = get()
          if (!projects.find(p => p.id === project.id)) {
            set({ projects: [...projects, project] })
          }
        }).catch(error => {
          console.error('Failed to fetch new project:', error)
        })
      }
    } else if (data.changes?.action === 'deleted') {
      // Project deleted - remove from local state
      set({ 
        projects: projects.filter(p => p.id !== data.projectId),
        currentProject: currentProject?.id === data.projectId ? null : currentProject
      })
    } else {
      // Project updated - update the project in store directly from changes or fetch silently
      const existingIndex = projects.findIndex(p => p.id === data.projectId)
      if (existingIndex >= 0) {
        // Update existing project with changes directly (no API call needed)
        const updatedProjects = [...projects]
        updatedProjects[existingIndex] = {
          ...updatedProjects[existingIndex],
          ...data.changes,
          updated_at: new Date().toISOString() // Update timestamp
        }
        set({ 
          projects: updatedProjects,
          currentProject: currentProject?.id === data.projectId 
            ? { ...currentProject, ...data.changes, updated_at: new Date().toISOString() }
            : currentProject
        })
      } else {
        // Project not in store, fetch it silently (without loading state)
        projectService.getProject(data.projectId).then(project => {
          const { projects } = get()
          const index = projects.findIndex(p => p.id === project.id)
          if (index >= 0) {
            const updatedProjects = [...projects]
            updatedProjects[index] = project
            set({ projects: updatedProjects })
          } else {
            set({ projects: [...projects, project] })
          }
        }).catch(error => {
          console.error('Failed to fetch updated project:', error)
        })
      }
    }
  })

  return {
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
  }
})
