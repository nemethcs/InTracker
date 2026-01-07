import { useState, useEffect } from 'react'
import { collaborationService, type ActiveUser } from '@/services/collaborationService'
import { signalrService } from '@/services/signalrService'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Users } from 'lucide-react'

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

    // Handle user joined/left events
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

    // Subscribe to SignalR events
    signalrService.on('userJoined', handleUserJoined)
    signalrService.on('userLeft', handleUserLeft)

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
      signalrService.off('joinedProject', handleJoinedProject)
    }
  }, [projectId])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Active Users
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          Active Users
        </CardTitle>
        <CardDescription>
          {activeUsers.length} {activeUsers.length === 1 ? 'user' : 'users'} currently viewing this project
        </CardDescription>
      </CardHeader>
      <CardContent>
        {activeUsers.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active users</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {activeUsers.map((user) => (
              <div key={user.id} className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.avatarUrl || undefined} alt={user.name || user.email} />
                  <AvatarFallback>
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
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{user.name || user.email}</span>
                  {user.name && <span className="text-xs text-muted-foreground">{user.email}</span>}
                </div>
                <Badge variant="outline" className="ml-1">
                  Online
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
