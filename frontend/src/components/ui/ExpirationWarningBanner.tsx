import { useState, useEffect, useMemo } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertTriangle, X, RefreshCw } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { settingsService } from '@/services/settingsService'
import { useNavigate } from 'react-router-dom'
import { iconSize } from './Icon'

const DISMISSED_BANNER_KEY = 'github_token_expiration_banner_dismissed'
const WARNING_THRESHOLD_DAYS = 7

export function ExpirationWarningBanner() {
  const { user, checkAuth } = useAuthStore()
  const navigate = useNavigate()
  const [dismissed, setDismissed] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)

  useEffect(() => {
    // Check if banner was dismissed
    const dismissedValue = localStorage.getItem(DISMISSED_BANNER_KEY)
    if (dismissedValue === 'true') {
      setDismissed(true)
    }
  }, [])

  const shouldShowBanner = useMemo(() => {
    if (!user?.github_token_expires_at || dismissed) {
      return false
    }

    const expirationDate = new Date(user.github_token_expires_at)
    const now = new Date()
    const daysUntilExpiration = Math.ceil(
      (expirationDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    )

    return daysUntilExpiration > 0 && daysUntilExpiration <= WARNING_THRESHOLD_DAYS
  }, [user?.github_token_expires_at, dismissed])

  const timeRemaining = useMemo(() => {
    if (!user?.github_token_expires_at) return null

    const expirationDate = new Date(user.github_token_expires_at)
    const now = new Date()
    const diffMs = expirationDate.getTime() - now.getTime()
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))

    if (days > 0) {
      return `${days} day${days !== 1 ? 's' : ''}`
    } else if (hours > 0) {
      return `${hours} hour${hours !== 1 ? 's' : ''}`
    } else if (minutes > 0) {
      return `${minutes} minute${minutes !== 1 ? 's' : ''}`
    } else {
      return 'less than a minute'
    }
  }, [user?.github_token_expires_at])

  const handleDismiss = () => {
    localStorage.setItem(DISMISSED_BANNER_KEY, 'true')
    setDismissed(true)
  }

  const handleReconnect = async () => {
    try {
      setIsReconnecting(true)
      // Navigate to settings page and trigger GitHub OAuth flow
      navigate('/settings?tab=github')
      // The Settings page will handle the OAuth flow
    } catch (error) {
      console.error('Failed to reconnect GitHub:', error)
    } finally {
      setIsReconnecting(false)
    }
  }

  if (!shouldShowBanner) {
    return null
  }

  return (
    <Alert className="border-warning bg-warning/10 mb-4">
      <AlertTriangle className={`${iconSize('md')} text-warning`} />
      <AlertDescription className="flex items-center justify-between gap-4">
        <div className="flex-1">
          <p className="font-medium text-warning">
            GitHub token expires soon
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Your GitHub token will expire in {timeRemaining}. Please reconnect to continue using GitHub features.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReconnect}
            disabled={isReconnecting}
            className="border-warning text-warning hover:bg-warning/20"
          >
            {isReconnecting ? (
              <>
                <RefreshCw className={`${iconSize('sm')} mr-2 animate-spin`} />
                Reconnecting...
              </>
            ) : (
              <>
                <RefreshCw className={`${iconSize('sm')} mr-2`} />
                Reconnect
              </>
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className={iconSize('sm')} />
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
}
