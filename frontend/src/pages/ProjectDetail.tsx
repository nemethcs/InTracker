import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { useFeatures } from '@/hooks/useFeatures'
import { useFeatureStore } from '@/stores/featureStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTodoStore } from '@/stores/todoStore'
import { adminService, type Team } from '@/services/adminService'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { FeatureCard } from '@/components/features/FeatureCard'
import { ProjectEditor } from '@/components/projects/ProjectEditor'
import { TodoCard } from '@/components/todos/TodoCard'
import { ActiveUsers } from '@/components/collaboration/ActiveUsers'
import { Plus, Edit, CheckSquare, UsersRound, ChevronDown, ChevronRight, ChevronLeft, Clock, FolderKanban, CheckCircle2, AlertCircle } from 'lucide-react'
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
  const [todosPage, setTodosPage] = useState(1)
  const TODOS_PER_PAGE = 4

  // Filter and sort todos: only open todos (exclude "done" status) for this project
  // Backend already filters by project_id via JOIN with ProjectElement in get_todos_by_project
  // Sort by priority (critical > high > medium > low) and status (in_progress > new)
  // Use useMemo to avoid recalculating on every render
  const todos = useMemo(() => {
    if (!id) return []
    
    // Backend already filters todos by project_id, so we can trust allTodos contains only project todos
    // Just filter out done todos - backend filtering is reliable
    const filtered = allTodos.filter(todo => {
      // Filter out done todos - only show open todos (new, in_progress)
      if (todo.status === 'done') return false
      // Trust backend filtering - all todos in allTodos are already filtered by project_id
      return true
    })
    
    // Backend already filters todos by project_id, so we can trust allTodos contains only project todos
    // Just filter out done todos - backend filtering is reliable

    // Sort by priority and status
    const priorityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3, undefined: 4 }
    const statusOrder = { 'in_progress': 0, 'new': 1 }

    return filtered.sort((a, b) => {
      // First sort by status (in_progress before new)
      const statusDiff = (statusOrder[a.status as keyof typeof statusOrder] ?? 999) - 
                        (statusOrder[b.status as keyof typeof statusOrder] ?? 999)
      if (statusDiff !== 0) return statusDiff

      // Then sort by priority (critical > high > medium > low)
      const priorityDiff = (priorityOrder[a.priority as keyof typeof priorityOrder] ?? 4) - 
                          (priorityOrder[b.priority as keyof typeof priorityOrder] ?? 4)
      if (priorityDiff !== 0) return priorityDiff

      // Finally sort by updated_at (most recent first)
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  }, [allTodos, id])

  // Paginated todos
  const paginatedTodos = useMemo(() => {
    const startIndex = (todosPage - 1) * TODOS_PER_PAGE
    return todos.slice(startIndex, startIndex + TODOS_PER_PAGE)
  }, [todos, todosPage])

  const totalPages = Math.ceil(todos.length / TODOS_PER_PAGE)

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

  // Get last 3 completed todos (status: done) for Context & Activity
  // IMPORTANT: Only show todos that are actually "done" status and have completed_at or recent updated_at
  const lastCompletedTodos = useMemo(() => {
    const completed = allTodos
      .filter(todo => {
        // STRICT: Only include todos with status === 'done'
        if (todo.status !== 'done') return false
        
        // Only show todos that have completed_at set (were actually completed)
        // OR have updated_at within last 30 days (recently marked as done)
        const updatedAt = new Date(todo.updated_at).getTime()
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000)
        
        // Prefer completed_at, but allow updated_at if recent
        return todo.completed_at || updatedAt > thirtyDaysAgo
      })
      .sort((a, b) => {
        // Prioritize completed_at, then updated_at
        // Most recent first
        const aTime = a.completed_at 
          ? new Date(a.completed_at).getTime() 
          : new Date(a.updated_at).getTime()
        const bTime = b.completed_at 
          ? new Date(b.completed_at).getTime() 
          : new Date(b.updated_at).getTime()
        return bTime - aTime
      })
      .slice(0, 3)
    
    // Enrich with feature names
    return completed.map(todo => ({
      ...todo,
      featureName: todo.feature_id ? features.find(f => f.id === todo.feature_id)?.name : undefined
    }))
  }, [allTodos, id, features])

  // Get all completed todos (status: done) for Completed Items section
  const completedTodos = useMemo(() => {
    const completed = allTodos
      .filter(todo => todo.status === 'done')
      .sort((a, b) => {
        // Use completed_at if available, otherwise fallback to updated_at
        const aTime = a.completed_at ? new Date(a.completed_at).getTime() : new Date(a.updated_at).getTime()
        const bTime = b.completed_at ? new Date(b.completed_at).getTime() : new Date(b.updated_at).getTime()
        return bTime - aTime
      })
    
    // Enrich with feature names
    return completed.map(todo => ({
      ...todo,
      featureName: todo.feature_id ? features.find(f => f.id === todo.feature_id)?.name : undefined
    }))
  }, [allTodos, features])

  // Get all completed features (status: merged, tested, done) for Completed Items section
  const completedFeatures = useMemo(() => {
    return features
      .filter(f => f.status === 'merged' || f.status === 'tested' || f.status === 'done')
      .sort((a, b) => {
        // Sort by updated_at (most recent first)
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      })
  }, [features])

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

    // Reset todos page when project changes
    setTodosPage(1)

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

    const handleProjectUpdate = (data: { projectId: string; changes: any }) => {
      if (data.projectId === id) {
        // Project updated - store will handle this automatically via SignalR subscription
        // But we should refetch to ensure we have the latest data
        fetchProject(id)
      }
    }

    // Subscribe to SignalR events
    signalrService.on('todoUpdated', handleTodoUpdate)
    signalrService.on('featureUpdated', handleFeatureUpdate)
    signalrService.on('userActivity', handleUserActivity)
    signalrService.on('projectUpdated', handleProjectUpdate)

    // Cleanup: Leave SignalR project group and unsubscribe from events when component unmounts or project changes
    return () => {
      // Unsubscribe from SignalR events
      signalrService.off('todoUpdated', handleTodoUpdate)
      signalrService.off('featureUpdated', handleFeatureUpdate)
      signalrService.off('userActivity', handleUserActivity)
      signalrService.off('projectUpdated', handleProjectUpdate)
      
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
      <div className="space-y-4">
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

      {/* Main Content: Two-column layout for better information density */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Context & Activity (1/3 width on large screens) */}
        <div className="lg:col-span-1 space-y-4">
          {/* Combined Recent Activity & Resume Context Card */}
          {(lastCompletedTodos.length > 0 || lastWorkedFeature || currentProject.resume_context) && (
            <Card className="border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Context & Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-0">
                {/* Recent Activity */}
                {(lastCompletedTodos.length > 0 || lastWorkedFeature) && (
                  <div>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                      Recent Activity
                    </h3>
                    {/* Last 3 completed todos */}
                    {lastCompletedTodos.length > 0 && (
                      <div className="mb-3">
                        <h4 className="text-xs font-medium text-muted-foreground mb-1.5">
                          Last Completed
                        </h4>
                        <div className="space-y-1.5">
                          {lastCompletedTodos.map((todo) => (
                            <div key={todo.id} className="flex items-start gap-2 text-xs">
                              <CheckSquare className={`${iconSize('xs')} text-success flex-shrink-0 mt-0.5`} />
                              <div className="flex-1 min-w-0">
                                <div className="font-medium truncate">{todo.title}</div>
                                {todo.featureName && (
                                  <Badge variant="outline" className="text-xs px-1 py-0 h-4 mt-0.5">
                                    {todo.featureName}
                                  </Badge>
                                )}
                              </div>
                              <span className="text-muted-foreground text-xs shrink-0">
                                {format(new Date(todo.completed_at || todo.updated_at), 'MMM d')}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Last worked feature */}
                    {lastWorkedFeature && (
                      <div className={lastCompletedTodos.length > 0 ? "pt-3 border-t" : ""}>
                        <h4 className="text-xs font-medium text-muted-foreground mb-1.5">
                          Last Worked On
                        </h4>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="font-medium truncate flex-1">{lastWorkedFeature.name}</span>
                          <Badge 
                            variant={
                              lastWorkedFeature.status === 'done' ? 'success' :
                              lastWorkedFeature.status === 'tested' ? 'warning' :
                              lastWorkedFeature.status === 'in_progress' ? 'info' :
                              lastWorkedFeature.status === 'merged' ? 'accent' : 'muted'
                            }
                            className="text-xs px-1.5 py-0 h-4 shrink-0"
                          >
                            {lastWorkedFeature.status}
                          </Badge>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
              </CardContent>
            </Card>
          )}

          {/* Resume Context Card - Separate card for project status summary */}
          {currentProject.resume_context && (
            <Card className="border-l-4 border-l-secondary">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Resume Context</CardTitle>
                <CardDescription className="text-xs">
                  Project status and current progress
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                {/* Format resume context based on structure */}
                {(() => {
                  const rc = currentProject.resume_context
                  
                  // If resume_context has simple string fields (last, now, next)
                  if (typeof rc.last === 'string' || typeof rc.now === 'string' || typeof rc.next === 'string') {
                    return (
                      <div className="space-y-3">
                        {rc.last && (
                          <div>
                            <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                              <Clock className="h-3 w-3" />
                              Last Session
                            </h4>
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                              {rc.last}
                            </p>
                          </div>
                        )}
                        {rc.now && (
                          <div>
                            <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                              <CheckSquare className="h-3 w-3" />
                              Current Status
                            </h4>
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                              {rc.now}
                            </p>
                          </div>
                        )}
                        {rc.next && (
                          <div>
                            <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                              <ChevronRight className="h-3 w-3" />
                              Next Steps
                            </h4>
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                              {rc.next}
                            </p>
                          </div>
                        )}
                      </div>
                    )
                  }
                  
                  // If resume_context has complex structure (objects)
                  const last = rc.last
                  const now = rc.now
                  const next = rc.next_blockers || rc.next
                  
                  return (
                    <div className="space-y-3">
                      {/* Last Session */}
                      {last && (
                        <div>
                          <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                            <Clock className="h-3 w-3" />
                            Last Session
                          </h4>
                          {typeof last === 'string' ? (
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{last}</p>
                          ) : last.session_summary ? (
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                              {last.session_summary}
                            </p>
                          ) : (
                            <p className="text-sm text-muted-foreground italic">No session summary available</p>
                          )}
                        </div>
                      )}
                      
                      {/* Current Status */}
                      {now && (
                        <div>
                          <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                            <CheckSquare className="h-3 w-3" />
                            Current Status
                          </h4>
                          {typeof now === 'string' ? (
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{now}</p>
                          ) : (
                            <div className="space-y-2">
                              {now.next_todos && now.next_todos.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-muted-foreground mb-1">Next Todos:</p>
                                  <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                                    {now.next_todos
                                      .filter((todo: any) => {
                                        // Filter out todos that are already done
                                        // Check if todo exists in allTodos and has status 'done'
                                        if (todo.id) {
                                          const actualTodo = allTodos.find(t => t.id === todo.id)
                                          return !actualTodo || actualTodo.status !== 'done'
                                        }
                                        return true
                                      })
                                      .slice(0, 3)
                                      .map((todo: any) => (
                                        <li key={todo.id || todo.title} className="text-xs">
                                          {todo.title}
                                        </li>
                                      ))}
                                  </ul>
                                </div>
                              )}
                              {now.immediate_goals && now.immediate_goals.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-muted-foreground mb-1">Immediate Goals:</p>
                                  <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                                    {now.immediate_goals.map((goal: string, idx: number) => (
                                      <li key={idx} className="text-xs">{goal}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Blockers */}
                      {rc.blockers && (
                        <div>
                          <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                            <AlertCircle className="h-3 w-3" />
                            Blockers
                          </h4>
                          {Array.isArray(rc.blockers) && rc.blockers.length > 0 ? (
                            <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                              {rc.blockers.map((blocker: string, idx: number) => (
                                <li key={idx} className="text-xs">{blocker}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-sm text-muted-foreground italic">No blockers</p>
                          )}
                        </div>
                      )}
                      
                      {/* Constraints */}
                      {rc.constraints && (
                        <div>
                          <h4 className="text-xs font-semibold text-muted-foreground mb-1.5 flex items-center gap-1.5">
                            <FolderKanban className="h-3 w-3" />
                            Constraints
                          </h4>
                          {Array.isArray(rc.constraints) && rc.constraints.length > 0 ? (
                            <ul className="list-disc list-inside space-y-0.5 text-sm text-foreground">
                              {rc.constraints.map((constraint: string, idx: number) => (
                                <li key={idx} className="text-xs">{constraint}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-sm text-muted-foreground italic">No constraints</p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })()}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column: Next Tasks & Features (2/3 width on large screens) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Next Tasks Section */}
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

          {/* Features Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl sm:text-2xl font-bold">Features</h2>
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
              <div className="grid gap-3 sm:grid-cols-2">
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
        </div>
      </div>

      {/* Completed Items Section - Collapsible */}
      {(completedFeatures.length > 0 || completedTodos.length > 0) && (
        <div className="mt-8">
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="completed-items">
              <AccordionTrigger className="text-xl sm:text-2xl font-bold">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className={iconSize('md')} />
                  <span>Completed Items</span>
                  <Badge variant="secondary" className="text-xs">
                    {completedFeatures.length + completedTodos.length} {completedFeatures.length + completedTodos.length === 1 ? 'item' : 'items'}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-6 pt-4">
                  {/* Completed Features */}
                  {completedFeatures.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <FolderKanban className="h-5 w-5" />
                        Completed Features ({completedFeatures.length})
                      </h3>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                        {completedFeatures.map((feature) => (
                          <Link key={feature.id} to={`/projects/${id}/features/${feature.id}`}>
                            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                              <CardHeader>
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <CardTitle className="mb-1 line-clamp-2">{feature.name}</CardTitle>
                                    <CardDescription className="line-clamp-2">
                                      {feature.description || 'No description'}
                                    </CardDescription>
                                  </div>
                                  <Badge 
                                    variant={
                                      feature.status === 'merged' ? 'default' :
                                      feature.status === 'tested' ? 'secondary' :
                                      'outline'
                                    }
                                    className="ml-2 flex-shrink-0"
                                  >
                                    {feature.status}
                                  </Badge>
                                </div>
                              </CardHeader>
                              <CardContent>
                                <div className="flex items-center justify-between text-sm">
                                  <span className="text-muted-foreground">
                                    {format(new Date(feature.updated_at), 'MMM d, yyyy')}
                                  </span>
                                  {feature.progress_percentage !== undefined && (
                                    <span className="text-muted-foreground">
                                      {feature.progress_percentage}% complete
                                    </span>
                                  )}
                                </div>
                              </CardContent>
                            </Card>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Completed Todos */}
                  {completedTodos.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <CheckSquare className="h-5 w-5" />
                        Completed Todos ({completedTodos.length})
                      </h3>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                        {completedTodos.map((todo) => (
                          <Card key={todo.id} className="hover:shadow-lg transition-shadow">
                            <CardHeader>
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <CardTitle className="mb-1 line-clamp-2">{todo.title}</CardTitle>
                                  {todo.description && (
                                    <CardDescription className="line-clamp-2">
                                      {todo.description}
                                    </CardDescription>
                                  )}
                                </div>
                                <Badge variant="outline" className="ml-2 flex-shrink-0">
                                  done
                                </Badge>
                              </div>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2">
                                {todo.featureName && (
                                  <div className="flex items-center gap-2 text-sm">
                                    <FolderKanban className="h-4 w-4 text-muted-foreground" />
                                    <Link 
                                      to={`/projects/${id}/features/${todo.feature_id}`}
                                      className="text-primary hover:underline"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      {todo.featureName}
                                    </Link>
                                  </div>
                                )}
                                <div className="flex items-center justify-between text-sm">
                                  <span className="text-muted-foreground">
                                    {format(new Date(todo.completed_at || todo.updated_at), 'MMM d, yyyy')}
                                  </span>
                                  {todo.priority && (
                                    <Badge variant="outline" className="text-xs capitalize">
                                      {todo.priority}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      )}

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

    </div>
  )
}
