import { memo } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Lightbulb, ArrowRight, CheckCircle2, UsersRound } from 'lucide-react'
import type { Idea } from '@/services/ideaService'
import type { Team } from '@/services/adminService'

interface IdeaCardProps {
  idea: Idea
  teams?: Team[]
  onConvert?: (idea: Idea) => void
}

export const IdeaCard = memo(function IdeaCard({ idea, teams, onConvert }: IdeaCardProps) {
  const teamName = teams?.find(t => t.id === idea.team_id)?.name

  return (
    <Card className="hover:shadow-lg transition-shadow h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Lightbulb className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
              <CardTitle>{idea.title}</CardTitle>
            </div>
            {idea.description && (
              <CardDescription className="line-clamp-2 mt-2">
                {idea.description}
              </CardDescription>
            )}
          </div>
          <Badge 
            variant={
              idea.status === 'active' ? 'default' :
              idea.status === 'archived' ? 'secondary' : 'outline'
            }
          >
            {idea.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {idea.team_id && teamName && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <UsersRound className="h-3 w-3" />
              <span>{teamName}</span>
            </div>
          )}
          {idea.tags && idea.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {idea.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {idea.tags.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{idea.tags.length - 3}
                </Badge>
              )}
            </div>
          )}
          {idea.converted_to_project_id ? (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span>Converted to project</span>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => onConvert?.(idea)}
            >
              Convert to Project
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
})
