import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useShallow } from 'zustand/react/shallow'
import { useFeatures } from '@/hooks/useFeatures'
import { useTodos } from '@/hooks/useTodos'
import { useFeatureStore } from '@/stores/featureStore'
import { useTodoStore } from '@/stores/todoStore'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingState } from '@/components/ui/LoadingState'
import { TodoEditor } from '@/components/todos/TodoEditor'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { DocumentEditor } from '@/components/documents/DocumentEditor'
import { documentService, type Document } from '@/services/documentService'
import { ArrowLeft } from 'lucide-react'
import { FeatureHeader } from '@/components/features/FeatureHeader'
import { FeatureProgressOverview } from '@/components/features/FeatureProgressOverview'
import { FeatureTodosSection } from '@/components/features/FeatureTodosSection'
import { FeatureDocumentsSection } from '@/components/features/FeatureDocumentsSection'
import type { Todo } from '@/services/todoService'
import type { Feature } from '@/services/featureService'

export function FeatureDetail() {
  const { projectId, featureId } = useParams<{ projectId: string; featureId: string }>()
  const { features, isLoading: featuresLoading, refetch: refetchFeatures } = useFeatures(projectId)
  const { todos, isLoading: todosLoading, refetch: refetchTodos } = useTodos(featureId)
  const { createTodo, updateTodo, deleteTodo, updateTodoStatus } = useTodoStore(
    useShallow((state) => ({
      createTodo: state.createTodo,
      updateTodo: state.updateTodo,
      deleteTodo: state.deleteTodo,
      updateTodoStatus: state.updateTodoStatus,
    }))
  )
  const { updateFeature } = useFeatureStore(
    useShallow((state) => ({
      updateFeature: state.updateFeature,
    }))
  )
  const [todoEditorOpen, setTodoEditorOpen] = useState(false)
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null)
  const [featureEditorOpen, setFeatureEditorOpen] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [documentEditorOpen, setDocumentEditorOpen] = useState(false)
  const [editingDocument, setEditingDocument] = useState<Document | null>(null)

  const feature = features.find(f => f.id === featureId)

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

  // Load documents for this feature
  useEffect(() => {
    if (!projectId || !featureId) return

    setIsLoadingDocuments(true)
    documentService.listDocuments(projectId, undefined, undefined, featureId)
      .then((docs) => {
        setDocuments(docs)
        setIsLoadingDocuments(false)
      })
      .catch((error) => {
        console.error('Failed to load documents:', error)
        setDocuments([])
        setIsLoadingDocuments(false)
      })
  }, [projectId, featureId])

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
    <div className="space-y-4">
      <FeatureHeader
        projectId={projectId!}
        feature={feature}
        onEdit={() => setFeatureEditorOpen(true)}
      />

      <FeatureProgressOverview
        feature={feature}
        todosByStatus={todosByStatus}
      />

      <FeatureTodosSection
        todos={todos}
        sortedTodos={sortedTodos}
        todosByStatus={todosByStatus}
        isLoading={todosLoading}
        onCreateTodo={() => {
          setEditingTodo(null)
          setTodoEditorOpen(true)
        }}
        onEditTodo={(todo) => {
          setEditingTodo(todo)
          setTodoEditorOpen(true)
        }}
        onDeleteTodo={async (todo) => {
          await deleteTodo(todo.id)
        }}
        onStatusChange={async (todo, newStatus) => {
          await updateTodoStatus(todo.id, newStatus, todo.version)
        }}
        onRefetch={refetchTodos}
      />

      <FeatureDocumentsSection
        documents={documents}
        isLoading={isLoadingDocuments}
        onCreateDocument={() => {
          setEditingDocument(null)
          setDocumentEditorOpen(true)
        }}
        onEditDocument={(document) => {
          setEditingDocument(document)
          setDocumentEditorOpen(true)
        }}
      />

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
        projectId={projectId}
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

      {/* Document Editor Dialog */}
      {projectId && featureId && (
        <DocumentEditor
          open={documentEditorOpen}
          onOpenChange={(open) => {
            setDocumentEditorOpen(open)
            if (!open) {
              setEditingDocument(null)
            }
          }}
          document={editingDocument}
          projectId={projectId}
          onSave={async (data) => {
            try {
              if (editingDocument) {
                await documentService.updateDocument(editingDocument.id, data as any)
              } else {
                // Create new document with feature_id
                await documentService.createDocument({
                  ...data as any,
                  project_id: projectId,
                  feature_id: featureId,
                })
              }
              // Reload documents
              const docs = await documentService.listDocuments(projectId, undefined, undefined, featureId)
              setDocuments(docs)
            } catch (error) {
              console.error('Failed to save document:', error)
              throw error
            }
          }}
        />
      )}

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
