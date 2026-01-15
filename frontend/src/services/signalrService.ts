import { HubConnection, HubConnectionBuilder, LogLevel } from '@microsoft/signalr'

export interface SignalREvents {
  todoUpdated: (data: { todoId: string; projectId: string; userId: string; changes: any }) => void
  featureUpdated: (data: { featureId: string; projectId: string; progress: number; status?: string }) => void
  userActivity: (data: { userId: string; projectId: string; action: string; featureId?: string }) => void
  projectUpdated: (data: { projectId: string; changes: any }) => void
  ideaUpdated: (data: { ideaId: string; teamId: string; changes: any }) => void
  userJoined: (data: { userId: string; projectId: string }) => void
  userLeft: (data: { userId: string; projectId: string }) => void
  joinedProject: (data: { projectId: string }) => void
  leftProject: (data: { projectId: string }) => void
  sessionStarted: (data: { userId: string; projectId: string }) => void
  sessionEnded: (data: { userId: string; projectId: string }) => void
  connected: (data: { connectionId: string | null }) => void
  reconnected: (data: { connectionId: string | null }) => void
}

class SignalRService {
  private connection: HubConnection | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null
  private isConnecting = false
  private eventHandlers: Map<string, Set<Function>> = new Map()
  private tokenRefreshInterval: NodeJS.Timeout | null = null
  private lastUsedToken: string | null = null

