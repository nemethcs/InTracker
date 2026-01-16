import { memo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, CheckSquare, ChevronRight, AlertCircle, FolderKanban } from 'lucide-react'
import type { Project } from '@/services/projectService'
import type { Todo } from '@/services/todoService'
import type { ProjectResumeContext, ResumeContextLast, ResumeContextNow, ResumeContextTodo } from '@/types/resumeContext'

interface ProjectResumeContextCardProps {
  resumeContext: Project['resume_context']
  allTodos: Todo[]
}

export const ProjectResumeContextCard = memo(function ProjectResumeContextCard({ resumeContext, allTodos }: ProjectResumeContextCardProps) {
  if (!resumeContext) {
    return null
  }

  // If resume_context has simple string fields (last, now, next)
  if (typeof resumeContext.last === 'string' || typeof resumeContext.now === 'string' || typeof resumeContext.next === 'string') {
    return (
      <Card className="border-l-4 border-l-secondary">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Resume Context</CardTitle>
          <CardDescription className="text-xs">
            Project status and current progress
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 pt-0">
          <div className="space-y-3">
            {resumeContext.last && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                  <Clock className="h-3 w-3" />
                  Last Session
                </h4>
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                  {resumeContext.last}
                </p>
              </div>
            )}
            {resumeContext.now && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                  <CheckSquare className="h-3 w-3" />
                  Current Status
                </h4>
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                  {resumeContext.now}
                </p>
              </div>
            )}
            {resumeContext.next && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                  <ChevronRight className="h-3 w-3" />
                  Next Steps
                </h4>
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                  {resumeContext.next}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  // If resume_context has complex structure (objects)
  const last = resumeContext.last
  const now = resumeContext.now
  const next = 'next_blockers' in resumeContext ? resumeContext.next_blockers : resumeContext.next

  return (
    <Card className="border-l-4 border-l-secondary">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Resume Context</CardTitle>
        <CardDescription className="text-xs">
          Project status and current progress
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <div className="space-y-3">
          {/* Last Session */}
          {last && (
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                <Clock className="h-3 w-3" />
                Last Session
              </h4>
              {typeof last === 'string' ? (
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{last}</p>
              ) : typeof last === 'object' && last !== null && 'session_summary' in last ? (
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                  {(last as ResumeContextLast).session_summary}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic">No session summary available</p>
              )}
            </div>
          )}

          {/* Current Status */}
          {now && (
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                <CheckSquare className="h-3 w-3" />
                Current Status
              </h4>
              {typeof now === 'string' ? (
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{now}</p>
              ) : (
                <div className="space-y-2">
                  {typeof now === 'object' && now !== null && 'next_todos' in now && Array.isArray((now as ResumeContextNow).next_todos) && (now as ResumeContextNow).next_todos.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Next Todos:</p>
                      <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                        {(now as ResumeContextNow).next_todos
                          .filter((todo: ResumeContextTodo) => {
                            if (todo.id) {
                              const actualTodo = allTodos.find(t => t.id === todo.id)
                              return !actualTodo || actualTodo.status !== 'done'
                            }
                            return true
                          })
                          .slice(0, 3)
                          .map((todo: ResumeContextTodo) => (
                            <li key={todo.id || todo.title} className="text-xs">
                              {todo.title}
                            </li>
                          ))}
                      </ul>
                    </div>
                  )}
                  {typeof now === 'object' && now !== null && 'immediate_goals' in now && Array.isArray((now as ResumeContextNow).immediate_goals) && (now as ResumeContextNow).immediate_goals.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Immediate Goals:</p>
                      <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                        {(now as ResumeContextNow).immediate_goals.map((goal: string, idx: number) => (
                          <li key={idx} className="text-xs">{goal}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Blockers */}
          {resumeContext.blockers && (
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                <AlertCircle className="h-3 w-3" />
                Blockers
              </h4>
              {Array.isArray(resumeContext.blockers) && resumeContext.blockers.length > 0 ? (
                <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                  {resumeContext.blockers.map((blocker: string, idx: number) => (
                    <li key={idx} className="text-xs">{blocker}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground italic">No blockers</p>
              )}
            </div>
          )}

          {/* Constraints */}
          {resumeContext.constraints && (
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                <FolderKanban className="h-3 w-3" />
                Constraints
              </h4>
              {Array.isArray(resumeContext.constraints) && resumeContext.constraints.length > 0 ? (
                <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                  {resumeContext.constraints.map((constraint: string, idx: number) => (
                    <li key={idx} className="text-xs">{constraint}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground italic">No constraints</p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
})
