import { useEffect, useMemo } from 'react'
import { useTodos } from '@/hooks/useTodos'
import { useProject } from '@/hooks/useProject'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { VirtualizedGrid } from '@/components/ui/VirtualizedGrid'
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
      <div className="space-y-6">
        <PageHeader
          title="All Todos"
          description="View and manage todos across all projects"
        />
        <LoadingState variant="combined" size="md" skeletonCount={6} />
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

  // Use virtualization for lists with more than 20 items
  const shouldVirtualize = todosList.length > 20
  const getColumns = (width: number) => {
    if (width >= 1024) return 3 // lg
    if (width >= 768) return 2 // md
    return 1 // sm
  }

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
      ) : shouldVirtualize ? (
        <div className="h-[600px]">
          <VirtualizedGrid
            items={todosList}
            columns={getColumns}
            gap={16}
            itemHeight={180}
            renderItem={(todo) => <TodoCard todo={todo} />}
            containerClassName="h-full"
          />
        </div>
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
