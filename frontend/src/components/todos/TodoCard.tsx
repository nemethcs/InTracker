import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle2, Circle, AlertCircle, Clock, User, Edit, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import type { Todo } from '@/services/todoService'

const statusIcons = {
  new: Circle,
  in_progress: Clock,
  done: CheckCircle2,
}

const statusColors = {
  new: 'text-muted-foreground',
  in_progress: 'text-primary',
  done: 'text-success',
}

const priorityColors = {
  low: 'text-muted-foreground',
  medium: 'text-primary',
  high: 'text-yellow-600 dark:text-yellow-400',
  critical: 'text-destructive',
}

const priorityLabels = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
}

interface TodoCardProps {
  todo: Todo
  onEdit?: (todo: Todo) => void
  onDelete?: (todo: Todo) => void
  onStatusChange?: (todo: Todo, newStatus: Todo['status']) => void
  number?: number | string
}

export function TodoCard({ todo, onEdit, onDelete, onStatusChange, number }: TodoCardProps) {
  const StatusIcon = statusIcons[todo.status] || Circle
  const statusColor = statusColors[todo.status] || 'text-muted-foreground'

  return (
    <Card className="hover:shadow-soft hover-lift transition-smooth">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2 flex-1">
            <StatusIcon className={`h-5 w-5 ${statusColor} flex-shrink-0 mt-0.5`} />
            <div className="flex-1">
              <CardTitle className="text-base">
                {todo.title}
              </CardTitle>
              {todo.description && (
                <CardDescription className="line-clamp-2 mt-1">
                  {todo.description}
                </CardDescription>
              )}
            </div>
          </div>
          {number !== undefined && (
            <Badge variant="outline" className="text-xs font-mono h-5 px-1.5 min-w-[24px] justify-center flex-shrink-0">
              {number}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Badge 
              variant={
                todo.status === 'done' ? 'default' :
                todo.status === 'in_progress' ? 'secondary' : 'outline'
              }
              className="capitalize"
            >
              {todo.status.replace('_', ' ')}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {todo.assigned_to && (
              <div className="flex items-center gap-1">
                <User className="h-3 w-3" />
                <span>Assigned</span>
              </div>
            )}
            {todo.priority && (
              <div className={`flex items-center gap-1 font-medium ${priorityColors[todo.priority]}`}>
                <span>Priority: {priorityLabels[todo.priority]}</span>
              </div>
            )}
            <div>
              Updated: {format(new Date(todo.updated_at), 'MMM d, yyyy')}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
