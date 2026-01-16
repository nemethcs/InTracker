/**
 * Event management for SignalR service
 */

import type {
  TodoUpdateData,
  FeatureUpdateData,
  ProjectUpdateData,
  IdeaUpdateData,
  UserActivityData,
  UserJoinedData,
  UserLeftData,
  JoinedProjectData,
  LeftProjectData,
  SessionStartedData,
  SessionEndedData,
  ConnectedData,
  ReconnectedData,
  McpVerifiedData,
} from '@/types/signalr'

export interface SignalREvents {
  todoUpdated: (data: TodoUpdateData) => void
  featureUpdated: (data: FeatureUpdateData) => void
  userActivity: (data: UserActivityData) => void
  projectUpdated: (data: ProjectUpdateData) => void
  ideaUpdated: (data: IdeaUpdateData) => void
  userJoined: (data: UserJoinedData) => void
  userLeft: (data: UserLeftData) => void
  joinedProject: (data: JoinedProjectData) => void
  leftProject: (data: LeftProjectData) => void
  sessionStarted: (data: SessionStartedData) => void
  sessionEnded: (data: SessionEndedData) => void
  connected: (data: ConnectedData) => void
  reconnected: (data: ReconnectedData) => void
  mcpVerified: (data: McpVerifiedData) => void
}

export class EventManager {
  private eventHandlers: Map<string, Set<Function>> = new Map()

  /**
   * Helper function to extract event data from SignalR message format
   */
  private extractEventData<T>(data: unknown): T {
    // SignalR sends data in arguments array, extract first element
    if (Array.isArray(data)) {
      return data[0] as T
    }
    if (data && typeof data === 'object' && 'arguments' in data) {
      const args = (data as { arguments?: unknown[] }).arguments
      return (args?.[0] || data) as T
    }
    return data as T
  }

  /**
   * Set up event handlers for SignalR connection
   */
  setupEventHandlers(connection: any): void {
    if (!connection) return

    // Todo updates
    connection.on('todoUpdated', (data: unknown) => {
      const eventData = this.extractEventData<TodoUpdateData>(data)
      this.emit('todoUpdated', eventData)
    })

    // Feature updates
    connection.on('featureUpdated', (data: unknown) => {
      const eventData = this.extractEventData<FeatureUpdateData>(data)
      this.emit('featureUpdated', eventData)
    })

    // User activity
    connection.on('userActivity', (data: unknown) => {
      const eventData = this.extractEventData<UserActivityData>(data)
      this.emit('userActivity', eventData)
    })

    // Project updates
    connection.on('projectUpdated', (data: unknown) => {
      const eventData = this.extractEventData<ProjectUpdateData>(data)
      this.emit('projectUpdated', eventData)
    })

    // User joined/left
    connection.on('userJoined', (data: unknown) => {
      const eventData = this.extractEventData<UserJoinedData>(data)
      this.emit('userJoined', eventData)
    })

    connection.on('userLeft', (data: unknown) => {
      const eventData = this.extractEventData<UserLeftData>(data)
      this.emit('userLeft', eventData)
    })

    // Project join/leave confirmations
    connection.on('joinedProject', (data: unknown) => {
      const eventData = this.extractEventData<JoinedProjectData>(data)
      this.emit('joinedProject', eventData)
    })

    connection.on('leftProject', (data: unknown) => {
      const eventData = this.extractEventData<LeftProjectData>(data)
      this.emit('leftProject', eventData)
    })

    // Session start/end events
    connection.on('sessionStarted', (data: unknown) => {
      const eventData = this.extractEventData<SessionStartedData>(data)
      this.emit('sessionStarted', eventData)
    })

    connection.on('sessionEnded', (data: unknown) => {
      const eventData = this.extractEventData<SessionEndedData>(data)
      this.emit('sessionEnded', eventData)
    })

    // Idea updates
    connection.on('ideaUpdated', (data: unknown) => {
      const eventData = this.extractEventData<IdeaUpdateData>(data)
      this.emit('ideaUpdated', eventData)
    })

    // MCP verification (onboarding)
    connection.on('mcpVerified', (data: unknown) => {
      const eventData = this.extractEventData<McpVerifiedData>(data)
      this.emit('mcpVerified', eventData)
    })
  }

  /**
   * Emit event to all registered handlers
   */
  emit<T extends keyof SignalREvents>(eventName: T, data: Parameters<SignalREvents[T]>[0]): void {
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
   * Clear all event handlers
   */
  clear(): void {
    this.eventHandlers.clear()
  }
}
