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
  in_progress: 'text-blue-500',
  done: 'text-green-500',
}

const priorityColors = {
  low: 'text-gray-500',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  critical: 'text-red-500',
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
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2 flex-1">
            <StatusIcon className={`h-5 w-5 ${statusColor} flex-shrink-0 mt-0.5`} />
            <div className="flex-1">
              <CardTitle className="text-base flex items-center gap-2">
                {number !== undefined && (
                  <Badge variant="outline" className="text-xs font-mono h-4 px-1.5 min-w-[20px] justify-center flex-shrink-0">
                    {number}
                  </Badge>
                )}
                {todo.title}
              </CardTitle>
              {todo.description && (
                <CardDescription className="line-clamp-2 mt-1">
                  {todo.description}
                </CardDescription>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1">
            {onEdit && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onEdit(todo)}
              >
                <Edit className="h-4 w-4" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={() => onDelete(todo)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
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
            {onStatusChange && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const nextStatus: Todo['status'] = 
                    todo.status === 'new' ? 'in_progress' :
                    todo.status === 'in_progress' ? 'done' :
                    'new'
                  onStatusChange(todo, nextStatus)
                }}
              >
                <CheckCircle2 className="h-3 w-3 mr-1" />
                {todo.status === 'new' ? 'Start' : 
                 todo.status === 'in_progress' ? 'Mark Done' : 'Reset'}
              </Button>
            )}
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
