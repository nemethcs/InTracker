import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle2, ArrowLeft, Sparkles } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

interface CompletionStepProps {
  onComplete: () => void
  onBack: () => void
}

export function CompletionStep({ onComplete, onBack }: CompletionStepProps) {
  const { checkAuth } = useAuthStore()
  const [isCompleting, setIsCompleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleComplete = async () => {
    try {
      setIsCompleting(true)
      setError(null)
      
      // Refresh user data to get updated setup_completed status
      // The backend automatically updates setup_completed when both MCP key and GitHub are connected
      await checkAuth()
      
      // Wait a moment for state to update, then check if setup is completed
      const currentUser = useAuthStore.getState().user
      if (currentUser?.setup_completed) {
        // Setup is completed, navigate to dashboard
        onComplete()
      } else {
        // Setup not completed yet, show error
        setError('Setup is not yet complete. Please ensure both MCP key and GitHub are connected.')
        setIsCompleting(false)
      }
    } catch (err) {
      console.error('Failed to complete setup:', err)
      setError(err instanceof Error ? err.message : 'Failed to complete setup')
      setIsCompleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <div className="rounded-full bg-green-100 dark:bg-green-900 p-4">
            <CheckCircle2 className="h-12 w-12 text-green-600 dark:text-green-400" />
          </div>
        </div>
        <h2 className="text-3xl font-bold">Setup Complete! 🎉</h2>
        <p className="text-muted-foreground text-lg">
          You're all set to start using InTracker with Cursor AI
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What's Next?</CardTitle>
          <CardDescription>
            Here's what you've configured and what you can do now
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="font-medium">MCP Integration</span>
            </div>
            <p className="text-sm text-muted-foreground ml-7">
              Cursor AI is connected and can access your InTracker projects
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="font-medium">GitHub Integration</span>
            </div>
            <p className="text-sm text-muted-foreground ml-7">
              Your GitHub repositories are linked for version control sync
            </p>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button onClick={handleComplete} disabled={isCompleting} size="lg" className="min-w-[150px]">
          {isCompleting ? (
            <>
              <Sparkles className="mr-2 h-4 w-4 animate-spin" />
              Completing...
            </>
          ) : (
            <>
              Go to Dashboard
              <Sparkles className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
