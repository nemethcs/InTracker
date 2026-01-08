import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useFeatures } from '@/hooks/useFeatures'
import { useTodos } from '@/hooks/useTodos'
import { useFeatureStore } from '@/stores/featureStore'
import { useTodoStore } from '@/stores/todoStore'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TodoCard } from '@/components/todos/TodoCard'
import { TodoEditor } from '@/components/todos/TodoEditor'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { ArrowLeft, Plus, CheckCircle2, Circle, AlertCircle, Clock, User, Edit } from 'lucide-react'
import { format } from 'date-fns'
import type { Todo } from '@/services/todoService'
import type { Feature } from '@/services/featureService'

const statusIcons = {
  new: Circle,
  in_progress: Clock,
  done: CheckCircle2,
  tested: CheckCircle2,
  merged: CheckCircle2,
}

const statusColors = {
  new: 'text-muted-foreground',
  in_progress: 'text-blue-500',
  done: 'text-green-500',
  tested: 'text-yellow-500',
  merged: 'text-purple-500',
}

export function FeatureDetail() {
  const { projectId, featureId } = useParams<{ projectId: string; featureId: string }>()
  const { features, isLoading: featuresLoading } = useFeatures(projectId)
  const { todos, isLoading: todosLoading, refetch: refetchTodos } = useTodos(featureId)
  const { createTodo, updateTodo, deleteTodo, updateTodoStatus } = useTodoStore()
  const { updateFeature } = useFeatureStore()
  const [todoEditorOpen, setTodoEditorOpen] = useState(false)
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null)
  const [featureEditorOpen, setFeatureEditorOpen] = useState(false)

  const feature = features.find(f => f.id === featureId)
  
  // Get first element ID for new todos (we'll improve this later)
  const elementId = '40447518-f6da-4e7a-9857-d42dbd1ca352' // Real-time Sync & WebSocket element

  // Sort todos by position (if available), then by created_at
  // IMPORTANT: This must be before any early returns to maintain hook order
  const sortedTodos = useMemo(() => {
    return [...todos].sort((a, b) => {
      // First sort by position (if both have position)
      if (a.position !== undefined && b.position !== undefined) {
        if (a.position !== b.position) {
          return a.position - b.position
        }
      } else if (a.position !== undefined) {
        return -1 // a has position, b doesn't - a comes first
      } else if (b.position !== undefined) {
        return 1 // b has position, a doesn't - b comes first
      }
      // If positions are equal or both null, sort by created_at
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    })
  }, [todos])

  const todosByStatus = {
    new: sortedTodos.filter(t => t.status === 'new'),
    in_progress: sortedTodos.filter(t => t.status === 'in_progress'),
    done: sortedTodos.filter(t => t.status === 'done'),
  }

  // Subscribe to SignalR real-time updates
  useEffect(() => {
    if (!projectId || !featureId) return

    // Join SignalR project group for real-time updates
    if (signalrService.isConnected()) {
      signalrService.joinProject(projectId).catch((error) => {
        console.error('Failed to join SignalR project group:', error)
      })
    }

    // Handle todo updates
    const handleTodoUpdate = (data: { todoId: string; projectId: string; userId: string; changes: any }) => {
      if (data.projectId === projectId) {
        // Refresh todos list to get updated data
        refetchTodos()
      }
    }

    // Handle feature updates
    const handleFeatureUpdate = (data: { featureId: string; projectId: string; progress: number }) => {
      if (data.featureId === featureId && data.projectId === projectId) {
        // Refresh feature data to get updated progress
        // The feature store will handle this automatically via SignalR subscription
        // No need to reload the page - the store will update the feature
      }
    }

    // Subscribe to SignalR events
    signalrService.on('todoUpdated', handleTodoUpdate)
    signalrService.on('featureUpdated', handleFeatureUpdate)

    // Cleanup: Leave SignalR project group and unsubscribe from events
    return () => {
      signalrService.off('todoUpdated', handleTodoUpdate)
      signalrService.off('featureUpdated', handleFeatureUpdate)
      
      if (projectId && signalrService.isConnected()) {
        signalrService.leaveProject(projectId).catch((error) => {
          console.error('Failed to leave SignalR project group:', error)
        })
      }
    }
  }, [projectId, featureId, refetchTodos])

  if (featuresLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!feature) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Feature not found</CardTitle>
            <CardDescription>Feature ID: {featureId}</CardDescription>
          </CardHeader>
          <CardContent>
            <Link to={`/projects/${projectId}`}>
              <Button variant="outline">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Project
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/projects/${projectId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{feature.name}</h1>
          {feature.description && (
            <p className="text-muted-foreground mt-2">{feature.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Badge 
            variant={
              feature.status === 'done' ? 'default' :
              feature.status === 'tested' ? 'secondary' :
              feature.status === 'in_progress' ? 'secondary' : 'outline'
            }
            className="text-lg px-3 py-1"
          >
            {feature.status}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFeatureEditorOpen(true)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
        </div>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Progress Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted-foreground">Overall Progress</span>
                <span className="font-medium text-lg">{feature.progress_percentage}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-3">
                <div
                  className="bg-primary h-3 rounded-full transition-all"
                  style={{ width: `${feature.progress_percentage}%` }}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{feature.total_todos}</div>
                <div className="text-sm text-muted-foreground">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-muted-foreground">{todosByStatus.new.length}</div>
                <div className="text-sm text-muted-foreground">New</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-500">{todosByStatus.in_progress.length}</div>
                <div className="text-sm text-muted-foreground">In Progress</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">{todosByStatus.done.length}</div>
                <div className="text-sm text-muted-foreground">Done</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">{feature.completed_todos}</div>
                <div className="text-sm text-muted-foreground">Completed</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Todos Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Todos</h2>
          <Button 
            onClick={() => {
              setEditingTodo(null)
              setTodoEditorOpen(true)
            }}
            disabled={todosLoading}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Todo
          </Button>
        </div>

        {todosLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : todos.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No todos yet. Create your first todo to get started.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {/* Todo Status Columns */}
            {(['new', 'in_progress', 'done'] as const).map((status) => {
              const statusTodos = todosByStatus[status]
              if (statusTodos.length === 0) return null

              const StatusIcon = statusIcons[status]
              const statusColor = statusColors[status]

              return (
                <div key={status}>
                  <div className="flex items-center gap-2 mb-2">
                    <StatusIcon className={`h-5 w-5 ${statusColor}`} />
                    <h3 className="font-semibold capitalize">{status.replace('_', ' ')}</h3>
                    <Badge variant="outline" className="ml-2">{statusTodos.length}</Badge>
                  </div>
                  <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                    {statusTodos.map((todo, todoIndex) => {
                      // Calculate todo number: find position in sorted todos
                      const todoNumber = sortedTodos.findIndex(t => t.id === todo.id) + 1
                      
                      return (
                        <TodoCard
                          key={todo.id}
                          todo={todo}
                          number={todoNumber}
                          onEdit={(todo) => {
                            setEditingTodo(todo)
                            setTodoEditorOpen(true)
                          }}
                          onDelete={async (todo) => {
                            if (confirm('Are you sure you want to delete this todo?')) {
                              await deleteTodo(todo.id)
                              refetchTodos()
                            }
                          }}
                          onStatusChange={async (todo, newStatus) => {
                            try {
                              await updateTodoStatus(todo.id, newStatus, todo.version)
                              refetchTodos()
                            } catch (error: any) {
                              if (error.isConflict) {
                                // Show conflict warning
                                alert(`Conflict: ${error.message}\n\nPlease refresh the page to get the latest version.`)
                                // Refresh todos to get latest data
                                refetchTodos()
                              } else {
                                alert(`Failed to update todo: ${error.message}`)
                              }
                            }
                          }}
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

      {/* Todo Editor Dialog */}
      <TodoEditor
        open={todoEditorOpen}
        onOpenChange={(open) => {
          setTodoEditorOpen(open)
          if (!open) {
            setEditingTodo(null)
          }
        }}
        todo={editingTodo}
        featureId={featureId}
        elementId={elementId}
        onSave={async (data) => {
          try {
            if (editingTodo) {
              await updateTodo(editingTodo.id, data as any)
            } else {
              await createTodo(data as any)
            }
            refetchTodos()
          } catch (error) {
            console.error('Failed to save todo:', error)
            throw error // Re-throw to let TodoEditor handle the error
          }
        }}
      />

      {/* Feature Editor Dialog */}
      {projectId && (
        <FeatureEditor
          open={featureEditorOpen}
          onOpenChange={(open) => {
            setFeatureEditorOpen(open)
          }}
          feature={feature}
          projectId={projectId}
          onSave={async (data) => {
            try {
              await updateFeature(featureId, data as any)
              // Refetch features to update the current feature
              window.location.reload() // Simple refresh for now
            } catch (error) {
              console.error('Failed to update feature:', error)
              throw error // Re-throw to let FeatureEditor handle the error
            }
          }}
        />
      )}
    </div>
  )
}
