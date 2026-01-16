import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Github, RefreshCw, AlertCircle, X, CheckCircle2 } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import { settingsService, type GitHubOAuthStatus } from '@/services/settingsService'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function GitHubSettings() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [githubStatus, setGitHubStatus] = useState<GitHubOAuthStatus | null>(null)
  const [isLoadingGitHub, setIsLoadingGitHub] = useState(true)
  const [isConnectingGitHub, setIsConnectingGitHub] = useState(false)
  const [githubError, setGitHubError] = useState<string | null>(null)
  const [isProcessingCallback, setIsProcessingCallback] = useState(false)
  // Guard against React StrictMode / double-invoked effects (dev) processing the same callback twice
  const processedOAuthStateRef = useRef<string | null>(null)

  useEffect(() => {
    loadGitHubStatus()
  }, [])

  const loadGitHubStatus = async () => {
    try {
      setIsLoadingGitHub(true)
      setGitHubError(null)
      const status = await settingsService.getGitHubStatus()
      setGitHubStatus(status)
    } catch (error) {
      console.error('Failed to load GitHub status:', error)
      setGitHubError(error instanceof Error ? error.message : 'Failed to load GitHub status')
      setGitHubStatus({
        connected: false,
        accessible_projects: [],
      })
    } finally {
      setIsLoadingGitHub(false)
    }
  }

  const handleConnectGitHub = async () => {
    try {
      setIsConnectingGitHub(true)
      setGitHubError(null)
      const { authorization_url } = await settingsService.getGitHubOAuthUrl()
      // Redirect to GitHub OAuth authorization page
      window.location.href = authorization_url
    } catch (error) {
      console.error('Failed to get GitHub OAuth URL:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to connect GitHub'
      setGitHubError(
        errorMessage.includes('not configured')
          ? 'GitHub OAuth is not configured on the server. Please contact your administrator or see the setup documentation.'
          : errorMessage
      )
      setIsConnectingGitHub(false)
    }
  }

  const handleDisconnectGitHub = async () => {
    try {
      setGitHubError(null)
      await settingsService.disconnectGitHub()
      await loadGitHubStatus() // Reload status after disconnect
    } catch (error) {
      console.error('Failed to disconnect GitHub:', error)
      setGitHubError(error instanceof Error ? error.message : 'Failed to disconnect GitHub')
    }
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  // Handle OAuth callback from GitHub
  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')
    const errorDescription = searchParams.get('error_description')

    if (error) {
      // GitHub OAuth error
      setGitHubError(errorDescription || error || 'GitHub OAuth authorization failed')
      // Remove error params from URL
      searchParams.delete('error')
      searchParams.delete('error_description')
      setSearchParams(searchParams, { replace: true })
      return
    }

    // Only process callback if we have both code and state
    // This prevents the callback from running when the page first loads
    if (!code || !state) {
      return // Don't process if code or state is missing
    }

    // Prevent processing the same state twice (can happen in dev StrictMode)
    if (processedOAuthStateRef.current === state) {
      return
    }
    processedOAuthStateRef.current = state

    // Process OAuth callback
    const processCallback = async () => {
      if (isProcessingCallback) {
        return // Prevent multiple calls
      }

      try {
        setIsProcessingCallback(true)
        setGitHubError(null)

        // Check if this callback is for onboarding flow
        // If redirect_path is /onboarding, let onboarding handle the callback
        // We need to check the redirect_path from Redis, but we can infer it from the state
        // For now, check if user is in onboarding flow
        // IMPORTANT: Admins should NEVER be redirected to onboarding, even if setup_completed is false
        const currentUserBeforeCallback = useAuthStore.getState().user
        const isAdmin = currentUserBeforeCallback?.role === 'admin'
        const isOnboardingFlow = currentUserBeforeCallback && !currentUserBeforeCallback.setup_completed && !isAdmin
        
        if (isOnboardingFlow) {
          // User is in onboarding flow (and not admin), redirect to onboarding with query params
          // Let onboarding handle the callback
          navigate(`/onboarding?code=${code}&state=${state}`, { replace: true })
          return
        }
        
        // Call backend to exchange code for tokens (only for settings page)
        const result = await settingsService.handleOAuthCallback(code, state)

        // Remove callback params from URL
        searchParams.delete('code')
        searchParams.delete('state')
        setSearchParams(searchParams, { replace: true })

        // Refresh user data to get updated GitHub info
        const { checkAuth } = useAuthStore.getState()
        await checkAuth()
        
        // Wait a moment for state to update, then check if setup is completed
        // The backend automatically updates setup_completed when both MCP key and GitHub are connected
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // Check multiple times to ensure state has updated
        let attempts = 0
        let currentUser = useAuthStore.getState().user
        while (currentUser && !currentUser.setup_completed && attempts < 3) {
          await new Promise(resolve => setTimeout(resolve, 200))
          await checkAuth()
          currentUser = useAuthStore.getState().user
          attempts++
        }
        
        // Use redirect_path from backend if available
        if (result.redirect_path && result.redirect_path !== '/settings') {
          // Backend specified a redirect path (e.g., /onboarding)
          navigate(result.redirect_path, { replace: true })
          return
        }

        // Reload GitHub status to show updated connection
        await loadGitHubStatus()

        // Show success message (optional - could use a toast notification)
        console.log('GitHub OAuth connection successful:', result.message)
      } catch (error) {
        console.error('Failed to process OAuth callback:', error)
        setGitHubError(error instanceof Error ? error.message : 'Failed to connect GitHub account')
        
        // Remove callback params from URL even on error
        searchParams.delete('code')
        searchParams.delete('state')
        setSearchParams(searchParams, { replace: true })
      } finally {
        setIsProcessingCallback(false)
      }
    }

    processCallback()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get('code'), searchParams.get('state')]) // Only depend on code and state values

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Github className={iconSize('md')} />
          GitHub Integration
        </CardTitle>
        <CardDescription>
          Connect your GitHub account to access repositories and manage projects
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {githubError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{githubError}</AlertDescription>
          </Alert>
        )}

        {isProcessingCallback ? (
          <div className="flex items-center justify-center py-4">
            <RefreshCw className={`${iconSize('sm')} animate-spin`} />
            <span className="ml-2 text-sm text-muted-foreground">Connecting GitHub account...</span>
          </div>
        ) : isLoadingGitHub ? (
          <div className="flex items-center justify-center py-4">
            <RefreshCw className={`${iconSize('sm')} animate-spin`} />
            <span className="ml-2 text-sm text-muted-foreground">Loading GitHub status...</span>
          </div>
        ) : githubStatus?.connected ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  {githubStatus.avatar_url && (
                    <OptimizedImage
                      src={githubStatus.avatar_url}
                      alt={githubStatus.github_username}
                      lazy={true}
                      className="h-8 w-8 rounded-full"
                    />
                  )}
                  <div>
                    <p className="text-sm font-medium">
                      Connected as {githubStatus.github_username}
                    </p>
                    {githubStatus.connected_at && (
                      <p className="text-xs text-muted-foreground">
                        Connected {formatDate(githubStatus.connected_at)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDisconnectGitHub}
                className="flex items-center gap-2"
              >
                <X className={iconSize('sm')} />
                Disconnect
              </Button>
            </div>

            {githubStatus.accessible_projects && githubStatus.accessible_projects.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Project Access Status</p>
                <div className="rounded-md border max-h-64 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Project</TableHead>
                        <TableHead>Team</TableHead>
                        <TableHead>Repository</TableHead>
                        <TableHead className="text-right">Access</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {githubStatus.accessible_projects.map((project) => (
                        <TableRow key={project.project_id}>
                          <TableCell className="font-medium">{project.project_name}</TableCell>
                          <TableCell className="text-muted-foreground">{project.team_name}</TableCell>
                          <TableCell>
                            {project.github_repo_url ? (
                              <a
                                href={project.github_repo_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-primary hover:underline"
                              >
                                GitHub
                              </a>
                            ) : (
                              <span className="text-xs text-muted-foreground">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            {project.has_access ? (
                              <span className="flex items-center justify-end gap-1 text-xs text-success">
                                <CheckCircle2 className={iconSize('sm')} />
                                {project.access_level || 'Access'}
                              </span>
                            ) : (
                              <span className="flex items-center justify-end gap-1 text-xs text-destructive">
                                <AlertCircle className={iconSize('sm')} />
                                No access
                              </span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                {githubStatus.accessible_projects.filter((p) => !p.has_access).length > 0 && (
                  <Alert>
                    <AlertCircle className={iconSize('sm')} />
                    <AlertDescription className="text-xs">
                      Some projects show "No access" because your GitHub token doesn't have
                      permission to access their repositories. You may need to grant additional
                      permissions or request access to those repositories.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Connect your GitHub account to enable repository access and project management.
            </p>
            <Button
              onClick={handleConnectGitHub}
              disabled={isConnectingGitHub}
              className="flex items-center gap-2"
            >
              {isConnectingGitHub ? (
                <>
                  <RefreshCw className={`${iconSize('sm')} animate-spin`} />
                  Connecting...
                </>
              ) : (
                <>
                  <Github className={iconSize('sm')} />
                  Connect with GitHub
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
