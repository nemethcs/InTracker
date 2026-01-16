import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { useShallow } from 'zustand/react/shallow'
import { useProjectStore } from '@/stores/projectStore'
import { adminService, type Team } from '@/services/adminService'
import { signalrService } from '@/services/signalrService'
import type { ProjectUpdateData } from '@/types/signalr'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { QueryState } from '@/components/ui/QueryState'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingState } from '@/components/ui/LoadingState'
import { ProjectEditor } from '@/components/projects/ProjectEditor'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FolderKanban, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { format } from 'date-fns'
import { PageHeader } from '@/components/layout/PageHeader'

export function Dashboard() {
  const [selectedTeamId, setSelectedTeamId] = useState<string | undefined>(undefined)
  const [statusFilter, setStatusFilter] = useState<string>('active') // Default to active projects
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoadingTeams, setIsLoadingTeams] = useState(false)
  const { projects, isLoading, error, refetch } = useProject(undefined, selectedTeamId, statusFilter)
  // Fetch all projects for statistics (without filters)
  const { projects: allProjects } = useProject(undefined, undefined, 'all')
  const { createProject } = useProjectStore(
    useShallow((state) => ({
      createProject: state.createProject,
    }))
  )
  const location = useLocation()
  const navigate = useNavigate()
  const [projectEditorOpen, setProjectEditorOpen] = useState(false)

  useEffect(() => {
    loadTeams()
  }, [])

  // Subscribe to SignalR real-time updates for projects
  useEffect(() => {
    const handleProjectUpdate = (data: ProjectUpdateData) => {
      // Refetch projects when any project is updated
      refetch()
    }

    // Subscribe to project updates
    signalrService.on('projectUpdated', handleProjectUpdate)

    // Cleanup: unsubscribe when component unmounts
    return () => {
      signalrService.off('projectUpdated', handleProjectUpdate)
    }
  }, [refetch])

  const loadTeams = async () => {
    setIsLoadingTeams(true)
    try {
      const response = await adminService.getTeams()
      setTeams(response.teams)
    } catch (error) {
      console.error('Failed to load teams:', error)
    } finally {
      setIsLoadingTeams(false)
    }
  }

  // Ensure projects is always an array
  const projectsList = Array.isArray(projects) ? projects : []

  // Group projects by team
  const projectsByTeam = projectsList.reduce((acc, project) => {
    const teamId = project.team_id || 'no-team'
    if (!acc[teamId]) {
      acc[teamId] = []
    }
    acc[teamId].push(project)
    return acc
  }, {} as Record<string, typeof projectsList>)

  // Determine title based on route
  const isProjectsPage = location.pathname === '/projects'
  const pageTitle = 'Projects' // Both Dashboard and Projects pages show the same content
  const pageDescription = 'View and manage all your projects'

  if (isLoading || isLoadingTeams) {
    return (
      <div className="space-y-6">
        <PageHeader
          title={pageTitle}
          description={pageDescription}
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
          <CardContent>
            <Button onClick={() => refetch()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Calculate statistics from all projects (not filtered)
  const allProjectsList = Array.isArray(allProjects) ? allProjects : []
  const totalProjects = allProjectsList.length
  const activeProjects = allProjectsList.filter(p => p.status === 'active').length
  const completedProjects = allProjectsList.filter(p => p.status === 'completed').length

  return (
    <div className="space-y-8">
      {/* Header */}
      <PageHeader
        title={pageTitle}
        description={pageDescription}
        actions={
          <Button onClick={() => setProjectEditorOpen(true)} className="w-full sm:w-auto">
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Status Filter */}
        <Select 
          value={statusFilter} 
          onValueChange={(value) => setStatusFilter(value)}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="blocked">Blocked</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>

        {/* Team Filter */}
        {teams.length > 0 && (
          <Select 
            value={selectedTeamId || 'all'} 
            onValueChange={(value) => setSelectedTeamId(value === 'all' ? undefined : value)}
          >
            <SelectTrigger className="w-full sm:w-[200px]">
              <SelectValue placeholder="Filter by team" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Teams</SelectItem>
              {teams.map((team) => (
                <SelectItem key={team.id} value={team.id}>
                  {team.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Statistics Cards */}
      {projectsList.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className="border-l-4 border-l-primary">
            <CardHeader className="pb-3">
              <CardDescription className="text-xs font-medium uppercase tracking-wide">Total Projects</CardDescription>
              <CardTitle className="text-3xl sm:text-4xl font-bold mt-2">{totalProjects}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-l-4 border-l-success">
            <CardHeader className="pb-3">
              <CardDescription className="text-xs font-medium uppercase tracking-wide">Active Projects</CardDescription>
              <CardTitle className="text-3xl sm:text-4xl font-bold mt-2 text-success">{activeProjects}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-l-4 border-l-accent sm:col-span-2 lg:col-span-1">
            <CardHeader className="pb-3">
              <CardDescription className="text-xs font-medium uppercase tracking-wide">Completed Projects</CardDescription>
              <CardTitle className="text-3xl sm:text-4xl font-bold mt-2 text-accent">{completedProjects}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {projectsList.length === 0 ? (
        <EmptyState
          icon={<FolderKanban className="h-12 w-12 text-muted-foreground" />}
          title="No projects yet"
          description="Get started by creating your first project"
          action={{
            label: 'Create Project',
            onClick: () => setProjectEditorOpen(true),
          }}
        />
      ) : (
        <div className="space-y-6">
          {Object.entries(projectsByTeam).map(([teamId, teamProjects]) => {
            // Try to find team by ID (handle both string and UUID formats)
            // Normalize IDs for comparison (remove dashes, convert to lowercase)
            const normalizeId = (id: string) => id?.replace(/-/g, '').toLowerCase() || ''
            const normalizedTeamId = normalizeId(teamId)
            const team = teams.find(t => {
              const normalizedTId = normalizeId(t.id)
              return normalizedTId === normalizedTeamId || t.id === teamId || t.id === String(teamId)
            })
            const teamName = team?.name || (teamId === 'no-team' ? 'No Team' : `Team ${teamId.substring(0, 8)}...`)
            
            return (
              <div key={teamId} className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 pb-2 border-b">
                  <h2 className="text-lg sm:text-xl font-semibold text-foreground">{teamName}</h2>
                  <Badge variant="secondary" className="text-xs font-medium w-fit">
                    {teamProjects.length} {teamProjects.length === 1 ? 'project' : 'projects'}
                  </Badge>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {teamProjects.map((project) => {
                    const statusVariants: Record<string, 'success' | 'warning' | 'destructive' | 'info' | 'muted'> = {
                      active: 'success',
                      paused: 'warning',
                      blocked: 'destructive',
                      completed: 'info',
                      archived: 'muted',
                    }
                    const statusVariant = statusVariants[project.status] || 'muted'
                    
                    return (
                      <Link key={project.id} to={`/projects/${project.id}`} className="group">
                        <Card className="h-full hover:shadow-lg transition-all duration-200 cursor-pointer border-2 hover:border-primary/50">
                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between gap-2 mb-2">
                              <CardTitle className="text-lg font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                                {project.name}
                              </CardTitle>
                              <Badge variant={statusVariant} className="text-xs font-medium shrink-0">
                                {project.status}
                              </Badge>
                            </div>
                            <CardDescription className="text-sm line-clamp-2 min-h-[2.5rem]">
                              {project.description || 'No description'}
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="pt-0">
                            <div className="space-y-2.5">
                              {project.last_session_at && (
                                <div className="flex items-center justify-between text-xs text-muted-foreground">
                                  <span>Last session</span>
                                  <span className="font-medium">{format(new Date(project.last_session_at), 'MMM d, yyyy')}</span>
                                </div>
                              )}
                              {project.tags && project.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 pt-1">
                                  {project.tags.slice(0, 3).map((tag) => (
                                    <Badge
                                      key={tag}
                                      variant="outline"
                                      className="text-xs px-2 py-0.5 font-normal"
                                    >
                                      {tag}
                                    </Badge>
                                  ))}
                                  {project.tags.length > 3 && (
                                    <Badge variant="outline" className="text-xs px-2 py-0.5 font-normal">
                                      +{project.tags.length - 3}
                                    </Badge>
                                  )}
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      </Link>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Project Editor Dialog */}
      <ProjectEditor
        open={projectEditorOpen}
        onOpenChange={setProjectEditorOpen}
        project={null}
        onSave={async (data) => {
          try {
            const newProject = await createProject(data as any)
            refetch()
            // Navigate to the new project
            navigate(`/projects/${newProject.id}`)
          } catch (error) {
            console.error('Failed to create project:', error)
            throw error // Re-throw to let ProjectEditor handle the error
          }
        }}
      />
    </div>
  )
}