  /**
   * Check if token is expired or about to expire
   */
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expiresAt = payload.exp * 1000 // Convert to milliseconds
      const now = Date.now()
      // Consider token expired if it expires within 1 minute
      return expiresAt - now < 60000
    } catch {
      return true // If we can't parse, consider it expired
    }
  }

  /**
   * Refresh access token using refresh token
   */
  private async refreshAccessToken(): Promise<string | null> {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        return null
      }

      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) {
        return null
      }

      const data = await response.json()
      const { access_token, refresh_token: newRefreshToken } = data.tokens

      localStorage.setItem('access_token', access_token)
      if (newRefreshToken) {
        localStorage.setItem('refresh_token', newRefreshToken)
      }

      return access_token
    } catch (error) {
      console.error('Failed to refresh token:', error)
      return null
    }
  }

  /**
   * Initialize SignalR connection
   */
  async connect(token?: string): Promise<void> {
    if (this.isConnecting || (this.connection && this.connection.state === 'Connected')) {
      return
    }

    this.isConnecting = true

    try {
      // Get current token from localStorage or parameter
      let currentToken = token || localStorage.getItem('access_token') || ''
      
      // Check if token is expired, if so, refresh it
      if (currentToken && this.isTokenExpired(currentToken)) {
        console.log('Token expired, refreshing...')
        const newToken = await this.refreshAccessToken()
        if (newToken) {
          currentToken = newToken
        } else {
          // If refresh failed, try to continue with existing token
          console.warn('Token refresh failed, attempting connection with existing token')
        }
      }
      
      this.lastUsedToken = currentToken
      
      const signalrUrl = import.meta.env.VITE_SIGNALR_URL || 'http://localhost:3000/signalr/hub'
      
      // Build URL with token as query parameter
      const urlWithToken = currentToken 
        ? `${signalrUrl}?access_token=${encodeURIComponent(currentToken)}`
        : signalrUrl
      
      // Connect to SignalR hub
      
      const builder = new HubConnectionBuilder()
        .withUrl(urlWithToken, {
          // Use WebSocket transport directly (backend uses WebSocket, not SignalR protocol)
          skipNegotiation: true, // Skip SignalR negotiation, connect directly via WebSocket
          transport: 1, // WebSockets only
        })
        .withAutomaticReconnect({
          nextRetryDelayInMilliseconds: (retryContext) => {
            // Exponential backoff: 1s, 2s, 4s, 8s, 16s
            const delay = Math.min(1000 * Math.pow(2, retryContext.previousRetryCount), 16000)
            return delay
          },
        })
        .configureLogging(import.meta.env.DEV ? LogLevel.Information : LogLevel.Warning)

      this.connection = builder.build()

      // Set up event handlers
      this.setupEventHandlers()

      // Connection state handlers
      this.connection.onclose((error) => {
        this.isConnecting = false
        // Stop token refresh monitor
        if (this.tokenRefreshInterval) {
          clearInterval(this.tokenRefreshInterval)
          this.tokenRefreshInterval = null
        }
        if (error) {
          this.attemptReconnect()
        }
      })

      this.connection.onreconnecting(() => {
        // Reconnecting...
      })

      this.connection.onreconnected((connectionId) => {
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
        // Emit reconnected event so components can rejoin project groups
        this.emit('reconnected', { connectionId })
      })

      // Start connection
      await this.connection.start()
      this.isConnecting = false
      this.reconnectAttempts = 0
      this.reconnectDelay = 1000
      
      // Start token refresh monitor
      this.startTokenRefreshMonitor()
      
      // Emit connected event so components can join project groups
      this.emit('connected', { connectionId: this.connection.connectionId })
    } catch (error) {
      console.error('SignalR connection failed:', error)
      this.isConnecting = false
      this.attemptReconnect()
      throw error
    }
  }

  /**
   * Monitor token changes and reconnect if token is refreshed
   */
  private startTokenRefreshMonitor(): void {
    // Clear existing interval
    if (this.tokenRefreshInterval) {
      clearInterval(this.tokenRefreshInterval)
    }

    // Check every 5 seconds if token has changed
    this.tokenRefreshInterval = setInterval(async () => {
      const currentToken = localStorage.getItem('access_token')
      
      // If token has changed, reconnect with new token
      if (currentToken && currentToken !== this.lastUsedToken) {
        console.log('Token refreshed, reconnecting SignalR...')
        this.lastUsedToken = currentToken
        
        // Disconnect and reconnect with new token
        try {
          await this.disconnect()
          await this.connect(currentToken)
        } catch (error) {
          console.error('Failed to reconnect with new token:', error)
        }
      }
    }, 5000) // Check every 5 seconds
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      // Always use the latest token from localStorage
      const currentToken = localStorage.getItem('access_token') || undefined
      this.connect(currentToken).catch((error) => {
        console.error('Reconnection failed:', error)
      })
    }, this.reconnectDelay)

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000) // Max 30 seconds
  }

  /**
   * Set up event handlers for SignalR events
   */
  private setupEventHandlers(): void {
    if (!this.connection) return

    // Todo updates - SignalR sends as {type: 1, target: "todoUpdated", arguments: [data]}
    this.connection.on('todoUpdated', (data: any) => {
      // SignalR sends data in arguments array, extract first element
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('todoUpdated', eventData)
    })

    // Feature updates
    this.connection.on('featureUpdated', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('featureUpdated', eventData)
    })

    // User activity
    this.connection.on('userActivity', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('userActivity', eventData)
    })

    // Project updates
    this.connection.on('projectUpdated', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('projectUpdated', eventData)
    })

    // User joined/left
    this.connection.on('userJoined', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('userJoined', eventData)
    })

    this.connection.on('userLeft', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('userLeft', eventData)
    })

    // Project join/leave confirmations
    this.connection.on('joinedProject', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('joinedProject', eventData)
    })

    this.connection.on('leftProject', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('leftProject', eventData)
    })

    // Session start/end events
    this.connection.on('sessionStarted', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('sessionStarted', eventData)
    })

    this.connection.on('sessionEnded', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('sessionEnded', eventData)
    })

    // Idea updates
    this.connection.on('ideaUpdated', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('ideaUpdated', eventData)
    })

    // MCP verification (onboarding)
    this.connection.on('mcpVerified', (data: any) => {
      const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
      this.emit('mcpVerified', eventData)
    })
  }

  /**
   * Emit event to all registered handlers
   */
  private emit(eventName: string, data: any): void {
    const handlers = this.eventHandlers.get(eventName)
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data)
        } catch (error) {
          console.error(`Error in SignalR event handler for ${eventName}:`, error)
        }
      })
    }
  }

  /**
   * Subscribe to a SignalR event
   */
  on<K extends keyof SignalREvents>(eventName: K, handler: SignalREvents[K]): void {
    if (!this.eventHandlers.has(eventName)) {
      this.eventHandlers.set(eventName, new Set())
    }
    this.eventHandlers.get(eventName)!.add(handler)
  }

  /**
   * Unsubscribe from a SignalR event
   */
  off<K extends keyof SignalREvents>(eventName: K, handler: SignalREvents[K]): void {
    const handlers = this.eventHandlers.get(eventName)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  /**
   * Join a project group for real-time updates
   */
  async joinProject(projectId: string): Promise<void> {
    if (this.connection && this.connection.state === 'Connected') {
      try {
        // Try SignalR invoke first
        await this.connection.invoke('JoinProject', projectId)
      } catch (error) {
        // Fallback to simple JSON message
        try {
          await this.connection.send({
            type: 'joinProject',
            projectId: projectId
          })
        } catch (fallbackError) {
          console.error('Failed to join project group:', fallbackError)
        }
      }
    }
  }

  /**
   * Leave a project group
   */
  async leaveProject(projectId: string): Promise<void> {
    if (this.connection && this.connection.state === 'Connected') {
      try {
        // Try SignalR invoke first
        await this.connection.invoke('LeaveProject', projectId)
      } catch (error) {
        // Fallback to simple JSON message
        try {
          await this.connection.send({
            type: 'leaveProject',
            projectId: projectId
          })
        } catch (fallbackError) {
          console.error('Failed to leave project group:', fallbackError)
        }
      }
    }
  }

  /**
   * Send user activity notification
   */
  async sendUserActivity(projectId: string, action: string, featureId?: string): Promise<void> {
    if (this.connection && this.connection.state === 'Connected') {
      try {
        // Try SignalR invoke first
        await this.connection.invoke('SendUserActivity', projectId, action, featureId)
      } catch (error) {
        // Fallback to simple JSON message
        try {
          await this.connection.send({
            type: 'userActivity',
            projectId: projectId,
            action: action,
            featureId: featureId
          })
        } catch (fallbackError) {
          console.error('Failed to send user activity:', fallbackError)
        }
      }
    }
  }

  /**
   * Disconnect from SignalR hub
   */
  async disconnect(): Promise<void> {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.tokenRefreshInterval) {
      clearInterval(this.tokenRefreshInterval)
      this.tokenRefreshInterval = null
    }

    if (this.connection) {
      try {
        await this.connection.stop()
        // SignalR disconnected
      } catch (error) {
        console.error('Error disconnecting SignalR:', error)
      }
      this.connection = null
    }

    this.eventHandlers.clear()
    this.isConnecting = false
    this.reconnectAttempts = 0
    this.reconnectDelay = 1000
    this.lastUsedToken = null
  }

  /**
   * Get connection state
   */
  getState(): string {
    return this.connection?.state || 'Disconnected'
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connection?.state === 'Connected'
  }
}

// Export singleton instance
export const signalrService = new SignalRService()
