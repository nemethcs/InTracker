import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Info, ExternalLink, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import api from '@/services/api'

interface VersionInfo {
  version: string
  latestVersion?: string
  updateAvailable?: boolean
  releaseNotes?: string
}

const FRONTEND_VERSION = '0.1.0' // Update this when releasing new versions

export function VersionInfo() {
  const [backendVersion, setBackendVersion] = useState<string>('0.1.0')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Fetch backend version
    api
      .get('/api')
      .then((response) => {
        if (response.data?.version) {
          setBackendVersion(response.data.version)
        }
      })
      .catch(() => {
        // If API call fails, use default version
        setBackendVersion('0.1.0')
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  return (
    <div className="mt-auto border-t pt-4 px-4 pb-4 space-y-3">
      {/* Settings Link */}
      <Link to="/settings">
        <Button
          variant="ghost"
          className="w-full justify-start text-muted-foreground hover:text-foreground"
        >
          <Settings className="h-4 w-4 mr-2" />
          Settings
        </Button>
      </Link>

      {/* Version Info */}
      <div className="space-y-2">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2 text-xs text-muted-foreground cursor-help">
                <Info className="h-3 w-3" />
                <span>InTracker v{FRONTEND_VERSION}</span>
              </div>
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-xs">
              <div className="space-y-1">
                <p className="font-semibold">Version Information</p>
                <p>Frontend: v{FRONTEND_VERSION}</p>
                <p>Backend: v{backendVersion}</p>
                {isLoading && <p className="text-xs italic">Loading...</p>}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Update Information */}
        <div className="text-xs text-muted-foreground space-y-1">
          <p>Check for updates and release notes:</p>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs p-1 w-full justify-start"
            asChild
          >
            <a
              href="https://github.com/nemethcs/InTracker/releases"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1"
            >
              <ExternalLink className="h-3 w-3" />
              Release Notes
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}
