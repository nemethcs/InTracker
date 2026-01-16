import { useEffect, useRef, useCallback } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { useProjectStore } from '@/stores/projectStore'

export function useProject(projectId?: string, teamId?: string, status?: string) {
  const {
    projects,
    currentProject,
    isLoading,
    error,
    fetchProjects,
    fetchProject,
    setCurrentProject,
  } = useProjectStore(
    useShallow((state) => ({
      projects: state.projects,
      currentProject: state.currentProject,
      isLoading: state.isLoading,
      error: state.error,
      fetchProjects: state.fetchProjects,
      fetchProject: state.fetchProject,
      setCurrentProject: state.setCurrentProject,
    }))
  )

  const lastProjectId = useRef<string | undefined>(undefined)
  const lastTeamId = useRef<string | undefined>(undefined)
  const lastStatus = useRef<string | undefined>(undefined)
  const hasFetched = useRef(false)

  useEffect(() => {
    // Only fetch if projectId, teamId, or status changed, or on first load
    if (!hasFetched.current || projectId !== lastProjectId.current || teamId !== lastTeamId.current || status !== lastStatus.current) {
      lastProjectId.current = projectId
      lastTeamId.current = teamId
      lastStatus.current = status
      hasFetched.current = true
      if (projectId) {
        fetchProject(projectId)
      } else {
        fetchProjects(teamId, status)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, teamId, status]) // fetchProject and fetchProjects are stable from Zustand store

  const refetch = useCallback(() => {
    hasFetched.current = false
    if (projectId) {
      fetchProject(projectId)
    } else {
      fetchProjects(teamId, status)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, teamId, status]) // fetchProject and fetchProjects are stable from Zustand store

  return {
    projects,
    currentProject: projectId ? currentProject : undefined,
    isLoading,
    error,
    refetch,
    setCurrentProject,
  }
}
