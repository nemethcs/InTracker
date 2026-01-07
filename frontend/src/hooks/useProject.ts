import { useEffect, useRef } from 'react'
import { useProjectStore } from '@/stores/projectStore'

export function useProject(projectId?: string) {
  const {
    projects,
    currentProject,
    isLoading,
    error,
    fetchProjects,
    fetchProject,
    setCurrentProject,
  } = useProjectStore()

  const lastProjectId = useRef<string | undefined>(undefined)

  useEffect(() => {
    // Only fetch if projectId changed
    if (projectId !== lastProjectId.current) {
      lastProjectId.current = projectId
      if (projectId) {
        fetchProject(projectId)
      } else {
        fetchProjects()
      }
    }
  }, [projectId]) // Remove fetchProject and fetchProjects from dependencies

  return {
    projects,
    currentProject: projectId ? currentProject : undefined,
    isLoading,
    error,
    refetch: projectId ? () => fetchProject(projectId) : fetchProjects,
    setCurrentProject,
  }
}
