import { memo } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight } from 'lucide-react'
import type { Feature } from '@/services/featureService'

interface FeatureCardProps {
  feature: Feature
  projectId: string
  onEdit?: (feature: Feature) => void
  number?: number
}

export const FeatureCard = memo(function FeatureCard({ feature, projectId, onEdit, number }: FeatureCardProps) {
  return (
    <Link to={`/projects/${projectId}/features/${feature.id}`}>
      <Card className="hover:shadow-elevated hover-lift transition-smooth cursor-pointer h-full relative">
        {number !== undefined && (
          <div className="absolute top-2 left-2 z-10">
            <Badge variant="outline" className="text-xs font-mono h-5 px-1.5 min-w-[24px] justify-center bg-background shadow-sm">
              {number}
            </Badge>
          </div>
        )}
        <div className="absolute top-2 right-2 z-10">
          <Badge 
            variant={
              feature.status === 'done' ? 'success' :
              feature.status === 'tested' ? 'warning' :
              feature.status === 'in_progress' ? 'info' :
              feature.status === 'merged' ? 'accent' : 'muted'
            }
            className="shadow-sm"
          >
            {feature.status}
          </Badge>
        </div>
        <CardHeader className="pt-10 pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0 pr-2">
              <CardTitle className="mb-1 line-clamp-2 break-words">
                {feature.name}
              </CardTitle>
              {feature.description && (
                <CardDescription className="line-clamp-2">
                  {feature.description}
                </CardDescription>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-muted-foreground">Progress</span>
                <span className="font-medium">{feature.progress_percentage}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${feature.progress_percentage}%` }}
                />
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {feature.completed_todos} / {feature.total_todos} todos
              </span>
              <div className="flex items-center gap-1 text-muted-foreground">
                <span>View</span>
                <ArrowRight className="h-3 w-3" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
})
