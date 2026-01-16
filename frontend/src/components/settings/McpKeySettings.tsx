import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Key, Copy, CheckCircle2, RefreshCw, AlertCircle, Plus } from 'lucide-react'
import { iconSize } from '@/components/ui/Icon'
import { mcpKeyService, type McpApiKey } from '@/services/mcpKeyService'
import { toast } from '@/hooks/useToast'

export function McpKeySettings() {
  const [mcpKey, setMcpKey] = useState<McpApiKey | null>(null)
  const [isLoadingKey, setIsLoadingKey] = useState(true)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [showNewKeyDialog, setShowNewKeyDialog] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadCurrentKey()
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
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
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
      toast.error('Failed to regenerate MCP key', 'Please try again.')
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

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className={iconSize('md')} />
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
                  <Badge variant={mcpKey.is_active ? 'success' : 'muted'}>
                    {mcpKey.is_active ? 'Active' : 'Inactive'}
                  </Badge>
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
                <AlertCircle className={iconSize('sm')} />
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
                  <Plus className={`mr-2 ${iconSize('sm')}`} />
                  Add to Cursor
                </Button>
                <Button
                  onClick={handleRegenerateKey}
                  disabled={isRegenerating}
                  variant="outline"
                  className="flex-1"
                >
                  <RefreshCw className={`mr-2 ${iconSize('sm')} ${isRegenerating ? 'animate-spin' : ''}`} />
                  {isRegenerating ? 'Regenerating...' : 'Regenerate Key'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <Alert>
                <AlertCircle className={iconSize('sm')} />
                <AlertDescription>
                  You don't have an MCP API key yet. Generate one to connect Cursor and other AI assistants.
                </AlertDescription>
              </Alert>

              <Button
                onClick={handleRegenerateKey}
                disabled={isRegenerating}
                className="w-full"
              >
                <Key className={`mr-2 ${iconSize('sm')} ${isRegenerating ? 'animate-spin' : ''}`} />
                {isRegenerating ? 'Generating...' : 'Generate MCP API Key'}
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
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={handleCopyKey}
                        aria-label={copied ? "MCP key copied" : "Copy MCP key"}
                      >
                        {copied ? (
                          <CheckCircle2 className={`${iconSize('sm')} text-success`} />
                        ) : (
                          <Copy className={iconSize('sm')} />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Copy to clipboard</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
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
    </>
  )
}
