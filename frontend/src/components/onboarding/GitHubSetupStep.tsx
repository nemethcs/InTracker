import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { settingsService, type GitHubOAuthStatus } from '@/services/settingsService'
import { useAuthStore } from '@/stores/authStore'
import { Github, CheckCircle2, AlertCircle, ArrowLeft, ArrowRight, X } from 'lucide-react'

interface GitHubSetupStepProps {
  onNext: () => void
  onBack: () => void
}

export function GitHubSetupStep({ onNext, onBack }: GitHubSetupStepProps) {
  const { user, checkAuth } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const [githubStatus, setGitHubStatus] = useState<GitHubOAuthStatus | null>(null)
  const [isLoadingGitHub, setIsLoadingGitHub] = useState(true)
  const [isConnectingGitHub, setIsConnectingGitHub] = useState(false)
  const [githubError, setGitHubError] = useState<string | null>(null)
  const [isProcessingCallback, setIsProcessingCallback] = useState(false)
  const processedOAuthStateRef = useRef<string | null>(null)

  useEffect(() => {
    loadGitHubStatus()
  }, [])

  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    if (error) {
      setGitHubError(error || 'GitHub OAuth authorization failed')
      searchParams.delete('error')
      searchParams.delete('error_description')
      setSearchParams(searchParams, { replace: true })
      return
    }

    if (!code || !state) {
      return
    }

    // Prevent duplicate processing
    if (processedOAuthStateRef.current === state) {
      return
    }
    processedOAuthStateRef.current = state

    const processCallback = async () => {
      if (isProcessingCallback) return

      try {
        setIsProcessingCallback(true)
        setGitHubError(null)
        await settingsService.handleOAuthCallback(code, state)
        await checkAuth()
        await loadGitHubStatus()
        searchParams.delete('code')
        searchParams.delete('state')
        setSearchParams(searchParams, { replace: true })
      } catch (error) {
        console.error('Failed to process OAuth callback:', error)
        setGitHubError(error instanceof Error ? error.message : 'Failed to connect GitHub account')
        searchParams.delete('code')
        searchParams.delete('state')
        setSearchParams(searchParams, { replace: true })
      } finally {
        setIsProcessingCallback(false)
      }
    }

    processCallback()
  }, [searchParams, checkAuth, isProcessingCallback])

  const loadGitHubStatus = async () => {
    try {
      setIsLoadingGitHub(true)
      setGitHubError(null)
      const status = await settingsService.getGitHubStatus()
      setGitHubStatus(status)
    } catch (error: any) {
      console.error('Failed to load GitHub status:', error)
      setGitHubError(error.response?.data?.detail || error.message || 'Failed to load GitHub status')
    } finally {
      setIsLoadingGitHub(false)
    }
  }

  const handleConnectGitHub = async () => {
    try {
      setIsConnectingGitHub(true)
      setGitHubError(null)
      const { authorization_url } = await settingsService.getGitHubOAuthUrl()
      window.location.href = authorization_url
    } catch (error: any) {
      console.error('Failed to get GitHub OAuth URL:', error)
      setGitHubError(
        error.message?.includes('not configured')
          ? 'GitHub OAuth is not configured on the server. Please contact your administrator.'
          : error.message || 'Failed to connect GitHub'
      )
      setIsConnectingGitHub(false)
    }
  }

  const isConnected = githubStatus?.connected || !!user?.github_connected_at
  const canProceed = isConnected

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">GitHub Integration</h2>
        <p className="text-muted-foreground">
          Connect your GitHub account to enable repository access and project management.
        </p>
      </div>

      {githubError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{githubError}</AlertDescription>
        </Alert>
      )}

      {isProcessingCallback ? (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center space-x-2">
              <LoadingSpinner />
              <span className="text-muted-foreground">Connecting GitHub account...</span>
            </div>
          </CardContent>
        </Card>
      ) : isLoadingGitHub ? (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center space-x-2">
              <LoadingSpinner />
              <span className="text-muted-foreground">Loading GitHub status...</span>
            </div>
          </CardContent>
        </Card>
      ) : isConnected ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              GitHub Connected
            </CardTitle>
            <CardDescription>
              Your GitHub account is successfully connected
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {githubStatus?.github_username && (
              <div className="flex items-center gap-3">
                {githubStatus.avatar_url && (
                  <img
                    src={githubStatus.avatar_url}
                    alt={githubStatus.github_username}
                    className="h-10 w-10 rounded-full"
                  />
                )}
                <div>
                  <p className="font-medium">@{githubStatus.github_username}</p>
                  {githubStatus.connected_at && (
                    <p className="text-sm text-muted-foreground">
                      Connected {new Date(githubStatus.connected_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            )}
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>
                ✅ GitHub integration is complete! You can proceed to the next step.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Github className="h-5 w-5" />
              Connect GitHub
            </CardTitle>
            <CardDescription>
              Click the button below to connect your GitHub account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={handleConnectGitHub}
              disabled={isConnectingGitHub}
              className="w-full"
              size="lg"
            >
              <Github className={`mr-2 h-4 w-4 ${isConnectingGitHub ? 'animate-spin' : ''}`} />
              {isConnectingGitHub ? 'Connecting...' : 'Connect with GitHub'}
            </Button>
          </CardContent>
        </Card>
      )}

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
