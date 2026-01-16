/**
 * SignalR service for real-time communication
 * 
 * This service is a facade that coordinates the various SignalR modules:
 * - ConnectionManager: Handles connection lifecycle
 * - EventManager: Manages event subscriptions and emissions
 * - ProjectGroupsManager: Handles project group operations
 * - TokenManager: Manages token refresh
 */

import { ConnectionManager } from './signalr/connectionManager'
import { EventManager } from './signalr/eventManager'
import { ProjectGroupsManager } from './signalr/projectGroups'
import type { SignalREvents } from './signalr/eventManager'

class SignalRService {
  private connectionManager: ConnectionManager
  private eventManager: EventManager
  private projectGroupsManager: ProjectGroupsManager

  constructor() {
    this.eventManager = new EventManager()
    this.projectGroupsManager = new ProjectGroupsManager(null)
    this.connectionManager = new ConnectionManager(this.eventManager, this.projectGroupsManager)
  }

  /**
   * Connect to SignalR hub
   */
  async connect(token?: string): Promise<void> {
    await this.connectionManager.connect(token)
  }

  /**
   * Disconnect from SignalR hub
   */
  async disconnect(): Promise<void> {
    await this.connectionManager.disconnect()
  }

  /**
   * Subscribe to a SignalR event
   */
  on<K extends keyof SignalREvents>(eventName: K, handler: SignalREvents[K]): void {
    this.eventManager.on(eventName, handler)
  }

  /**
   * Unsubscribe from a SignalR event
   */
  off<K extends keyof SignalREvents>(eventName: K, handler: SignalREvents[K]): void {
    this.eventManager.off(eventName, handler)
  }

  /**
   * Join a project group for real-time updates
   */
  async joinProject(projectId: string): Promise<void> {
    await this.projectGroupsManager.joinProject(projectId)
  }

  /**
   * Leave a project group
   */
  async leaveProject(projectId: string): Promise<void> {
    await this.projectGroupsManager.leaveProject(projectId)
  }

  /**
   * Send user activity notification
   */
  async sendUserActivity(projectId: string, action: string, featureId?: string): Promise<void> {
    await this.projectGroupsManager.sendUserActivity(projectId, action, featureId)
  }

  /**
   * Get connection state
   */
  getState(): string {
    return this.connectionManager.getState()
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionManager.isConnected()
  }
}

// Export singleton instance
export const signalrService = new SignalRService()

// Re-export SignalREvents interface for convenience
export type { SignalREvents } from './signalr/eventManager'
