import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useProject } from '@/hooks/useProject'
import { useFeatures } from '@/hooks/useFeatures'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { Badge } from '@/components/ui/badge'

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { currentProject, isLoading: projectLoading } = useProject(id)
  const { features, isLoading: featuresLoading } = useFeatures(id)

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Project not found</CardTitle>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{currentProject.name}</h1>
        {currentProject.description && (
          <p className="text-muted-foreground mt-2">{currentProject.description}</p>
        )}
        <div className="flex gap-2 mt-4">
          <Badge variant="outline">{currentProject.status}</Badge>
          {currentProject.tags?.map((tag) => (
            <Badge key={tag} variant="secondary">{tag}</Badge>
          ))}
        </div>
      </div>

      {currentProject.resume_context && (
        <Card>
          <CardHeader>
            <CardTitle>Resume Context</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentProject.resume_context.last && (
              <div>
                <h3 className="font-semibold mb-1">Last</h3>
                <p className="text-sm text-muted-foreground">{currentProject.resume_context.last}</p>
              </div>
            )}
            {currentProject.resume_context.now && (
              <div>
                <h3 className="font-semibold mb-1">Now</h3>
                <p className="text-sm text-muted-foreground">{currentProject.resume_context.now}</p>
              </div>
            )}
            {currentProject.resume_context.next && (
              <div>
                <h3 className="font-semibold mb-1">Next</h3>
                <p className="text-sm text-muted-foreground">{currentProject.resume_context.next}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="text-2xl font-bold mb-4">Features</h2>
        {featuresLoading ? (
          <LoadingSpinner />
        ) : features.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No features yet
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {features.map((feature) => (
              <Card key={feature.id}>
                <CardHeader>
                  <CardTitle>{feature.name}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Progress</span>
                      <span className="text-sm font-medium">{feature.progress_percentage}%</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${feature.progress_percentage}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        {feature.completed_todos} / {feature.total_todos} todos
                      </span>
                      <Badge variant="outline">{feature.status}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
