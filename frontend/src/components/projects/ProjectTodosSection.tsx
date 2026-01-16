import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingState } from '@/components/ui/LoadingState'
import { TodoCard } from '@/components/todos/TodoCard'
import { CheckSquare, ChevronLeft, ChevronRight } from 'lucide-react'
import type { Todo } from '@/services/todoService'
import type { Feature } from '@/services/featureService'

interface ProjectTodosSectionProps {
  projectId: string
  todos: Todo[]
  isLoading: boolean
  features: Feature[]
}

const TODOS_PER_PAGE = 4

export function ProjectTodosSection({ projectId, todos, isLoading, features }: ProjectTodosSectionProps) {
  const [todosPage, setTodosPage] = useState(1)

  const paginatedTodos = todos.slice(
    (todosPage - 1) * TODOS_PER_PAGE,
    todosPage * TODOS_PER_PAGE
  )
  const totalPages = Math.ceil(todos.length / TODOS_PER_PAGE)

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-xl sm:text-2xl font-bold">Next Tasks</h2>
          {todos.length > 0 && (
            <Badge variant="secondary" className="text-xs">
              {todos.length} {todos.length === 1 ? 'task' : 'tasks'}
            </Badge>
          )}
        </div>
        {features.length > 0 && todos.length > 0 && (
          <Link to={`/projects/${projectId}/features/${features[0]?.id}`}>
            <Button variant="outline" size="sm">
              <CheckSquare className="mr-2 h-4 w-4" />
              View by Feature
            </Button>
          </Link>
        )}
      </div>
      {isLoading ? (
        <LoadingState variant="combined" size="md" skeletonCount={3} />
      ) : todos.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-8 text-center">
            <CheckSquare className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm font-medium text-foreground mb-1">No open todos</p>
            <p className="text-xs text-muted-foreground">All tasks are completed! Great job!</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            {paginatedTodos.map((todo) => (
              <TodoCard key={todo.id} todo={todo} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Showing {((todosPage - 1) * TODOS_PER_PAGE) + 1}-{Math.min(todosPage * TODOS_PER_PAGE, todos.length)} of {todos.length}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTodosPage(prev => Math.max(1, prev - 1))}
                  disabled={todosPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <div className="text-sm text-muted-foreground min-w-[60px] text-center">
                  {todosPage} / {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTodosPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={todosPage === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
