import { Button } from '@/components/ui/button'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { FeatureCard } from '@/components/features/FeatureCard'
import { Plus, FolderKanban } from 'lucide-react'
import type { Feature } from '@/services/featureService'

interface ProjectFeaturesSectionProps {
  projectId: string
  features: Feature[]
  isLoading: boolean
  onCreateFeature: () => void
}

export function ProjectFeaturesSection({
  projectId,
  features,
  isLoading,
  onCreateFeature,
}: ProjectFeaturesSectionProps) {
  // Sort and filter features: in_progress → done → tested (hide merged)
  const sortedFeatures = features
    .filter(f => f.status !== 'merged')
    .sort((a, b) => {
      const statusOrder = { 'in_progress': 0, 'done': 1, 'tested': 2, 'new': 3 }
      const statusDiff = (statusOrder[a.status as keyof typeof statusOrder] ?? 999) -
                        (statusOrder[b.status as keyof typeof statusOrder] ?? 999)
      if (statusDiff !== 0) return statusDiff
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl sm:text-2xl font-bold">Features</h2>
        <Button onClick={onCreateFeature}>
          <Plus className="mr-2 h-4 w-4" />
          New Feature
        </Button>
      </div>
      {isLoading ? (
        <LoadingState variant="combined" size="md" skeletonCount={3} />
      ) : features.length === 0 ? (
        <EmptyState
          icon={<FolderKanban className="h-12 w-12 text-muted-foreground" />}
          title="No features yet"
          description="Create your first feature to get started"
          action={{
            label: 'Create Feature',
            onClick: onCreateFeature,
          }}
          variant="compact"
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {sortedFeatures.map((feature, index) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              projectId={projectId}
              number={index + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
