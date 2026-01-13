import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useFeatures } from '@/hooks/useFeatures'
import { useTodos } from '@/hooks/useTodos'
import { useFeatureStore } from '@/stores/featureStore'
import { useTodoStore } from '@/stores/todoStore'
import { signalrService } from '@/services/signalrService'
import { elementService, type ElementTree } from '@/services/elementService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TodoCard } from '@/components/todos/TodoCard'
import { TodoEditor } from '@/components/todos/TodoEditor'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { ArrowLeft, Plus, CheckCircle2, Circle, AlertCircle, Clock, User, Edit } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import { format } from 'date-fns'
import { PageHeader } from '@/components/layout/PageHeader'
import type { Todo } from '@/services/todoService'
import type { Feature } from '@/services/featureService'
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

export function FeatureDetail() {
  const { projectId, featureId } = useParams<{ projectId: string; featureId: string }>()
  const { features, isLoading: featuresLoading, refetch: refetchFeatures } = useFeatures(projectId)
  const { todos, isLoading: todosLoading, refetch: refetchTodos } = useTodos(featureId)
  const { createTodo, updateTodo, deleteTodo, updateTodoStatus } = useTodoStore()
  const { updateFeature } = useFeatureStore()
  const [todoEditorOpen, setTodoEditorOpen] = useState(false)
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null)
  const [featureEditorOpen, setFeatureEditorOpen] = useState(false)
  const [elementTree, setElementTree] = useState<ElementTree | null>(null)
  const [isLoadingElements, setIsLoadingElements] = useState(false)

  const feature = features.find(f => f.id === featureId)
  
  // Get element ID for new todos - use first element from project tree or feature's linked elements
  const elementId = useMemo(() => {
    if (!elementTree || !elementTree.elements || elementTree.elements.length === 0) {
      return undefined
    }
    
    // Helper function to find first element in tree (recursive)
    const findFirstElement = (elements: any[]): string | undefined => {
      for (const el of elements) {
        // Prefer component or module type elements
        if (el.type === 'component' || el.type === 'module') {
          return el.id
        }
        // Check children recursively
        if (el.children && el.children.length > 0) {
          const childId = findFirstElement(el.children)
          if (childId) return childId
        }
      }
      // Fallback to first element
      return elements[0]?.id
    }
    
    return findFirstElement(elementTree.elements)
  }, [elementTree])

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

  // Load element tree for project
  useEffect(() => {
    if (!projectId) return

    setIsLoadingElements(true)
    elementService.getProjectTree(projectId)
      .then((tree) => {
        setElementTree(tree)
        setIsLoadingElements(false)
      })
      .catch((error) => {
        console.error('Failed to load element tree:', error)
        setElementTree(null)
        setIsLoadingElements(false)
      })
  }, [projectId])

  // Subscribe to SignalR real-time updates
  useEffect(() => {
    if (!projectId || !featureId) return

    // Join SignalR project group for real-time updates
    const joinProject = async () => {
      if (signalrService.isConnected()) {
        try {
          await signalrService.joinProject(projectId)
        } catch (error) {
          console.error('Failed to join SignalR project group:', error)
        }
      }
    }

    // Handle connection events to join when connection is established
    const handleConnected = () => {
      if (projectId) {
        joinProject()
      }
    }

    // Try to join immediately if already connected
    joinProject()

    // Subscribe to connection events
    signalrService.on('connected', handleConnected)
    signalrService.on('reconnected', handleConnected)

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
      // Unsubscribe from SignalR events
      signalrService.off('todoUpdated', handleTodoUpdate)
      signalrService.off('featureUpdated', handleFeatureUpdate)
      
      // Unsubscribe from connection events
      signalrService.off('connected', handleConnected)
      signalrService.off('reconnected', handleConnected)
      
      // Leave SignalR project group
      if (projectId && signalrService.isConnected()) {
        signalrService.leaveProject(projectId).catch((error) => {
          console.error('Failed to leave SignalR project group:', error)
        })
      }
    }
  }, [projectId, featureId, refetchTodos])

  if (featuresLoading) {
    return (
      <div className="space-y-6">
        <LoadingState variant="combined" size="md" skeletonCount={6} />
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
      <PageHeader
        title={
          <div className="flex items-center gap-2 sm:gap-4">
            <Link to={`/projects/${projectId}`}>
              <Button variant="ghost" size="icon">
                <ArrowLeft className={iconSize('sm')} />
              </Button>
            </Link>
            <span className="truncate">{feature.name}</span>
          </div>
        }
        description={feature.description}
        actions={
          <div className="flex items-center gap-2">
            <Badge 
              variant={
                feature.status === 'done' ? 'success' :
                feature.status === 'tested' ? 'warning' :
                feature.status === 'in_progress' ? 'info' :
                feature.status === 'merged' ? 'accent' : 'muted'
              }
              className="text-base sm:text-lg px-2 sm:px-3 py-1"
            >
              {feature.status}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFeatureEditorOpen(true)}
              className="w-full sm:w-auto"
            >
              <Edit className={`mr-2 ${iconSize('sm')}`} />
              Edit
            </Button>
          </div>
        }
      />

      {/* Progress Overview */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Progress Overview</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-muted-foreground">Overall Progress</span>
                <span className="font-semibold text-base">{feature.progress_percentage}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${feature.progress_percentage}%` }}
                />
              </div>
            </div>
            <div className="grid grid-cols-5 gap-2">
              <div className="text-center">
                <div className="text-lg font-bold">{feature.total_todos}</div>
                <div className="text-xs text-muted-foreground">Total</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-muted-foreground">{todosByStatus.new.length}</div>
                <div className="text-xs text-muted-foreground">New</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-primary">{todosByStatus.in_progress.length}</div>
                <div className="text-xs text-muted-foreground">In Progress</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-success">{todosByStatus.done.length}</div>
                <div className="text-xs text-muted-foreground">Done</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-success">{feature.completed_todos}</div>
                <div className="text-xs text-muted-foreground">Completed</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Todos Section */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <h2 className="text-xl sm:text-2xl font-bold">Todos</h2>
          <Button 
            onClick={() => {
              setEditingTodo(null)
              setTodoEditorOpen(true)
            }}
            disabled={todosLoading}
            className="w-full sm:w-auto"
          >
            <Plus className={`mr-2 ${iconSize('sm')}`} />
            New Todo
          </Button>
        </div>

        {todosLoading ? (
          <LoadingState variant="combined" size="md" skeletonCount={3} />
        ) : todos.length === 0 ? (
          <EmptyState
            icon={<CheckSquare className="h-12 w-12 text-muted-foreground" />}
            title="No todos yet"
            description="Create your first todo to get started"
            action={{
              label: 'Create Todo',
              onClick: () => {
                setEditingTodo(null)
                setTodoEditorOpen(true)
              }
            }}
            variant="compact"
          />
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
                    <StatusIcon className={`${iconSize('md')} ${statusColor}`} />
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
                                toast.warning('Conflict detected', error.message + '\n\nPlease refresh the page to get the latest version.')
                                // Refresh todos to get latest data
                                refetchTodos()
                              } else {
                                toast.error('Failed to update todo', error.message || 'An error occurred')
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
        elementId={elementId || undefined}
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
              refetchFeatures()
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
