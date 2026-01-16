/**
 * Type definitions for SignalR events
 */

export interface TodoUpdateData {
  todoId: string
  projectId: string
  userId: string
  changes: {
    status?: 'new' | 'in_progress' | 'done'
    title?: string
    description?: string
    priority?: 'low' | 'medium' | 'high' | 'critical'
    assigned_to?: string
    version?: number
    [key: string]: unknown
  }
}

export interface FeatureUpdateData {
  featureId: string
  projectId: string
  progress: number
  status?: 'new' | 'in_progress' | 'done' | 'tested' | 'merged'
}

export interface ProjectUpdateData {
  projectId: string
  changes: {
    name?: string
    description?: string
    status?: 'active' | 'paused' | 'blocked' | 'completed' | 'archived'
    tags?: string[]
    technology_tags?: string[]
    cursor_instructions?: string
    resume_context?: ProjectResumeContext
    [key: string]: unknown
  }
}

export interface IdeaUpdateData {
  ideaId: string
  teamId: string
  changes: {
    title?: string
    description?: string
    status?: 'draft' | 'active' | 'archived'
    tags?: string[]
    converted_to_project_id?: string
    [key: string]: unknown
  }
}

export interface UserActivityData {
  userId: string
  projectId: string
  action: string
  featureId?: string
}

export interface UserJoinedData {
  userId: string
  projectId: string
}

export interface UserLeftData {
  userId: string
  projectId: string
}

export interface JoinedProjectData {
  projectId: string
}

export interface LeftProjectData {
  projectId: string
}

export interface SessionStartedData {
  userId: string
  projectId: string
}

export interface SessionEndedData {
  userId: string
  projectId: string
}

export interface ConnectedData {
  connectionId: string | null
}

export interface ReconnectedData {
  connectionId: string | null
}

export interface McpVerifiedData {
  userId: string
  verifiedAt: string
}
