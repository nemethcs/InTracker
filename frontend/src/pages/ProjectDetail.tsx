import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { useFeatures } from '@/hooks/useFeatures'
import { useFeatureStore } from '@/stores/featureStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTodoStore } from '@/stores/todoStore'
import { adminService, type Team } from '@/services/adminService'
import { elementService, type ElementTree as ElementTreeData } from '@/services/elementService'
import { documentService, type Document } from '@/services/documentService'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { FeatureCard } from '@/components/features/FeatureCard'
import { ProjectEditor } from '@/components/projects/ProjectEditor'
import { ElementTree } from '@/components/elements/ElementTree'
import { ElementDetailDialog } from '@/components/elements/ElementDetailDialog'
import { TodoCard } from '@/components/todos/TodoCard'
import { ActiveUsers } from '@/components/collaboration/ActiveUsers'
import { Plus, Edit, FileText, CheckSquare, UsersRound, ChevronDown, ChevronRight, Clock, FolderKanban, Layers } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import { PageHeader } from '@/components/layout/PageHeader'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { format } from 'date-fns'
import type { Feature } from '@/services/featureService'
import type { Todo } from '@/services/todoService'

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { currentProject, isLoading: projectLoading, error: projectError } = useProject(id)
  const { features, isLoading: featuresLoading, refetch: refetchFeatures } = useFeatures(id)
  // Use todoStore directly - it supports projectId and auto-updates via SignalR
  const { todos: allTodos, isLoading: isLoadingTodos, fetchTodos } = useTodoStore()
  const { createFeature, updateFeature } = useFeatureStore()
  const { updateProject, fetchProject } = useProjectStore()
  const [featureEditorOpen, setFeatureEditorOpen] = useState(false)
  const [editingFeature, setEditingFeature] = useState<any>(null)
  const [projectEditorOpen, setProjectEditorOpen] = useState(false)
  const [elementTree, setElementTree] = useState<ElementTreeData | null>(null)
  // Filter todos: only open todos (exclude "done" status) for this project
  // Filter by project using element tree - only show todos whose elements belong to this project
  // Use useMemo to avoid recalculating on every render and to handle elementTree initialization
  const todos = useMemo(() => {
    return allTodos.filter(todo => {
      if (todo.status === 'done') return false // Only show open todos
      if (!id || !elementTree) return true // If no project or element tree not loaded yet, show all
      // Check if todo's element belongs to this project by searching in element tree
      const findElementInTree = (elements: any[]): boolean => {
        for (const el of elements) {
          if (el.id === todo.element_id) return true
          if (el.children && findElementInTree(el.children)) return true
        }
        return false
      }
      return findElementInTree(elementTree.elements)
    })
  }, [allTodos, id, elementTree])

  // Sort and filter features: in_progress → done → tested (hide merged)
  const sortedFeatures = useMemo(() => {
    const filtered = features.filter(f => f.status !== 'merged')
    
    // Sort by status priority, then by updated_at
    const statusOrder = { 'in_progress': 0, 'done': 1, 'tested': 2, 'new': 3 }
    
    return filtered.sort((a, b) => {
      const statusDiff = (statusOrder[a.status as keyof typeof statusOrder] ?? 999) - 
                        (statusOrder[b.status as keyof typeof statusOrder] ?? 999)
      if (statusDiff !== 0) return statusDiff
      
      // Within same status, sort by updated_at (most recent first)
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  }, [features])

  // Get last 3 completed todos (status: done)
  const lastCompletedTodos = useMemo(() => {
    const completed = allTodos
      .filter(todo => {
        if (todo.status !== 'done') return false
        if (!id || !elementTree) return true
        const findElementInTree = (elements: any[]): boolean => {
          for (const el of elements) {
            if (el.id === todo.element_id) return true
            if (el.children && findElementInTree(el.children)) return true
          }
          return false
        }
        return findElementInTree(elementTree.elements)
      })
      .sort((a, b) => {
        // Use completed_at if available, otherwise fallback to updated_at
        const aTime = a.completed_at ? new Date(a.completed_at).getTime() : new Date(a.updated_at).getTime()
        const bTime = b.completed_at ? new Date(b.completed_at).getTime() : new Date(b.updated_at).getTime()
        return bTime - aTime
      })
      .slice(0, 3)
    
    // Enrich with feature names
    return completed.map(todo => ({
      ...todo,
      featureName: todo.feature_id ? features.find(f => f.id === todo.feature_id)?.name : undefined
    }))
  }, [allTodos, id, elementTree, features])

  // Get last worked feature (has in_progress or done todos, or was recently updated)
  const lastWorkedFeature = useMemo(() => {
    if (sortedFeatures.length === 0) return null
    
    // Find features with active todos
    const featuresWithActiveTodos = sortedFeatures
      .map(feature => {
        const activeTodos = allTodos.filter(t => 
          t.feature_id === feature.id && 
          (t.status === 'in_progress' || t.status === 'done')
        )
        return { feature, activeTodos: activeTodos.length, lastTodoUpdate: 
          activeTodos.length > 0 ? Math.max(...activeTodos.map(t => new Date(t.updated_at).getTime())) : 0
        }
      })
      .filter(f => f.activeTodos > 0 || new Date(f.feature.updated_at).getTime() > Date.now() - 7 * 24 * 60 * 60 * 1000) // Last 7 days
    
    if (featuresWithActiveTodos.length === 0) {
      // Fallback to most recently updated feature
      return sortedFeatures[0]
    }
    
    // Sort by last todo update or feature update
    featuresWithActiveTodos.sort((a, b) => {
      const aTime = a.lastTodoUpdate || new Date(a.feature.updated_at).getTime()
      const bTime = b.lastTodoUpdate || new Date(b.feature.updated_at).getTime()
      return bTime - aTime
    })
    
    return featuresWithActiveTodos[0].feature
  }, [sortedFeatures, allTodos])
  const [isLoadingElements, setIsLoadingElements] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [selectedElement, setSelectedElement] = useState<any>(null)
  const [elementDetailOpen, setElementDetailOpen] = useState(false)
  const [teams, setTeams] = useState<Team[]>([])

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
          console.log('Element tree loaded:', tree)
          setElementTree(tree)
          setIsLoadingElements(false)
        })
        .catch((error) => {
          console.error('Failed to load element tree:', error)
          setElementTree(null)
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

      // Fetch todos using store - it will auto-update via SignalR
      fetchTodos(undefined, undefined, id)

    // Subscribe to SignalR real-time updates
    // Note: We don't need to manually refresh - the stores auto-update via SignalR subscriptions
    // The components will re-render automatically when the store state changes
    const handleTodoUpdate = (data: { todoId: string; projectId: string; userId: string; changes: any }) => {
      // Store already handles this via SignalR subscription in todoStore
      // Only fetch if the todo is not in the current list (e.g., new todo created)
      // The store's SignalR handler will fetch it automatically if needed
    }

    const handleFeatureUpdate = (data: { featureId: string; projectId: string; progress: number }) => {
      // Store already handles this via SignalR subscription in featureStore
      // No need to manually refetch - the store updates automatically
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
      <div className="space-y-6">
        <LoadingState variant="combined" size="md" skeletonCount={8} />
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
      <PageHeader
        title={
          <div className="flex items-center gap-3 flex-wrap">
            <span>{currentProject.name}</span>
            {/* Small, unobtrusive active users display */}
            {id && <ActiveUsers projectId={id} />}
          </div>
        }
        description={
          <div className="space-y-2">
            {currentProject.description && (
              <p className="text-muted-foreground text-sm sm:text-base">{currentProject.description}</p>
            )}
            <div className="flex flex-wrap gap-2">
              {currentProject.team_id && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <UsersRound className={iconSize('xs')} />
                  {teams.find(t => t.id === currentProject.team_id)?.name || 'Unknown Team'}
                </Badge>
              )}
              <Badge 
                variant={
                  currentProject.status === 'active' ? 'success' :
                  currentProject.status === 'paused' ? 'warning' :
                  currentProject.status === 'blocked' ? 'destructive' :
                  currentProject.status === 'completed' ? 'info' :
                  currentProject.status === 'archived' ? 'muted' : 'outline'
                }
              >
                {currentProject.status}
              </Badge>
              {currentProject.tags?.map((tag) => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
          </div>
        }
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => setProjectEditorOpen(true)}
            className="w-full sm:w-auto"
          >
            <Edit className={`mr-2 ${iconSize('sm')}`} />
            Edit Project
          </Button>
        }
      />

      {/* Recent Activity - Compact display */}
      {(lastCompletedTodos.length > 0 || lastWorkedFeature) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Last 3 completed todos */}
            {lastCompletedTodos.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                  Last 3 Completed
                </h3>
                <div className="space-y-1.5">
                  {lastCompletedTodos.map((todo, idx) => (
                    <div key={todo.id} className="flex items-start gap-2 text-sm">
                      <CheckSquare className={`${iconSize('xs')} text-success mt-0.5 flex-shrink-0`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium truncate">{todo.title}</span>
                          {todo.featureName && (
                            <Badge variant="outline" className="text-xs px-1.5 py-0">
                              {todo.featureName}
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Clock className={iconSize('xs')} />
                          {format(new Date(todo.completed_at || todo.updated_at), 'MMM d, HH:mm')}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Last worked feature */}
            {lastWorkedFeature && (
              <div className="pt-2 border-t">
                <h3 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                  Last Worked On
                </h3>
                <div className="flex items-start gap-2 text-sm">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{lastWorkedFeature.name}</span>
                      <Badge 
                        variant={
                          lastWorkedFeature.status === 'done' ? 'default' :
                          lastWorkedFeature.status === 'tested' ? 'secondary' :
                          lastWorkedFeature.status === 'in_progress' ? 'secondary' : 'outline'
                        }
                        className="text-xs"
                      >
                        {lastWorkedFeature.status}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                      <Clock className="h-3 w-3" />
                      {format(new Date(lastWorkedFeature.updated_at), 'MMM d, HH:mm')}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
          <LoadingState variant="combined" size="md" skeletonCount={3} />
        ) : todos.length === 0 ? (
          <EmptyState
            icon={<CheckSquare className="h-12 w-12 text-muted-foreground" />}
            title="No open todos"
            description="All tasks are completed! Great job!"
            variant="compact"
          />
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
          <LoadingState variant="combined" size="md" skeletonCount={3} />
        ) : features.length === 0 ? (
          <EmptyState
            icon={<FolderKanban className="h-12 w-12 text-muted-foreground" />}
            title="No features yet"
            description="Create your first feature to get started"
            action={{
              label: 'Create Feature',
              onClick: () => {
                setEditingFeature(null)
                setFeatureEditorOpen(true)
              }
            }}
            variant="compact"
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sortedFeatures.map((feature, index) => (
              <FeatureCard
                key={feature.id}
                feature={feature}
                projectId={id!}
                number={index + 1}
              />
            ))}
          </div>
        )}
      </div>

      {/* Element Tree Section - Collapsible with Accordion */}
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="project-structure">
          <AccordionTrigger className="text-xl sm:text-2xl font-bold">
            <div className="flex items-center gap-2">
              <Layers className={iconSize('md')} />
              <span>Project Structure</span>
              {elementTree && elementTree.elements && elementTree.elements.length > 0 && (
                <span className="text-sm font-normal text-muted-foreground">
                  ({elementTree.elements.length} {elementTree.elements.length === 1 ? 'element' : 'elements'})
                </span>
              )}
            </div>
          </AccordionTrigger>
          <AccordionContent>
            {isLoadingElements ? (
              <Card>
                <CardContent className="py-8">
                  <LoadingState variant="combined" size="md" skeletonCount={3} />
                </CardContent>
              </Card>
            ) : elementTree && elementTree.elements && elementTree.elements.length > 0 ? (
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
              <EmptyState
                icon={<Layers className="h-12 w-12 text-muted-foreground" />}
                title="No elements yet"
                description="Elements are created automatically when you add features and todos to the project."
                variant="compact"
              />
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Documents Section */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <h2 className="text-xl sm:text-2xl font-bold">Documents</h2>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Document
          </Button>
        </div>
        {isLoadingDocuments ? (
          <LoadingState variant="combined" size="md" skeletonCount={3} />
        ) : documents.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-12 w-12 text-muted-foreground" />}
            title="No documents yet"
            description="Create your first document to get started"
            variant="compact"
          />
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
