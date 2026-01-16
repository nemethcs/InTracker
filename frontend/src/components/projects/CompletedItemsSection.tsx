import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { CheckCircle2, FolderKanban, CheckSquare } from 'lucide-react'
import { format } from 'date-fns'
import { iconSize } from '@/components/ui/Icon'
import type { Feature } from '@/services/featureService'
import type { Todo } from '@/services/todoService'

interface CompletedItemsSectionProps {
  projectId: string
  completedFeatures: Feature[]
  completedTodos: Array<Todo & { featureName?: string }>
}

export function CompletedItemsSection({
  projectId,
  completedFeatures,
  completedTodos,
}: CompletedItemsSectionProps) {
  if (completedFeatures.length === 0 && completedTodos.length === 0) {
    return null
  }

  return (
    <div className="mt-8">
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="completed-items">
          <AccordionTrigger className="text-xl sm:text-2xl font-bold">
            <div className="flex items-center gap-2">
              <CheckCircle2 className={iconSize('md')} />
              <span>Completed Items</span>
              <Badge variant="secondary" className="text-xs">
                {completedFeatures.length + completedTodos.length} {completedFeatures.length + completedTodos.length === 1 ? 'item' : 'items'}
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-6 pt-4">
              {/* Completed Features */}
              {completedFeatures.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <FolderKanban className="h-5 w-5" />
                    Completed Features ({completedFeatures.length})
                  </h3>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {completedFeatures.map((feature) => (
                      <Link key={feature.id} to={`/projects/${projectId}/features/${feature.id}`}>
                        <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                          <CardHeader>
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <CardTitle className="mb-1 line-clamp-2">{feature.name}</CardTitle>
                                <CardDescription className="line-clamp-2">
                                  {feature.description || 'No description'}
                                </CardDescription>
                              </div>
                              <Badge
                                variant={
                                  feature.status === 'merged' ? 'default' :
                                  feature.status === 'tested' ? 'secondary' :
                                  'outline'
                                }
                                className="ml-2 flex-shrink-0"
                              >
                                {feature.status}
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">
                                {format(new Date(feature.updated_at), 'MMM d, yyyy')}
                              </span>
                              {feature.progress_percentage !== undefined && (
                                <span className="text-muted-foreground">
                                  {feature.progress_percentage}% complete
                                </span>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Completed Todos */}
              {completedTodos.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <CheckSquare className="h-5 w-5" />
                    Completed Todos ({completedTodos.length})
                  </h3>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {completedTodos.map((todo) => (
                      <Card key={todo.id} className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="mb-1 line-clamp-2">{todo.title}</CardTitle>
                              {todo.description && (
                                <CardDescription className="line-clamp-2">
                                  {todo.description}
                                </CardDescription>
                              )}
                            </div>
                            <Badge variant="outline" className="ml-2 flex-shrink-0">
                              done
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            {todo.featureName && (
                              <div className="flex items-center gap-2 text-sm">
                                <FolderKanban className="h-4 w-4 text-muted-foreground" />
                                <Link
                                  to={`/projects/${projectId}/features/${todo.feature_id}`}
                                  className="text-primary hover:underline"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {todo.featureName}
                                </Link>
                              </div>
                            )}
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">
                                {format(new Date(todo.completed_at || todo.updated_at), 'MMM d, yyyy')}
                              </span>
                              {todo.priority && (
                                <Badge variant="outline" className="text-xs capitalize">
                                  {todo.priority}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  )
}
