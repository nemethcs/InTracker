import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthStore } from '@/stores/authStore'
import { mcpKeyService, type McpApiKey } from '@/services/mcpKeyService'
import { settingsService, type GitHubOAuthStatus } from '@/services/settingsService'
import { Settings as SettingsIcon, Key, Copy, CheckCircle2, RefreshCw, AlertCircle, Plus, Github, X } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function Settings() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [mcpKey, setMcpKey] = useState<McpApiKey | null>(null)
  const [isLoadingKey, setIsLoadingKey] = useState(true)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [showNewKeyDialog, setShowNewKeyDialog] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [copiedConfig, setCopiedConfig] = useState(false)
  const [showCursorConfigDialog, setShowCursorConfigDialog] = useState(false)
  const [githubStatus, setGitHubStatus] = useState<GitHubOAuthStatus | null>(null)
  const [isLoadingGitHub, setIsLoadingGitHub] = useState(true)
  const [isConnectingGitHub, setIsConnectingGitHub] = useState(false)
  const [githubError, setGitHubError] = useState<string | null>(null)
  const [isProcessingCallback, setIsProcessingCallback] = useState(false)

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

    if (code && state) {
      // Process OAuth callback
      handleOAuthCallback(code, state)
    }
  }, [searchParams])

  useEffect(() => {
    loadCurrentKey()
    loadGitHubStatus()
  }, [])

  // Auto-open deeplink when newKey is set (after regeneration from Add to Cursor)
  useEffect(() => {
    if (newKey && showNewKeyDialog) {
      // Wait a bit for the dialog to show, then auto-open deeplink
      const timer = setTimeout(() => {
        const { deeplink } = generateCursorConfig(newKey)
        // Open deeplink directly - this will trigger Cursor to install
        window.location.href = deeplink
        // Also copy to clipboard as fallback
        navigator.clipboard.writeText(deeplink).catch(() => {
          // Ignore clipboard errors
        })
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [newKey, showNewKeyDialog])

  const loadCurrentKey = async () => {
    try {
      setIsLoadingKey(true)
      const key = await mcpKeyService.getCurrentKey()
      setMcpKey(key)
    } catch (error: any) {
      if (error.response?.status === 404) {
        // No key exists yet, that's okay
        setMcpKey(null)
      } else {
        console.error('Failed to load MCP key:', error)
      }
    } finally {
      setIsLoadingKey(false)
    }
  }

  const handleRegenerateKey = async () => {
    try {
      setIsRegenerating(true)
      const response = await mcpKeyService.regenerateKey()
      setNewKey(response.plain_text_key)
      setShowNewKeyDialog(true)
      await loadCurrentKey() // Reload to get the new key metadata
    } catch (error) {
      console.error('Failed to regenerate MCP key:', error)
      alert('Failed to regenerate MCP key. Please try again.')
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleCopyKey = async () => {
    if (newKey) {
      await navigator.clipboard.writeText(newKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getApiBaseUrl = (): string => {
    // Always use production URL for MCP configuration
    // Users can override locally if needed
    return import.meta.env.VITE_API_BASE_URL || 'https://intracker-api.kesmarki.com'
  }

  const generateCursorConfig = (apiKey: string): { config: string; deeplink: string } => {
    const apiBaseUrl = getApiBaseUrl()
    
    // Server configuration (what goes inside mcpServers)
    const serverConfig = {
      url: `${apiBaseUrl}/mcp/sse`,
      headers: {
        "X-API-Key": apiKey
      }
    }

    // Full config for manual copy (with mcpServers wrapper)
    const fullConfig = {
      mcpServers: {
        intracker: serverConfig
      }
    }

    const configJson = JSON.stringify(fullConfig, null, 2)
    
    // Generate Cursor deeplink for one-click install
    // Format: cursor://anysphere.cursor-deeplink/mcp/install?name=$NAME&config=$BASE64_ENCODED_CONFIG
    // IMPORTANT: Only encode the server config, NOT the mcpServers wrapper!
    // Cursor will automatically wrap it in mcpServers[name]
    const base64Config = btoa(JSON.stringify(serverConfig))
    const deeplink = `cursor://anysphere.cursor-deeplink/mcp/install?name=intracker&config=${base64Config}`

    return {
      config: configJson,
      deeplink
    }
  }

  const handleAddToCursor = async () => {
    // If no key exists, generate one first
    if (!mcpKey && !newKey) {
      await handleRegenerateKey()
      // After regeneration, the useEffect will auto-open the deeplink
      return
    }

    // If we have an active key but no newKey (plain text), we need to regenerate
    // to get the plain text key for the configuration
    if (mcpKey && !newKey) {
      const confirmed = window.confirm(
        "To add InTracker to Cursor, you need to regenerate your MCP API key. " +
        "This will revoke your current key. Continue?"
      )
      if (confirmed) {
        await handleRegenerateKey()
        // After regeneration, the useEffect will auto-open the deeplink
        return
      } else {
        return
      }
    }

    // If we have newKey, directly open the deeplink (quick install)
    if (newKey) {
      const { deeplink } = generateCursorConfig(newKey)
      // Open deeplink directly - this will trigger Cursor to install
      window.location.href = deeplink
      
      // Also copy to clipboard as fallback
      navigator.clipboard.writeText(deeplink).catch(() => {
        // Ignore clipboard errors
      })
    }
  }

  const handleCopyCursorConfig = async (apiKey: string) => {
    const { config } = generateCursorConfig(apiKey)
    await navigator.clipboard.writeText(config)
    setCopiedConfig(true)
    setTimeout(() => setCopiedConfig(false), 2000)
  }

  const handleCopyDeeplink = async (apiKey: string) => {
    const { deeplink } = generateCursorConfig(apiKey)
    await navigator.clipboard.writeText(deeplink)
    setCopiedConfig(true)
    setTimeout(() => setCopiedConfig(false), 2000)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

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

  const handleOAuthCallback = async (code: string, state: string) => {
    if (isProcessingCallback) {
      return // Prevent multiple calls
    }

    try {
      setIsProcessingCallback(true)
      setGitHubError(null)

      // Call backend to exchange code for tokens
      const result = await settingsService.handleOAuthCallback(code, state)

      // Remove callback params from URL
      searchParams.delete('code')
      searchParams.delete('state')
      setSearchParams(searchParams, { replace: true })

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Manage your account and preferences</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>Your account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {user && (
              <div className="space-y-2">
                <div>
                  <p className="text-sm font-medium">Email</p>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                </div>
                {user.name && (
                  <div>
                    <p className="text-sm font-medium">Name</p>
                    <p className="text-sm text-muted-foreground">{user.name}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
            <CardDescription>Account actions</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={handleLogout}>
              Logout
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* MCP API Key Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            MCP API Key
          </CardTitle>
          <CardDescription>
            Your MCP API key for connecting Cursor and other AI assistants to InTracker.
            You can only have one active key at a time.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingKey ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : mcpKey ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Key Status</Label>
                  <span className={`text-xs px-2 py-1 rounded ${
                    mcpKey.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {mcpKey.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                {mcpKey.name && (
                  <div>
                    <Label>Name</Label>
                    <p className="text-sm text-muted-foreground">{mcpKey.name}</p>
                  </div>
                )}
                <div>
                  <Label>Created</Label>
                  <p className="text-sm text-muted-foreground">{formatDate(mcpKey.created_at)}</p>
                </div>
                <div>
                  <Label>Last Used</Label>
                  <p className="text-sm text-muted-foreground">{formatDate(mcpKey.last_used_at)}</p>
                </div>
                {mcpKey.expires_at && (
                  <div>
                    <Label>Expires</Label>
                    <p className="text-sm text-muted-foreground">{formatDate(mcpKey.expires_at)}</p>
                  </div>
                )}
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  The API key value cannot be retrieved after creation. If you've lost your key,
                  regenerate a new one below.
                </AlertDescription>
              </Alert>

              <div className="flex gap-2">
                <Button
                  onClick={handleAddToCursor}
                  className="flex-1"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add to Cursor
                </Button>
                <Button
                  onClick={handleRegenerateKey}
                  disabled={isRegenerating}
                  variant="outline"
                  className="flex-1"
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${isRegenerating ? 'animate-spin' : ''}`} />
                  {isRegenerating ? 'Regenerating...' : 'Regenerate Key'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  You don't have an MCP API key yet. Generate one to connect Cursor and other AI assistants.
                </AlertDescription>
              </Alert>

              <Button
                onClick={handleRegenerateKey}
                disabled={isRegenerating}
                className="w-full"
              >
                <Key className={`mr-2 h-4 w-4 ${isRegenerating ? 'animate-spin' : ''}`} />
                {isRegenerating ? 'Generating...' : 'Generate MCP API Key'}
              </Button>
              {newKey && (
                <Button
                  onClick={() => {
                    handleCopyCursorConfig(newKey)
                    setShowCursorConfigDialog(true)
                  }}
                  className="w-full mt-2"
                  variant="outline"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add to Cursor
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* GitHub OAuth Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
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
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span className="ml-2 text-sm text-muted-foreground">Connecting GitHub account...</span>
            </div>
          ) : isLoadingGitHub ? (
            <div className="flex items-center justify-center py-4">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span className="ml-2 text-sm text-muted-foreground">Loading GitHub status...</span>
            </div>
          ) : githubStatus?.connected ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {githubStatus.avatar_url && (
                      <img
                        src={githubStatus.avatar_url}
                        alt={githubStatus.github_username}
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
                  <X className="h-4 w-4" />
                  Disconnect
                </Button>
              </div>

              {githubStatus.accessible_projects && githubStatus.accessible_projects.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Project Access Status</p>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {githubStatus.accessible_projects.map((project) => (
                      <div
                        key={project.project_id}
                        className={`flex items-center justify-between rounded border p-3 text-sm ${
                          project.has_access
                            ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950'
                            : 'border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950'
                        }`}
                      >
                        <div className="flex-1">
                          <p className="font-medium">{project.project_name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-xs text-muted-foreground">{project.team_name}</p>
                            {project.github_repo_url && (
                              <>
                                <span className="text-xs text-muted-foreground">•</span>
                                <a
                                  href={project.github_repo_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-blue-600 hover:underline dark:text-blue-400"
                                >
                                  GitHub
                                </a>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {project.has_access ? (
                            <span className="flex items-center gap-1 text-xs text-green-700 dark:text-green-400">
                              <CheckCircle2 className="h-4 w-4" />
                              {project.access_level || 'Access'}
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-xs text-red-700 dark:text-red-400">
                              <AlertCircle className="h-4 w-4" />
                              No access
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {githubStatus.accessible_projects.filter((p) => !p.has_access).length > 0 && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
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
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Github className="h-4 w-4" />
                    Connect with GitHub
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Key Dialog */}
      <Dialog open={showNewKeyDialog} onOpenChange={setShowNewKeyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Your New MCP API Key</DialogTitle>
            <DialogDescription>
              Copy this key now! You won't be able to see it again after closing this dialog.
              Set it as the <code className="text-xs bg-muted px-1 py-0.5 rounded">MCP_API_KEY</code> environment variable
              in your Cursor settings or MCP configuration.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>API Key</Label>
              <div className="flex gap-2">
                <Input
                  value={newKey || ''}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleCopyKey}
                  title="Copy to clipboard"
                >
                  {copied ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Important:</strong> Save this key securely. If you lose it, you'll need to regenerate a new one.
              </AlertDescription>
            </Alert>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowNewKeyDialog(false)}>
              I've Saved the Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cursor Configuration Dialog */}
      <Dialog open={showCursorConfigDialog} onOpenChange={setShowCursorConfigDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add InTracker to Cursor</DialogTitle>
            <DialogDescription>
              {newKey ? (
                <>Click the button below to automatically add InTracker to Cursor, or copy the configuration manually.</>
              ) : mcpKey ? (
                <>You have an active MCP API key, but the key value cannot be retrieved. Please regenerate your key to get the configuration.</>
              ) : (
                <>Generate a new MCP API key first to get the configuration.</>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {newKey && (
              <>
                {/* One-click install button */}
                <div className="space-y-2">
                  <Label>Quick Install (Recommended)</Label>
                  <div className="flex items-center gap-2">
                    <a
                      href={generateCursorConfig(newKey).deeplink}
                      className="flex-1"
                      onClick={(e) => {
                        // If deeplink doesn't work, fallback to copying
                        setTimeout(() => {
                          if (!copiedConfig) {
                            handleCopyDeeplink(newKey)
                          }
                        }, 100)
                      }}
                    >
                      <Button className="w-full" size="lg">
                        <Plus className="mr-2 h-4 w-4" />
                        Add to Cursor
                      </Button>
                    </a>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleCopyDeeplink(newKey)}
                      title="Copy install link"
                    >
                      {copiedConfig ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Click the button above to automatically install InTracker in Cursor. 
                    If it doesn't work, copy the link and paste it in your browser.
                  </p>
                </div>

                <div className="border-t pt-4">
                  <Label className="text-sm text-muted-foreground">Manual Configuration (Alternative)</Label>
                </div>
              </>
            )}

            {/* Manual configuration */}
            <div className="space-y-2">
              <Label>Cursor MCP Configuration (JSON)</Label>
              <div className="flex gap-2">
                <textarea
                  value={newKey ? generateCursorConfig(newKey).config : (mcpKey ? '// Generate a new key to get the configuration' : '// No key available')}
                  readOnly
                  className="flex-1 font-mono text-xs p-3 bg-muted rounded-md min-h-[150px] resize-none"
                  spellCheck={false}
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    if (newKey) {
                      handleCopyCursorConfig(newKey)
                    }
                  }}
                  title="Copy configuration to clipboard"
                  disabled={!newKey}
                >
                  {copiedConfig ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {newKey && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Manual installation:</strong>
                  <ol className="list-decimal list-inside mt-2 space-y-1 text-sm">
                    <li>Open Cursor Settings (Cmd/Ctrl + ,)</li>
                    <li>Go to "Features" → "Model Context Protocol"</li>
                    <li>Click "Edit Config" or open the MCP settings file</li>
                    <li>Paste the configuration above into the <code className="text-xs bg-muted px-1 py-0.5 rounded">mcpServers</code> section</li>
                    <li>Save and restart Cursor</li>
                  </ol>
                </AlertDescription>
              </Alert>
            )}
          </div>
          <DialogFooter>
            <Button onClick={() => setShowCursorConfigDialog(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
