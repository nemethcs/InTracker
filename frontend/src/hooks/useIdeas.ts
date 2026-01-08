import { useEffect, useRef, useCallback } from 'react'
import { useIdeaStore } from '@/stores/ideaStore'

export function useIdeas(status?: string, teamId?: string) {
  const {
    ideas,
    isLoading,
    error,
    fetchIdeas,
  } = useIdeaStore()

  const lastStatus = useRef<string | undefined>(undefined)
  const lastTeamId = useRef<string | undefined>(undefined)
  const hasFetched = useRef(false)

  useEffect(() => {
    // Fetch on first load or if status/teamId changed
    if (!hasFetched.current || status !== lastStatus.current || teamId !== lastTeamId.current) {
      lastStatus.current = status
      lastTeamId.current = teamId
      hasFetched.current = true
      fetchIdeas(status, teamId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, teamId]) // fetchIdeas is stable from Zustand store

  const refetch = useCallback(() => {
    hasFetched.current = false
    fetchIdeas(status, teamId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, teamId]) // fetchIdeas is stable from Zustand store

  return {
    ideas,
    isLoading,
    error,
    refetch,
  }
}
