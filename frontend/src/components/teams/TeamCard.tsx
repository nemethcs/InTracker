import { Card, CardContent } from '@/components/ui/card'
import { UsersRound } from 'lucide-react'
import type { Team } from '@/services/adminService'

interface TeamCardProps {
  team: Team
  isSelected: boolean
  onClick: () => void
}

export function TeamCard({ team, isSelected, onClick }: TeamCardProps) {
  return (
    <Card
      className={`cursor-pointer transition-colors ${
        isSelected ? 'border-primary bg-accent' : ''
      }`}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="font-semibold">{team.name}</h3>
            {team.description && (
              <p className="text-sm text-muted-foreground mt-1">{team.description}</p>
            )}
          </div>
          <UsersRound className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  )
}
