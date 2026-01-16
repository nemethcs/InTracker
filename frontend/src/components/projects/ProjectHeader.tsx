import { memo } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout/PageHeader'
import { ActiveUsers } from '@/components/collaboration/ActiveUsers'
import { Edit, UsersRound } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import type { Project } from '@/services/projectService'
import type { Team } from '@/services/adminService'

interface ProjectHeaderProps {
  project: Project
  teams: Team[]
  onEdit: () => void
}

export const ProjectHeader = memo(function ProjectHeader({ project, teams, onEdit }: ProjectHeaderProps) {
  return (
    <PageHeader
      title={
        <div className="flex items-center gap-3 flex-wrap">
          <span>{project.name}</span>
          {project.id && <ActiveUsers projectId={project.id} />}
        </div>
      }
      description={
        <div className="space-y-2">
          {project.description && (
            <p className="text-muted-foreground text-sm sm:text-base">{project.description}</p>
          )}
          <div className="flex flex-wrap gap-2">
            {project.team_id && (
              <Badge variant="outline" className="flex items-center gap-1">
                <UsersRound className={iconSize('xs')} />
                {teams.find(t => t.id === project.team_id)?.name || 'Unknown Team'}
              </Badge>
            )}
            <Badge
              variant={
                project.status === 'active' ? 'success' :
                project.status === 'paused' ? 'warning' :
                project.status === 'blocked' ? 'destructive' :
                project.status === 'completed' ? 'info' :
                project.status === 'archived' ? 'muted' : 'outline'
              }
            >
              {project.status}
            </Badge>
            {project.tags?.map((tag) => (
              <Badge key={tag} variant="secondary">{tag}</Badge>
            ))}
          </div>
        </div>
      }
      actions={
        <Button
          variant="outline"
          size="sm"
          onClick={onEdit}
          className="w-full sm:w-auto"
        >
          <Edit className={`mr-2 ${iconSize('sm')}`} />
          Edit Project
        </Button>
      }
    />
  )
})
