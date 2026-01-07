import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight } from 'lucide-react'
import type { Feature } from '@/services/featureService'

interface FeatureCardProps {
  feature: Feature
  projectId: string
  onEdit?: (feature: Feature) => void
}

export function FeatureCard({ feature, projectId, onEdit }: FeatureCardProps) {
  return (
    <Link to={`/projects/${projectId}/features/${feature.id}`}>
      <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="mb-1">{feature.name}</CardTitle>
              {feature.description && (
                <CardDescription className="line-clamp-2">
                  {feature.description}
                </CardDescription>
              )}
            </div>
            <Badge 
              variant={
                feature.status === 'done' ? 'default' :
                feature.status === 'tested' ? 'secondary' :
                feature.status === 'in_progress' ? 'secondary' : 'outline'
              }
            >
              {feature.status}
            </Badge>
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
}
