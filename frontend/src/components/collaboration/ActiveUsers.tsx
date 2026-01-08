import { useState, useEffect } from 'react'
import { collaborationService, type ActiveUser } from '@/services/collaborationService'
import { signalrService } from '@/services/signalrService'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

interface ActiveUsersProps {
  projectId: string
}

export function ActiveUsers({ projectId }: ActiveUsersProps) {
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!projectId) return

    // Fetch active users function
    const fetchActiveUsers = async () => {
      try {
        const response = await collaborationService.getActiveUsers(projectId)
        setActiveUsers(response.activeUsers)
        setIsLoading(false)
      } catch (error) {
        console.error('Failed to fetch active users:', error)
        setIsLoading(false)
      }
    }

    // Wait a bit for joinProject to complete, then fetch active users
    const initializeActiveUsers = async () => {
      // Wait for SignalR connection and joinProject to complete
      if (signalrService.isConnected()) {
        // Small delay to ensure joinProject has completed
        await new Promise(resolve => setTimeout(resolve, 500))
      } else {
        // If not connected, wait for connection
        const checkConnection = setInterval(() => {
          if (signalrService.isConnected()) {
            clearInterval(checkConnection)
            setTimeout(() => fetchActiveUsers(), 500)
          }
        }, 100)
        
        // Cleanup interval after 5 seconds
        setTimeout(() => clearInterval(checkConnection), 5000)
        return
      }
      
      fetchActiveUsers()
    }

    initializeActiveUsers()

    // Handle user joined/left events (WebSocket connection events)
    const handleUserJoined = (data: { userId: string; projectId: string }) => {
      if (data.projectId === projectId) {
        // Refresh active users list after a short delay
        setTimeout(() => fetchActiveUsers(), 200)
      }
    }

    const handleUserLeft = (data: { userId: string; projectId: string }) => {
      if (data.projectId === projectId) {
        // Remove user from list immediately
        setActiveUsers(prev => prev.filter(user => user.id !== data.userId))
        // Also refresh to ensure consistency
        setTimeout(() => fetchActiveUsers(), 200)
      }
    }

    // Handle session start/end events (MCP session events - these are what define "active users")
    const handleSessionStarted = (data: { userId: string; projectId: string }) => {
      if (data.projectId === projectId) {
        // Refresh active users list when a session starts
        setTimeout(() => fetchActiveUsers(), 200)
      }
    }

    const handleSessionEnded = (data: { userId: string; projectId: string }) => {
      if (data.projectId === projectId) {
        // Remove user from list immediately when session ends
        setActiveUsers(prev => prev.filter(user => user.id !== data.userId))
        // Also refresh to ensure consistency
        setTimeout(() => fetchActiveUsers(), 200)
      }
    }

    // Subscribe to SignalR events
    signalrService.on('userJoined', handleUserJoined)
    signalrService.on('userLeft', handleUserLeft)
    signalrService.on('sessionStarted', handleSessionStarted)
    signalrService.on('sessionEnded', handleSessionEnded)

    // Listen for joinedProject confirmation to refresh
    const handleJoinedProject = (data: { projectId: string }) => {
      if (data.projectId === projectId) {
        // Refresh active users after joining
        setTimeout(() => fetchActiveUsers(), 300)
      }
    }

    signalrService.on('joinedProject', handleJoinedProject)

    // Cleanup
    return () => {
      signalrService.off('userJoined', handleUserJoined)
      signalrService.off('userLeft', handleUserLeft)
      signalrService.off('sessionStarted', handleSessionStarted)
      signalrService.off('sessionEnded', handleSessionEnded)
      signalrService.off('joinedProject', handleJoinedProject)
    }
  }, [projectId])

  // Very small, unobtrusive display - just a badge with count and avatars
  // Only show if there are active users
  if (isLoading || activeUsers.length === 0) {
    return null // Don't show anything while loading or if no active users
  }

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center -space-x-1.5">
        {activeUsers.slice(0, 3).map((user) => (
          <Avatar key={user.id} className="h-5 w-5 border-2 border-background">
            <AvatarImage src={user.avatarUrl || undefined} alt={user.name || user.email} />
            <AvatarFallback className="text-[10px]">
              {user.name
                ? user.name
                    .split(' ')
                    .map(n => n[0])
                    .join('')
                    .toUpperCase()
                    .slice(0, 2)
                : user.email[0].toUpperCase()}
            </AvatarFallback>
          </Avatar>
        ))}
        {activeUsers.length > 3 && (
          <div className="h-5 w-5 rounded-full bg-muted border-2 border-background flex items-center justify-center text-[10px] font-medium">
            +{activeUsers.length - 3}
          </div>
        )}
      </div>
      <span className="text-xs text-muted-foreground">
        {activeUsers.length} {activeUsers.length === 1 ? 'working' : 'working'}
      </span>
    </div>
  )
}
