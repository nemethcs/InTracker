import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { mcpKeyService, type McpApiKey } from '@/services/mcpKeyService'
import { signalrService } from '@/services/signalrService'
import { useAuthStore } from '@/stores/authStore'
import { Key, CheckCircle2, AlertCircle, ArrowLeft, ArrowRight, ExternalLink } from 'lucide-react'

interface McpSetupStepProps {
  onNext: () => void
  onBack: () => void
}

export function McpSetupStep({ onNext, onBack }: McpSetupStepProps) {
  const { user, checkAuth } = useAuthStore()
  const [mcpKey, setMcpKey] = useState<McpApiKey | null>(null)
  const [isLoadingKey, setIsLoadingKey] = useState(true)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isVerified, setIsVerified] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load existing MCP key
  useEffect(() => {
    loadCurrentKey()
  }, [])

  // Check if already verified
  useEffect(() => {
    if (user?.mcp_verified_at) {
      setIsVerified(true)
    }
  }, [user?.mcp_verified_at])

  // Listen for SignalR mcpVerified event
  useEffect(() => {
    const handleMcpVerified = async (data: { user_id: string; verified_at: string }) => {
      // Check if this event is for the current user
      if (data.user_id === user?.id) {
        setIsVerified(true)
        // Refresh user data to get updated mcp_verified_at
        await checkAuth()
      }
    }

    signalrService.on('mcpVerified', handleMcpVerified)

    return () => {
      signalrService.off('mcpVerified', handleMcpVerified)
    }
  }, [user?.id, checkAuth])

  const loadCurrentKey = async () => {
    try {
      setIsLoadingKey(true)
      const key = await mcpKeyService.getCurrentKey()
      setMcpKey(key)
    } catch (error: any) {
      if (error.response?.status === 404) {
        setMcpKey(null)
      } else {
        console.error('Failed to load MCP key:', error)
        setError('Failed to load MCP key')
      }
    } finally {
      setIsLoadingKey(false)
    }
  }

  const handleGenerateKey = async () => {
    try {
      setIsGenerating(true)
      setError(null)
      const response = await mcpKeyService.regenerateKey()
      setNewKey(response.plain_text_key)
      setMcpKey(response.key)
    } catch (error) {
      console.error('Failed to generate MCP key:', error)
      setError('Failed to generate MCP key. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const getApiBaseUrl = (): string => {
    return import.meta.env.VITE_API_BASE_URL || 'https://intracker-api.kesmarki.com'
  }

  const generateCursorMcpDeeplink = (apiKey: string): string => {
    const apiBaseUrl = getApiBaseUrl()
    const serverConfig = {
      url: `${apiBaseUrl}/mcp/sse`,
      headers: {
        "X-API-Key": apiKey
      }
    }
    const base64Config = btoa(JSON.stringify(serverConfig))
    return `cursor://anysphere.cursor-deeplink/mcp/install?name=intracker&config=${base64Config}`
  }

  const generateCursorVerifyPromptDeeplink = (): string => {
    const promptText = "Use the mcp_verify_connection tool"
    return `cursor://anysphere.cursor-deeplink/prompt?text=${encodeURIComponent(promptText)}`
  }

  const handleAddToCursor = () => {
    if (!newKey && !mcpKey) {
      // Generate key first
      handleGenerateKey()
      return
    }

    const apiKey = newKey || (mcpKey ? 'existing' : null)
    if (!apiKey) {
      setError('Please generate an MCP key first')
      return
    }

    // If we have a key but not newKey (plain text), we need to regenerate
    if (mcpKey && !newKey) {
      handleGenerateKey()
      return
    }

    if (newKey) {
      const deeplink = generateCursorMcpDeeplink(newKey)
      window.location.href = deeplink
    }
  }

  const handleVerifyConnection = () => {
    const verifyDeeplink = generateCursorVerifyPromptDeeplink()
    window.location.href = verifyDeeplink
  }

  const canProceed = isVerified && (mcpKey !== null || newKey !== null)

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">MCP Setup</h2>
        <p className="text-muted-foreground">
          Connect InTracker to Cursor AI by generating an MCP API key and adding it to Cursor.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Step 1: Generate MCP Key */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Step 1: Generate MCP API Key
          </CardTitle>
          <CardDescription>
            Generate a unique API key for Cursor to connect to InTracker
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingKey ? (
            <LoadingSpinner />
          ) : mcpKey || newKey ? (
            <div className="space-y-2">
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  MCP API Key generated successfully!
                </AlertDescription>
              </Alert>
              <Button onClick={handleAddToCursor} className="w-full" size="lg">
                <ExternalLink className="mr-2 h-4 w-4" />
                Add to Cursor
              </Button>
            </div>
          ) : (
            <Button onClick={handleGenerateKey} disabled={isGenerating} className="w-full" size="lg">
              {isGenerating ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Key className="mr-2 h-4 w-4" />
                  Generate MCP API Key
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Step 2: Verify Connection */}
      {(mcpKey || newKey) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {isVerified ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5" />
              )}
              Step 2: Verify Connection
            </CardTitle>
            <CardDescription>
              Verify that Cursor is connected and can communicate with InTracker
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isVerified ? (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  ✅ MCP connection verified successfully! You can proceed to the next step.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    After adding MCP to Cursor, click the button below to verify the connection.
                    This will open Cursor with a pre-filled prompt for the agent.
                  </AlertDescription>
                </Alert>
                <Button onClick={handleVerifyConnection} className="w-full" size="lg" variant="outline">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Verify Connection in Cursor
                </Button>
                <p className="text-sm text-muted-foreground text-center">
                  Waiting for verification... The page will update automatically when verified.
                </p>
              </div>
            )}
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
