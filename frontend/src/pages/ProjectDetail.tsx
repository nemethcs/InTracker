import { useState, useEffect, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { useFeatures } from '@/hooks/useFeatures'
import { useFeatureStore } from '@/stores/featureStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTodoStore } from '@/stores/todoStore'
import { adminService, type Team } from '@/services/adminService'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState } from '@/components/ui/LoadingState'
import { FeatureEditor } from '@/components/features/FeatureEditor'
import { ProjectEditor } from '@/components/projects/ProjectEditor'
import { ProjectHeader } from '@/components/projects/ProjectHeader'
import { ProjectContextCard } from '@/components/projects/ProjectContextCard'
import { ProjectResumeContextCard } from '@/components/projects/ProjectResumeContextCard'
import { ProjectTodosSection } from '@/components/projects/ProjectTodosSection'
import { ProjectFeaturesSection } from '@/components/projects/ProjectFeaturesSection'
import { CompletedItemsSection } from '@/components/projects/CompletedItemsSection'
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
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null)
  const [projectEditorOpen, setProjectEditorOpen] = useState(false)

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

  // Sort and filter features: in_progress → done → tested (hide merged)
  const sortedFeatures = useMemo(() => {
    const filtered = features.filter(f => f.status !== 'merged')
    const statusOrder = { 'in_progress': 0, 'done': 1, 'tested': 2, 'new': 3 }
    return filtered.sort((a, b) => {
      const statusDiff = (statusOrder[a.status as keyof typeof statusOrder] ?? 999) -
                        (statusOrder[b.status as keyof typeof statusOrder] ?? 999)
      if (statusDiff !== 0) return statusDiff
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
      <ProjectHeader
        project={currentProject}
        teams={teams}
        onEdit={() => setProjectEditorOpen(true)}
      />

      {/* Main Content: Two-column layout for better information density */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Context & Activity (1/3 width on large screens) */}
        <div className="lg:col-span-1 space-y-4">
          <ProjectContextCard
            lastCompletedTodos={lastCompletedTodos}
            lastWorkedFeature={lastWorkedFeature}
          />
          <ProjectResumeContextCard
            resumeContext={currentProject.resume_context}
            allTodos={allTodos}
          />
        </div>

        {/* Right Column: Next Tasks & Features (2/3 width on large screens) */}
        <div className="lg:col-span-2 space-y-6">
          <ProjectTodosSection
            projectId={id!}
            todos={todos}
            isLoading={isLoadingTodos}
            features={features}
          />
          <ProjectFeaturesSection
            projectId={id!}
            features={features}
            isLoading={featuresLoading}
            onCreateFeature={() => {
              setEditingFeature(null)
              setFeatureEditorOpen(true)
            }}
          />
        </div>
      </div>

      {/* Completed Items Section */}
      <CompletedItemsSection
        projectId={id!}
        completedFeatures={completedFeatures}
        completedTodos={completedTodos}
      />

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
