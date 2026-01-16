import { Card, CardContent } from '@/components/ui/card'
import { TeamCard } from './TeamCard'
import type { Team } from '@/services/adminService'

interface TeamsListProps {
  teams: Team[]
  selectedTeam: Team | null
  onSelectTeam: (team: Team) => void
}

export function TeamsList({ teams, selectedTeam, onSelectTeam }: TeamsListProps) {
  if (teams.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-muted-foreground">
          No teams found
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-2">
      {teams.map((team) => (
        <TeamCard
          key={team.id}
          team={team}
          isSelected={selectedTeam?.id === team.id}
          onClick={() => onSelectTeam(team)}
        />
      ))}
    </div>
  )
}
