import { memo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Feature } from '@/services/featureService'
import type { Todo } from '@/services/todoService'

interface FeatureProgressOverviewProps {
  feature: Feature
  todosByStatus: {
    new: Todo[]
    in_progress: Todo[]
    done: Todo[]
  }
}

export const FeatureProgressOverview = memo(function FeatureProgressOverview({ feature, todosByStatus }: FeatureProgressOverviewProps) {
  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Progress Overview</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-muted-foreground">Overall Progress</span>
              <span className="font-semibold text-base">{feature.progress_percentage ?? 0}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${feature.progress_percentage ?? 0}%` }}
              />
            </div>
          </div>
          <div className="grid grid-cols-5 gap-2">
            <div className="text-center">
              <div className="text-lg font-bold">{feature.total_todos ?? 0}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-muted-foreground">{todosByStatus.new.length}</div>
              <div className="text-xs text-muted-foreground">New</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-primary">{todosByStatus.in_progress.length}</div>
              <div className="text-xs text-muted-foreground">In Progress</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-success">{todosByStatus.done.length}</div>
              <div className="text-xs text-muted-foreground">Done</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-success">{feature.completed_todos ?? 0}</div>
              <div className="text-xs text-muted-foreground">Completed</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
