import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { useFeatures } from '@/hooks/useFeatures'
import { useFeatureStore } from '@/stores/featureStore'
import { useProjectStore } from '@/stores/projectStore'
import { adminService, type Team } from '@/services/adminService'
import { elementService, type ElementTree as ElementTreeData } from '@/services/elementService'
import { documentService, type Document } from '@/services/documentService'
import { todoService } from '@/services/todoService'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { FeatureCard } from '@/components/features/FeatureCard'
import { ProjectEditor } from '@/components/projects/ProjectEditor'
import { ElementTree } from '@/components/elements/ElementTree'
import { ElementDetailDialog } from '@/components/elements/ElementDetailDialog'
import { TodoCard } from '@/components/todos/TodoCard'
import { ActiveUsers } from '@/components/collaboration/ActiveUsers'
import { Plus, Edit, FileText, CheckSquare, UsersRound } from 'lucide-react'

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { currentProject, isLoading: projectLoading, error: projectError } = useProject(id)
  const { features, isLoading: featuresLoading, refetch: refetchFeatures } = useFeatures(id)
  // Get all todos for the project - we'll use the todoService directly since useTodos doesn't support projectId
  const [todos, setTodos] = useState<any[]>([])
  const [isLoadingTodos, setIsLoadingTodos] = useState(false)
  const { createFeature, updateFeature } = useFeatureStore()
  const { updateProject, fetchProject } = useProjectStore()
  const [featureEditorOpen, setFeatureEditorOpen] = useState(false)
  const [editingFeature, setEditingFeature] = useState<any>(null)
  const [projectEditorOpen, setProjectEditorOpen] = useState(false)
  const [elementTree, setElementTree] = useState<ElementTreeData | null>(null)
  const [isLoadingElements, setIsLoadingElements] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [selectedElement, setSelectedElement] = useState<any>(null)
  const [elementDetailOpen, setElementDetailOpen] = useState(false)
  const [teams, setTeams] = useState<Team[]>([])
  const [showProjectStructure, setShowProjectStructure] = useState(false)

  useEffect(() => {
    loadTeams()
  }, [])

  const loadTeams = async () => {
    try {
      const response = await adminService.getTeams()
      setTeams(response.teams)
    } catch (error) {
      console.error('Failed to load teams:', error)
    }
  }

  useEffect(() => {
    if (!id) return

    // Join SignalR project group for real-time updates
    const joinProject = async () => {
      if (signalrService.isConnected()) {
        try {
          await signalrService.joinProject(id)
        } catch (error) {
          console.error('Failed to join SignalR project group:', error)
        }
      }
    }
    
    // Also listen for connection events to join when connection is established
    const handleConnected = () => {
      if (id) {
        joinProject()
      }
    }
    
    // Try to join immediately if already connected
    joinProject()
    
    // Subscribe to connection events
    signalrService.on('connected', handleConnected)
    signalrService.on('reconnected', handleConnected)
    
    // Load element tree
    setIsLoadingElements(true)
    elementService.getProjectTree(id)
        .then((tree) => {
          setElementTree(tree)
          setIsLoadingElements(false)
        })
        .catch((error) => {
          console.error('Failed to load element tree:', error)
          setIsLoadingElements(false)
        })

      setIsLoadingDocuments(true)
      documentService.listDocuments(id)
        .then((docs) => {
          setDocuments(docs)
          setIsLoadingDocuments(false)
        })
        .catch((error) => {
          console.error('Failed to load documents:', error)
          setIsLoadingDocuments(false)
        })

      setIsLoadingTodos(true)
      todoService.listTodos(undefined, undefined, id)
        .then((projectTodos) => {
          // Filter out "done" todos - only show open todos (new, in_progress, tested)
          const openTodos = projectTodos.filter(todo => todo.status !== 'done')
          setTodos(openTodos)
          setIsLoadingTodos(false)
        })
        .catch((error) => {
          console.error('Failed to load todos:', error)
          setIsLoadingTodos(false)
        })

    // Subscribe to SignalR real-time updates
    const handleTodoUpdate = (data: { todoId: string; projectId: string; userId: string; changes: any }) => {
      if (data.projectId === id) {
        // Refresh todos list to get updated data
        todoService.listTodos(undefined, undefined, id)
          .then((projectTodos) => {
            const openTodos = projectTodos.filter(todo => todo.status !== 'done')
            setTodos(openTodos)
          })
          .catch((error) => {
            console.error('Failed to refresh todos after update:', error)
          })
      }
    }

    const handleFeatureUpdate = (data: { featureId: string; projectId: string; progress: number }) => {
      if (data.projectId === id) {
        // Refresh features list to get updated progress
        refetchFeatures()
      }
    }

    const handleUserActivity = (data: { userId: string; projectId: string; action: string; featureId?: string }) => {
      if (data.projectId === id) {
        // Optionally show user activity notifications
        // User activity handled silently
      }
    }

    // Subscribe to SignalR events
    signalrService.on('todoUpdated', handleTodoUpdate)
    signalrService.on('featureUpdated', handleFeatureUpdate)
    signalrService.on('userActivity', handleUserActivity)

    // Cleanup: Leave SignalR project group and unsubscribe from events when component unmounts or project changes
    return () => {
      // Unsubscribe from SignalR events
      signalrService.off('todoUpdated', handleTodoUpdate)
      signalrService.off('featureUpdated', handleFeatureUpdate)
      signalrService.off('userActivity', handleUserActivity)
      
      // Unsubscribe from connection events
      // handleConnected is defined in the same scope, so it's accessible here
      signalrService.off('connected', handleConnected)
      signalrService.off('reconnected', handleConnected)
      
      // Leave SignalR project group
      if (id && signalrService.isConnected()) {
        signalrService.leaveProject(id).catch((error) => {
          console.error('Failed to leave SignalR project group:', error)
        })
      }
    }
  }, [id]) // Removed refetchFeatures from dependencies to prevent infinite loop


  if (projectLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (projectError) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Error loading project</CardTitle>
            <CardDescription>{projectError}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (!currentProject && !projectLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Project not found</CardTitle>
            <CardDescription>Project ID: {id}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (!currentProject) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">{currentProject.name}</h1>
            {/* Small, unobtrusive active users display */}
            {id && <ActiveUsers projectId={id} />}
          </div>
          {currentProject.description && (
            <p className="text-muted-foreground mt-2">{currentProject.description}</p>
          )}
          <div className="flex gap-2 mt-4">
            {currentProject.team_id && (
              <Badge variant="outline" className="flex items-center gap-1">
                <UsersRound className="h-3 w-3" />
                {teams.find(t => t.id === currentProject.team_id)?.name || 'Unknown Team'}
              </Badge>
            )}
            <Badge variant="outline">{currentProject.status}</Badge>
            {currentProject.tags?.map((tag) => (
              <Badge key={tag} variant="secondary">{tag}</Badge>
            ))}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setProjectEditorOpen(true)}
        >
          <Edit className="mr-2 h-4 w-4" />
          Edit Project
        </Button>
      </div>

      {/* Resume Context - Most important: what was done, what's next */}
      {currentProject.resume_context && (
        <Card>
          <CardHeader>
            <CardTitle>Resume Context</CardTitle>
            <CardDescription>Quick overview of recent work and next steps</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentProject.resume_context.last && (
              <div>
                <h3 className="font-semibold mb-1 text-sm">Last</h3>
                <p className="text-sm text-muted-foreground">{currentProject.resume_context.last}</p>
              </div>
            )}
            {currentProject.resume_context.now && (
              <div>
                <h3 className="font-semibold mb-1 text-sm">Now</h3>
                <p className="text-sm text-muted-foreground">{currentProject.resume_context.now}</p>
              </div>
            )}
            {currentProject.resume_context.next && (
              <div>
                <h3 className="font-semibold mb-1 text-sm">Next</h3>
                <p className="text-sm text-muted-foreground">{currentProject.resume_context.next}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Open Todos Section - Next tasks (most important after resume context) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Next Tasks</h2>
          {features.length > 0 && (
            <Link to={`/projects/${id}/features/${features[0]?.id}`}>
              <Button variant="outline" size="sm">
                <CheckSquare className="mr-2 h-4 w-4" />
                View by Feature
              </Button>
            </Link>
          )}
        </div>
        {isLoadingTodos ? (
          <LoadingSpinner />
        ) : todos.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No open todos. All tasks are completed!
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {todos.map((todo) => (
              <TodoCard key={todo.id} todo={todo} />
            ))}
          </div>
        )}
      </div>

      {/* Features Section - Active features (sorted by last update) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Features</h2>
          <Button onClick={() => {
            setEditingFeature(null)
            setFeatureEditorOpen(true)
          }}>
            <Plus className="mr-2 h-4 w-4" />
            New Feature
          </Button>
        </div>
        {featuresLoading ? (
          <LoadingSpinner />
        ) : features.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No features yet. Create your first feature to get started.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <FeatureCard
                key={feature.id}
                feature={feature}
                projectId={id!}
              />
            ))}
          </div>
        )}
      </div>

      {/* Element Tree Section - Moved down, less important for daily work */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Project Structure</h2>
          <div className="flex items-center gap-2">
            {elementTree && elementTree.elements.length > 0 && (
              <div className="text-sm text-muted-foreground">
                {elementTree.elements.length} {elementTree.elements.length === 1 ? 'element' : 'elements'}
              </div>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowProjectStructure(!showProjectStructure)}
            >
              {showProjectStructure ? 'Hide' : 'Show'} Structure
            </Button>
          </div>
        </div>
        {showProjectStructure && (
          <>
            {isLoadingElements ? (
              <Card>
                <CardContent className="py-8">
                  <LoadingSpinner />
                </CardContent>
              </Card>
            ) : elementTree && elementTree.elements.length > 0 ? (
              <Card className="overflow-hidden">
                <CardHeader className="pb-3">
                  <CardDescription>
                    Click on an element to view details. Use the chevron icons to expand/collapse folders.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-[400px] overflow-y-auto">
                    <ElementTree
                      elements={elementTree.elements}
                      onElementClick={(element) => {
                        setSelectedElement(element)
                        setElementDetailOpen(true)
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No elements yet. Project structure will appear here.
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>

      {/* Documents Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Documents</h2>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Document
          </Button>
        </div>
        {isLoadingDocuments ? (
          <LoadingSpinner />
        ) : documents.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No documents yet. Create your first document to get started.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {documents.map((document) => {
              // Get preview of content (first 200 characters, strip markdown)
              const preview = document.content
                ? document.content
                    .replace(/[#*`\[\]]/g, '') // Remove markdown syntax
                    .replace(/\n/g, ' ') // Replace newlines with spaces
                    .trim()
                    .substring(0, 200)
                : 'No content'
              
              // Get first open todo for this element if exists
              const elementTodos = document.element_id 
                ? todos.filter(t => t.element_id === document.element_id && t.status !== 'done')
                : []
              const firstTodo = elementTodos.length > 0 ? elementTodos[0] : null

              // Helper function to find element in tree
              const findElementInTree = (elements: any[], targetId: string): any => {
                for (const el of elements) {
                  if (el.id === targetId) {
                    return el
                  }
                  if (el.children) {
                    const found = findElementInTree(el.children, targetId)
                    if (found) return found
                  }
                }
                return null
              }

              const handleViewTodos = (e: React.MouseEvent) => {
                e.preventDefault()
                if (document.element_id && elementTree) {
                  const element = findElementInTree(elementTree.elements, document.element_id)
                  if (element) {
                    setSelectedElement(element)
                    setElementDetailOpen(true)
                  }
                }
              }

              return (
                <Card key={document.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="mb-1">{document.title}</CardTitle>
                        <CardDescription className="line-clamp-1">
                          {document.type.replace('_', ' ')}
                        </CardDescription>
                      </div>
                      <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {/* Content Preview */}
                      <div className="text-sm text-muted-foreground line-clamp-3 min-h-[3.5rem]">
                        {preview}
                        {document.content && document.content.length > 200 && '...'}
                      </div>
                      
                      <div className="flex items-center justify-between text-sm pt-2 border-t">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="capitalize text-xs">
                            {document.type.replace('_', ' ')}
                          </Badge>
                          {elementTodos.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                              {elementTodos.length} open {elementTodos.length === 1 ? 'todo' : 'todos'}
                            </span>
                          )}
                        </div>
                        {document.element_id && (
                          firstTodo && firstTodo.feature_id ? (
                            <Link to={`/projects/${id}/features/${firstTodo.feature_id}`}>
                              <Button variant="ghost" size="sm" className="h-7 text-xs">
                                <CheckSquare className="mr-1 h-3 w-3" />
                                View Todos
                              </Button>
                            </Link>
                          ) : (
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="h-7 text-xs"
                              onClick={handleViewTodos}
                            >
                              <CheckSquare className="mr-1 h-3 w-3" />
                              View Todos
                            </Button>
                          )
                        )}
                      </div>
                      
                      {document.tags && document.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {document.tags.slice(0, 3).map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 text-xs bg-secondary rounded-md"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {/* Feature Editor Dialog */}
      {id && (
        <FeatureEditor
          open={featureEditorOpen}
          onOpenChange={(open) => {
            setFeatureEditorOpen(open)
            if (!open) {
              setEditingFeature(null)
            }
          }}
          feature={editingFeature}
          projectId={id}
          onSave={async (data) => {
            try {
              if (editingFeature) {
                await updateFeature(editingFeature.id, data as any)
              } else {
                await createFeature(data as any)
              }
              refetchFeatures()
            } catch (error) {
              console.error('Failed to save feature:', error)
              throw error // Re-throw to let FeatureEditor handle the error
            }
          }}
        />
      )}

      {/* Project Editor Dialog */}
      {id && currentProject && (
        <ProjectEditor
          open={projectEditorOpen}
          onOpenChange={(open) => {
            setProjectEditorOpen(open)
          }}
          project={currentProject}
          onSave={async (data) => {
            try {
              await updateProject(id, data as any)
              await fetchProject(id)
            } catch (error) {
              console.error('Failed to update project:', error)
              throw error // Re-throw to let ProjectEditor handle the error
            }
          }}
        />
      )}

      {/* Element Detail Dialog */}
      {id && (
        <ElementDetailDialog
          open={elementDetailOpen}
          onOpenChange={setElementDetailOpen}
          element={selectedElement}
          projectId={id}
        />
      )}
    </div>
  )
}
