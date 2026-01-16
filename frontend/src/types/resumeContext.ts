/**
 * Type definitions for project resume context
 */

export interface ResumeContextTodo {
  id?: string
  title: string
  status?: 'new' | 'in_progress' | 'done'
}

export interface ResumeContextLast {
  session_summary?: string
  [key: string]: unknown
}

export interface ResumeContextNow {
  next_todos?: ResumeContextTodo[]
  immediate_goals?: string[]
  [key: string]: unknown
}

export interface ProjectResumeContext {
  last?: string | ResumeContextLast
  now?: string | ResumeContextNow
  next?: string
  next_blockers?: string[]
  blockers?: string[]
  constraints?: string[]
}
