import { useEffect, useRef } from 'react'
import { useIdeaStore } from '@/stores/ideaStore'

export function useIdeas(status?: string) {
  const {
    ideas,
    isLoading,
    error,
    fetchIdeas,
  } = useIdeaStore()

  const lastStatus = useRef<string | undefined>(undefined)
  const hasFetched = useRef(false)

  useEffect(() => {
    // Fetch on first load or if status changed
    if (!hasFetched.current || status !== lastStatus.current) {
      lastStatus.current = status
      hasFetched.current = true
      fetchIdeas(status)
    }
  }, [status]) // Remove fetchIdeas from dependencies to avoid infinite loop

  return {
    ideas,
    isLoading,
    error,
    refetch: () => {
      hasFetched.current = false
      fetchIdeas(status)
    },
  }
}
