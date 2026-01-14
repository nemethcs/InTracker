import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { adminService, type Team } from '@/services/adminService'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/hooks/useToast'
import { UsersRound, CheckCircle2, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface TeamSetupStepProps {
  onNext: () => void
  onBack: () => void
}

export function TeamSetupStep({ onNext, onBack }: TeamSetupStepProps) {
  const { user, checkAuth } = useAuthStore()
  const toast = useToast()
  const [team, setTeam] = useState<Team | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [teamName, setTeamName] = useState('')
  const [teamLanguage, setTeamLanguage] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadUserTeam()
  }, [user])

  const loadUserTeam = async () => {
    if (!user || user.role !== 'team_leader') {
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      const response = await adminService.getTeams()
      // Find team created by this user
      const userTeam = response.teams.find(t => t.created_by === user.id)
      if (userTeam) {
        setTeam(userTeam)
        setTeamName(userTeam.name)
        setTeamLanguage(userTeam.language || '')
      }
    } catch (err) {
      console.error('Failed to load team:', err)
      setError('Failed to load team information')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!team) return

    try {
      setIsSaving(true)
      setError(null)

      // Update team name if changed
      if (teamName.trim() && teamName.trim() !== team.name) {
        await adminService.updateTeam(team.id, { name: teamName.trim() })
      }

      // Set team language if not already set
      if (teamLanguage && !team.language) {
        await adminService.setTeamLanguage(team.id, teamLanguage)
      }

      // Refresh team data
      await loadUserTeam()
      await checkAuth()

      // Clear teamLanguage state after saving (it's now in team.language)
      setTeamLanguage('')

      toast.success('Team settings saved', 'Your team name and language have been saved successfully.')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save team settings'
      setError(errorMessage)
      toast.error('Failed to save team settings', errorMessage)
    } finally {
      setIsSaving(false)
    }
  }

  // Can proceed only if team exists and language is set (either already set or just saved)
  // Language must be set before proceeding
  const canProceed = team !== null && team.language !== null

  // If user is not team_leader or doesn't have a team, skip this step
  if (!user || user.role !== 'team_leader' || isLoading) {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <LoadingSpinner size="lg" />
        </div>
      )
    }
    // Skip this step if not team leader
    return (
      <div className="space-y-4">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            This step is only for team leaders. Proceeding to next step...
          </AlertDescription>
        </Alert>
        <div className="flex justify-end">
          <Button onClick={onNext} size="lg">
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  if (!team) {
    return (
      <div className="space-y-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No team found. Please contact support.
          </AlertDescription>
        </Alert>
        <div className="flex justify-end">
          <Button onClick={onNext} size="lg">
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">Team Setup</h2>
        <p className="text-muted-foreground">
          Configure your team name and language. The language can only be set once.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UsersRound className="h-5 w-5" />
            Team Configuration
          </CardTitle>
          <CardDescription>
            Set up your team name and language preference
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="team-name">Team Name (Optional)</Label>
            <Input
              id="team-name"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              placeholder="Enter team name"
            />
            <p className="text-xs text-muted-foreground">
              You can change your team name later if needed.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="team-language">Team Language *</Label>
            <Select
              value={team.language || teamLanguage}
              onValueChange={setTeamLanguage}
              disabled={!!team.language}
            >
              <SelectTrigger id="team-language">
                <SelectValue placeholder="Select language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hu">Hungarian (Magyar)</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
            {team.language ? (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  Language is already set to <strong>{team.language === 'hu' ? 'Hungarian' : 'English'}</strong> and cannot be changed.
                </AlertDescription>
              </Alert>
            ) : (
              <p className="text-xs text-muted-foreground">
                This can only be set once. Choose carefully!
              </p>
            )}
          </div>

          {!team.language && (
            <>
              {teamLanguage ? (
                <Button
                  onClick={handleSave}
                  disabled={isSaving || !teamLanguage}
                  className="w-full"
                  size="lg"
                >
                  {isSaving ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Save Team Settings
                    </>
                  )}
                </Button>
              ) : (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Please select a team language to continue. This can only be set once.
                  </AlertDescription>
                </Alert>
              )}
            </>
          )}
          
          {team.language && (
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>
                Team language is set to <strong>{team.language === 'hu' ? 'Hungarian' : 'English'}</strong>. You can proceed to the next step.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button onClick={onNext} disabled={!canProceed} size="lg">
          Next
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
