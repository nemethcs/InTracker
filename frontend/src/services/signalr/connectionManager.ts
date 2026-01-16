/**
 * Connection management for SignalR service
 */

import { HubConnection, HubConnectionBuilder, LogLevel } from '@microsoft/signalr'
import { isTokenExpired, refreshAccessToken, getCurrentToken } from './tokenManager'
import type { EventManager } from './eventManager'
import type { ProjectGroupsManager } from './projectGroups'

export class ConnectionManager {
  private connection: HubConnection | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null
  private isConnecting = false
  private tokenRefreshInterval: NodeJS.Timeout | null = null
  private lastUsedToken: string | null = null

  constructor(
    private eventManager: EventManager,
    private projectGroupsManager: ProjectGroupsManager
  ) {}

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
      let currentToken = getCurrentToken(token)
      
      // Check if token is expired, if so, refresh it
      if (currentToken && isTokenExpired(currentToken)) {
        console.log('Token expired, refreshing...')
        const newToken = await refreshAccessToken()
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
      this.eventManager.setupEventHandlers(this.connection)

      // Update project groups manager with new connection
      this.projectGroupsManager.updateConnection(this.connection)

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
        this.eventManager.emit('reconnected', { connectionId })
      })

      // Start connection
      await this.connection.start()
      this.isConnecting = false
      this.reconnectAttempts = 0
      this.reconnectDelay = 1000
      
      // Start token refresh monitor
      this.startTokenRefreshMonitor()
      
      // Emit connected event so components can join project groups
      this.eventManager.emit('connected', { connectionId: this.connection.connectionId })
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

    this.eventManager.clear()
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

  /**
   * Get connection instance
   */
  getConnection(): HubConnection | null {
    return this.connection
  }
}
