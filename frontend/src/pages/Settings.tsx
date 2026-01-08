import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthStore } from '@/stores/authStore'
import { mcpKeyService, type McpApiKey } from '@/services/mcpKeyService'
import { Settings as SettingsIcon, Key, Copy, CheckCircle2, RefreshCw, AlertCircle, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function Settings() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [mcpKey, setMcpKey] = useState<McpApiKey | null>(null)
  const [isLoadingKey, setIsLoadingKey] = useState(true)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [showNewKeyDialog, setShowNewKeyDialog] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [copiedConfig, setCopiedConfig] = useState(false)
  const [showCursorConfigDialog, setShowCursorConfigDialog] = useState(false)

  useEffect(() => {
    loadCurrentKey()
  }, [])

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

  const generateCursorConfig = (apiKey: string): string => {
    // Determine if we should use HTTP/SSE or stdio
    // For now, we'll provide both options
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
    const isProduction = apiBaseUrl.includes('intracker-api.kesmarki.com') || apiBaseUrl.includes('azure')
    
    if (isProduction) {
      // HTTP/SSE transport for production
      return JSON.stringify({
        mcpServers: {
          intracker: {
            url: `${apiBaseUrl}/mcp/sse`,
            headers: {
              "X-API-Key": apiKey
            }
          }
        }
      }, null, 2)
    } else {
      // stdio transport for local development
      // Note: This assumes the MCP server is in the same repo
      // Users may need to adjust the path
      return JSON.stringify({
        mcpServers: {
          intracker: {
            command: "python",
            args: ["-m", "src.mcp.server"],
            env: {
              "MCP_API_KEY": apiKey,
              "DATABASE_URL": "${DATABASE_URL}"
            }
          }
        }
      }, null, 2)
    }
  }

  const handleAddToCursor = async () => {
    if (!mcpKey) {
      // If no key exists, generate one first
      await handleRegenerateKey()
      return
    }

    // We need the plain text key, but we can't retrieve it
    // So we'll show instructions to generate a new key or use the existing one
    setShowCursorConfigDialog(true)
  }

  const handleCopyCursorConfig = async (apiKey: string) => {
    const config = generateCursorConfig(apiKey)
    await navigator.clipboard.writeText(config)
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
              Copy the configuration below and add it to your Cursor MCP settings.
              {newKey ? ' The API key is included in the configuration.' : ' You\'ll need to add your MCP API key manually.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Cursor MCP Configuration</Label>
              <div className="flex gap-2">
                <textarea
                  value={newKey ? generateCursorConfig(newKey) : (mcpKey ? '// Generate a new key to get the configuration' : '// No key available')}
                  readOnly
                  className="flex-1 font-mono text-xs p-3 bg-muted rounded-md min-h-[200px] resize-none"
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
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>How to add:</strong>
                <ol className="list-decimal list-inside mt-2 space-y-1 text-sm">
                  <li>Open Cursor Settings (Cmd/Ctrl + ,)</li>
                  <li>Go to "Features" → "Model Context Protocol"</li>
                  <li>Click "Edit Config" or open the MCP settings file</li>
                  <li>Paste the configuration above into the <code className="text-xs bg-muted px-1 py-0.5 rounded">mcpServers</code> section</li>
                  <li>Save and restart Cursor</li>
                </ol>
              </AlertDescription>
            </Alert>
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
