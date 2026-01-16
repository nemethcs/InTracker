import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { CheckSquare, Package, Link2, ExternalLink } from 'lucide-react'
import { elementService, type Element } from '@/services/elementService'
import { todoService, type Todo } from '@/services/todoService'
import { Link } from 'react-router-dom'

interface ElementDependency {
  id: string
  dependency_type: string
  depends_on_element_id: string
}

interface ElementDetails extends Element {
  dependencies?: ElementDependency[]
}

interface ElementDetailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  element: Element | null
  projectId?: string
}

export function ElementDetailDialog({ open, onOpenChange, element, projectId }: ElementDetailDialogProps) {
  const [elementDetails, setElementDetails] = useState<ElementDetails | null>(null)
  const [todos, setTodos] = useState<Todo[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (open && element) {
      setIsLoading(true)
      // Get full element details with todos
      elementService.getElement(element.id)
        .then((details) => {
          setElementDetails(details)
          // Get todos for this element
          return todoService.listTodos(undefined, element.id)
        })
        .then((elementTodos) => {
          setTodos(elementTodos)
          setIsLoading(false)
        })
        .catch((error) => {
          console.error('Failed to load element details:', error)
          setIsLoading(false)
        })
    } else {
      setElementDetails(null)
      setTodos([])
    }
  }, [open, element])

  if (!element) return null

  const statusColors = {
    new: 'bg-muted text-muted-foreground',
    in_progress: 'bg-primary/10 text-primary dark:bg-primary/20',
    tested: 'bg-accent/20 text-accent-foreground dark:bg-accent/30',
    done: 'bg-primary/20 text-primary dark:bg-primary/30',
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {element.title}
            <Badge variant="outline" className="capitalize">
              {element.type}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            {element.description || 'No description'}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status and Metadata */}
            <div className="flex items-center gap-4">
              <Badge
                variant={
                  element.status === 'done' ? 'default' :
                  element.status === 'tested' ? 'secondary' :
                  element.status === 'in_progress' ? 'secondary' : 'outline'
                }
                className="capitalize"
              >
                {element.status.replace('_', ' ')}
              </Badge>
              {element.todos_count !== undefined && element.todos_count > 0 && (
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <CheckSquare className="h-4 w-4" />
                  <span>{element.todos_done_count || 0} / {element.todos_count} todos</span>
                </div>
              )}
              {element.features_count !== undefined && element.features_count > 0 && (
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Package className="h-4 w-4" />
                  <span>{element.features_count} feature{element.features_count !== 1 ? 's' : ''}</span>
                </div>
              )}
            </div>

            {/* Linked Features */}
            {element.linked_features && element.linked_features.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <Link2 className="h-4 w-4" />
                  Linked Features
                </h3>
                <div className="flex flex-wrap gap-2">
                  {element.linked_features.map((featureName, index) => (
                    <Badge key={index} variant="secondary">
                      {featureName}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Todos */}
            {todos.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <CheckSquare className="h-4 w-4" />
                  Todos ({todos.length})
                </h3>
                <div className="space-y-2">
                  {todos.map((todo) => (
                    <div
                      key={todo.id}
                      className="flex items-start justify-between p-2 rounded-md border hover:bg-accent"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{todo.title}</span>
                          <Badge
                            variant={
                              todo.status === 'done' ? 'default' :
                              todo.status === 'tested' ? 'secondary' :
                              todo.status === 'in_progress' ? 'secondary' : 'outline'
                            }
                            className="text-xs capitalize"
                          >
                            {todo.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        {todo.description && (
                          <p className="text-xs text-muted-foreground mt-1">{todo.description}</p>
                        )}
                      </div>
                      {todo.feature_id && projectId && (
                        <Link to={`/projects/${projectId}/features/${todo.feature_id}`}>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-6"
                            aria-label={`View feature for todo: ${todo.title}`}
                          >
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </Link>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Dependencies */}
            {elementDetails?.dependencies && elementDetails.dependencies.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Dependencies</h3>
                <div className="space-y-1">
                  {elementDetails.dependencies.map((dep: ElementDependency) => (
                    <div key={dep.id} className="text-sm text-muted-foreground">
                      {dep.dependency_type}: {dep.depends_on_element_id}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* GitHub Issue */}
            {element.github_issue_url && (
              <div>
                <a
                  href={element.github_issue_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline flex items-center gap-1"
                >
                  <ExternalLink className="h-3 w-3" />
                  GitHub Issue #{element.github_issue_number}
                </a>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
