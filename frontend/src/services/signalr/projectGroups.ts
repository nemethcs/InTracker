/**
 * Project group management for SignalR
 */

import type { HubConnection } from '@microsoft/signalr'

export class ProjectGroupsManager {
  constructor(private connection: HubConnection | null) {}

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
   * Update connection reference
   */
  updateConnection(connection: HubConnection | null): void {
    this.connection = connection
  }
}
