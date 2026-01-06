import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { FolderKanban, Plus } from 'lucide-react'
import { format } from 'date-fns'

export function Dashboard() {
  const { projects, isLoading, error, refetch } = useProject()

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
          <CardContent>
            <Button onClick={() => refetch()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Manage your projects and track progress</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {projects.length === 0 ? (
        <EmptyState
          icon={<FolderKanban className="h-12 w-12 text-muted-foreground" />}
          title="No projects yet"
          description="Get started by creating your first project"
          action={{
            label: 'Create Project',
            onClick: () => {
              // TODO: Open create project dialog
            },
          }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <CardTitle>{project.name}</CardTitle>
                  <CardDescription>
                    {project.description || 'No description'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <span className="capitalize">{project.status}</span>
                    </div>
                    {project.last_session_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Last session</span>
                        <span>{format(new Date(project.last_session_at), 'MMM d, yyyy')}</span>
                      </div>
                    )}
                    {project.tags && project.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {project.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 text-xs bg-secondary rounded-md"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
