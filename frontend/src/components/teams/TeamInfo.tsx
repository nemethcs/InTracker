import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Edit } from 'lucide-react'
import type { Team } from '@/services/adminService'

interface TeamInfoProps {
  team: Team
  isTeamLeader: boolean
  onEdit: () => void
  onSetLanguage: (language: string) => void
}

export function TeamInfo({ team, isTeamLeader, onEdit, onSetLanguage }: TeamInfoProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Team Information</CardTitle>
            <CardDescription>{team.description || 'No description'}</CardDescription>
          </div>
          {isTeamLeader && (
            <Button
              variant="outline"
              size="sm"
              onClick={onEdit}
            >
              <Edit className="h-4 w-4 mr-1" />
              Edit
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Team Name</Label>
          <p className="text-sm font-medium">{team.name}</p>
        </div>
        <div>
          <Label>Language</Label>
          {team.language ? (
            <p className="text-sm font-medium">
              {team.language === 'hu' ? 'Hungarian (Magyar)' : team.language === 'en' ? 'English' : team.language}
            </p>
          ) : isTeamLeader ? (
            <div className="space-y-2">
              <Select
                value=""
                onValueChange={onSetLanguage}
              >
                <SelectTrigger className="w-full sm:w-[200px]">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hu">Hungarian (Magyar)</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Set the team language. This can only be set once and cannot be changed later.
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Not set</p>
          )}
        </div>
        <div>
          <Label>Created</Label>
          <p className="text-sm text-muted-foreground">
            {new Date(team.created_at).toLocaleDateString()}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
