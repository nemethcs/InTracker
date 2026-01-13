import { useEffect } from 'react'
import { useTodos } from '@/hooks/useTodos'
import { useProject } from '@/hooks/useProject'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { TodoCard } from '@/components/todos/TodoCard'
import { CheckSquare } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'

export function Todos() {
  const { projects } = useProject()
  const { todos, isLoading, error, refetch } = useTodos()

  useEffect(() => {
    refetch()
  }, [refetch])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const todosList = Array.isArray(todos) ? todos : []

  return (
    <div className="space-y-6">
      <PageHeader
        title="All Todos"
        description="View and manage todos across all projects"
      />

      {todosList.length === 0 ? (
        <EmptyState
          icon={<CheckSquare className="h-12 w-12 text-muted-foreground" />}
          title="No todos yet"
          description="Todos will appear here when you create them in your projects"
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {todosList.map((todo) => (
            <TodoCard key={todo.id} todo={todo} />
          ))}
        </div>
      )}
    </div>
  )
}
