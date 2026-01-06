import { useEffect } from 'react'
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

  useEffect(() => {
    if (projectId) {
      fetchProject(projectId)
    } else {
      fetchProjects()
    }
  }, [projectId, fetchProject, fetchProjects])

  return {
    projects,
    currentProject: projectId ? currentProject : undefined,
    isLoading,
    error,
    refetch: projectId ? () => fetchProject(projectId) : fetchProjects,
    setCurrentProject,
  }
}
