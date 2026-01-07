import { HubConnection, HubConnectionBuilder, LogLevel } from '@microsoft/signalr'

export interface SignalREvents {
  todoUpdated: (data: { todoId: string; projectId: string; userId: string; changes: any }) => void
  featureUpdated: (data: { featureId: string; projectId: string; progress: number }) => void
  userActivity: (data: { userId: string; projectId: string; action: string; featureId?: string }) => void
  projectUpdated: (data: { projectId: string; changes: any }) => void
}

class SignalRService {
  private connection: HubConnection | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null
  private isConnecting = false
  private eventHandlers: Map<string, Set<Function>> = new Map()

  /**
   * Initialize SignalR connection
   */
  async connect(token?: string): Promise<void> {
    if (this.isConnecting || (this.connection && this.connection.state === 'Connected')) {
      return
    }

    this.isConnecting = true

    try {
      const signalrUrl = import.meta.env.VITE_SIGNALR_URL || 'http://localhost:3000/hub'
      
      // Build URL with token as query parameter
      const urlWithToken = token 
        ? `${signalrUrl}?access_token=${encodeURIComponent(token)}`
        : signalrUrl
      
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
        console.log('SignalR connection closed', error)
        this.isConnecting = false
        if (error) {
          this.attemptReconnect(token)
        }
      })

      this.connection.onreconnecting((error) => {
        console.log('SignalR reconnecting...', error)
      })

      this.connection.onreconnected((connectionId) => {
        console.log('SignalR reconnected', connectionId)
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
      })

      // Start connection
      await this.connection.start()
      console.log('SignalR connected', this.connection.connectionId)
      this.isConnecting = false
      this.reconnectAttempts = 0
      this.reconnectDelay = 1000
    } catch (error) {
      console.error('SignalR connection failed:', error)
      this.isConnecting = false
      this.attemptReconnect(token)
      throw error
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(token?: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      this.connect(token).catch((error) => {
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

    // Todo updates
    this.connection.on('todoUpdated', (data) => {
      this.emit('todoUpdated', data)
    })

    // Feature updates
    this.connection.on('featureUpdated', (data) => {
      this.emit('featureUpdated', data)
    })

    // User activity
    this.connection.on('userActivity', (data) => {
      this.emit('userActivity', data)
    })

    // Project updates
    this.connection.on('projectUpdated', (data) => {
      this.emit('projectUpdated', data)
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
        console.log(`Joined project group: ${projectId}`)
      } catch (error) {
        // Fallback to simple JSON message
        try {
          await this.connection.send({
            type: 'joinProject',
            projectId: projectId
          })
          console.log(`Joined project group (fallback): ${projectId}`)
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
        console.log(`Left project group: ${projectId}`)
      } catch (error) {
        // Fallback to simple JSON message
        try {
          await this.connection.send({
            type: 'leaveProject',
            projectId: projectId
          })
          console.log(`Left project group (fallback): ${projectId}`)
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

    if (this.connection) {
      try {
        await this.connection.stop()
        console.log('SignalR disconnected')
      } catch (error) {
        console.error('Error disconnecting SignalR:', error)
      }
      this.connection = null
    }

    this.eventHandlers.clear()
    this.isConnecting = false
    this.reconnectAttempts = 0
    this.reconnectDelay = 1000
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
