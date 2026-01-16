import { memo } from 'react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout/PageHeader'
import { ArrowLeft, Edit } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import type { Feature } from '@/services/featureService'

interface FeatureHeaderProps {
  projectId: string
  feature: Feature
  onEdit: () => void
}

export const FeatureHeader = memo(function FeatureHeader({ projectId, feature, onEdit }: FeatureHeaderProps) {
  return (
    <PageHeader
      title={
        <div className="flex items-center gap-2 sm:gap-4">
          <Link to={`/projects/${projectId}`}>
            <Button variant="ghost" size="icon" aria-label="Go back to project">
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
            onClick={onEdit}
            className="w-full sm:w-auto"
          >
            <Edit className={`mr-2 ${iconSize('sm')}`} />
            Edit
          </Button>
        </div>
      }
    />
  )
})
