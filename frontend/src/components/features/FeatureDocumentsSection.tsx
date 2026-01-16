import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, FileText } from 'lucide-react'
import type { Document } from '@/services/documentService'

interface FeatureDocumentsSectionProps {
  documents: Document[]
  isLoading: boolean
  onCreateDocument: () => void
  onEditDocument: (document: Document) => void
}

export function FeatureDocumentsSection({
  documents,
  isLoading,
  onCreateDocument,
  onEditDocument,
}: FeatureDocumentsSectionProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h2 className="text-xl sm:text-2xl font-bold">Documents</h2>
        <Button onClick={onCreateDocument}>
          <Plus className="mr-2 h-4 w-4" />
          New Document
        </Button>
      </div>
      {isLoading ? (
        <LoadingState variant="combined" size="md" skeletonCount={3} />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-12 w-12 text-muted-foreground" />}
          title="No documents yet"
          description="Create your first document for this feature"
          variant="compact"
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {documents.map((document) => {
            const preview = document.content
              ? document.content
                  .replace(/[#*_`\[\]]/g, '')
                  .replace(/\n/g, ' ')
                  .trim()
                  .substring(0, 200)
              : 'No content'

            return (
              <Card
                key={document.id}
                className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => onEditDocument(document)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="mb-1">{document.title}</CardTitle>
                      <CardDescription className="line-clamp-1">
                        {document.type.replace('_', ' ')}
                      </CardDescription>
                    </div>
                    <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm text-muted-foreground line-clamp-3 min-h-[3.5rem]">
                      {preview}
                      {document.content && document.content.length > 200 && '...'}
                    </div>
                    <div className="flex items-center justify-between text-sm pt-2 border-t">
                      <Badge variant="outline" className="capitalize text-xs">
                        {document.type.replace('_', ' ')}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        v{document.version}
                      </span>
                    </div>
                    {document.tags && document.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {document.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 text-xs bg-secondary rounded-md"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
