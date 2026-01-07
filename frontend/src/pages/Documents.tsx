import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/EmptyState'
import { FileText } from 'lucide-react'

export function Documents() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="text-muted-foreground">Project documentation and resources</p>
      </div>

      <EmptyState
        icon={<FileText className="h-12 w-12 text-muted-foreground" />}
        title="No documents yet"
        description="Documents will appear here when you create them in your projects"
      />
    </div>
  )
}
