import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { TodoCard } from '@/components/todos/TodoCard'
import { Plus, CheckSquare, Circle, Clock, CheckCircle2 } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import type { Todo } from '@/services/todoService'
import { toast } from '@/hooks/useToast'

const statusIcons = {
  new: Circle,
  in_progress: Clock,
  done: CheckCircle2,
  tested: CheckCircle2,
  merged: CheckCircle2,
}

const statusColors = {
  new: 'text-muted-foreground',
  in_progress: 'text-primary',
  done: 'text-success',
  tested: 'text-warning',
  merged: 'text-accent',
}

interface FeatureTodosSectionProps {
  todos: Todo[]
  sortedTodos: Todo[]
  todosByStatus: {
    new: Todo[]
    in_progress: Todo[]
    done: Todo[]
  }
  isLoading: boolean
  onCreateTodo: () => void
  onEditTodo: (todo: Todo) => void
  onDeleteTodo: (todo: Todo) => Promise<void>
  onStatusChange: (todo: Todo, newStatus: 'new' | 'in_progress' | 'done') => Promise<void>
  onRefetch: () => void
}

export function FeatureTodosSection({
  todos,
  sortedTodos,
  todosByStatus,
  isLoading,
  onCreateTodo,
  onEditTodo,
  onDeleteTodo,
  onStatusChange,
  onRefetch,
}: FeatureTodosSectionProps) {
  const handleStatusChange = async (todo: Todo, newStatus: 'new' | 'in_progress' | 'done') => {
    try {
      await onStatusChange(todo, newStatus)
      onRefetch()
    } catch (error: any) {
      if (error.isConflict) {
        toast.warning('Conflict detected', error.message + '\n\nPlease refresh the page to get the latest version.')
        onRefetch()
      } else {
        toast.error('Failed to update todo', error.message || 'An error occurred')
      }
    }
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
        <h2 className="text-xl sm:text-2xl font-bold">Todos</h2>
        <Button
          onClick={onCreateTodo}
          disabled={isLoading}
          className="w-full sm:w-auto"
        >
          <Plus className={`mr-2 ${iconSize('sm')}`} />
          New Todo
        </Button>
      </div>

      {isLoading ? (
        <LoadingState variant="combined" size="md" skeletonCount={3} />
      ) : todos.length === 0 ? (
        <EmptyState
          icon={<CheckSquare className="h-12 w-12 text-muted-foreground" />}
          title="No todos yet"
          description="Create your first todo to get started"
          action={{
            label: 'Create Todo',
            onClick: onCreateTodo,
          }}
          variant="compact"
        />
      ) : (
        <div className="space-y-4">
          {(['new', 'in_progress', 'done'] as const).map((status) => {
            const statusTodos = todosByStatus[status]
            if (statusTodos.length === 0) return null

            const StatusIcon = statusIcons[status]
            const statusColor = statusColors[status]

            return (
              <div key={status}>
                <div className="flex items-center gap-2 mb-2">
                  <StatusIcon className={`${iconSize('md')} ${statusColor}`} />
                  <h3 className="font-semibold capitalize">{status.replace('_', ' ')}</h3>
                  <Badge variant="outline" className="ml-2">{statusTodos.length}</Badge>
                </div>
                <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                  {statusTodos.map((todo) => {
                    const todoNumber = sortedTodos.findIndex(t => t.id === todo.id) + 1
                    return (
                      <TodoCard
                        key={todo.id}
                        todo={todo}
                        number={todoNumber}
                        onEdit={onEditTodo}
                        onDelete={async (todo) => {
                          if (confirm('Are you sure you want to delete this todo?')) {
                            await onDeleteTodo(todo)
                            onRefetch()
                          }
                        }}
                        onStatusChange={handleStatusChange}
                      />
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
