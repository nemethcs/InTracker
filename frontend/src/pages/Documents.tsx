import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/EmptyState'
import { FileText } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'

export function Documents() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Documents"
        description="Project documentation and resources"
      />

      <EmptyState
        icon={<FileText className="h-12 w-12 text-muted-foreground" />}
        title="No documents yet"
        description="Documents will appear here when you create them in your projects"
      />
    </div>
  )
}
