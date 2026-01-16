import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckSquare, Clock, ChevronRight } from 'lucide-react'
import { format } from 'date-fns'
import type { Feature } from '@/services/featureService'
import type { Todo } from '@/services/todoService'

interface ProjectContextCardProps {
  lastCompletedTodos: Array<Todo & { featureName?: string }>
  lastWorkedFeature: Feature | null
}

export function ProjectContextCard({ lastCompletedTodos, lastWorkedFeature }: ProjectContextCardProps) {
  if (lastCompletedTodos.length === 0 && !lastWorkedFeature) {
    return null
  }

  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Context & Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            Recent Activity
          </h3>
          {/* Last 3 completed todos */}
          {lastCompletedTodos.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs font-medium text-muted-foreground mb-1.5">
                Last Completed
              </h4>
              <div className="space-y-1.5">
                {lastCompletedTodos.map((todo) => (
                  <div key={todo.id} className="flex items-start gap-2 text-xs">
                    <CheckSquare className="h-3 w-3 text-success flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{todo.title}</div>
                      {todo.featureName && (
                        <Badge variant="outline" className="text-xs px-1 py-0 h-4 mt-0.5">
                          {todo.featureName}
                        </Badge>
                      )}
                    </div>
                    <span className="text-muted-foreground text-xs shrink-0">
                      {format(new Date(todo.completed_at || todo.updated_at), 'MMM d')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last worked feature */}
          {lastWorkedFeature && (
            <div className={lastCompletedTodos.length > 0 ? "pt-3 border-t" : ""}>
              <h4 className="text-xs font-medium text-muted-foreground mb-1.5">
                Last Worked On
              </h4>
              <div className="flex items-center gap-2 text-xs">
                <span className="font-medium truncate flex-1">{lastWorkedFeature.name}</span>
                <Badge
                  variant={
                    lastWorkedFeature.status === 'done' ? 'success' :
                    lastWorkedFeature.status === 'tested' ? 'warning' :
                    lastWorkedFeature.status === 'in_progress' ? 'info' :
                    lastWorkedFeature.status === 'merged' ? 'accent' : 'muted'
                  }
                  className="text-xs px-1.5 py-0 h-4 shrink-0"
                >
                  {lastWorkedFeature.status}
                </Badge>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
