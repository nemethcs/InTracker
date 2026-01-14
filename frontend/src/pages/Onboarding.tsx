import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/authStore'
import { ProgressBar } from '@/components/ui/progress-bar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { ArrowLeft, ArrowRight } from 'lucide-react'

// Step components (will be created separately)
import { WelcomeScreen } from '@/components/onboarding/WelcomeScreen'
import { TeamSetupStep } from '@/components/onboarding/TeamSetupStep'
import { McpSetupStep } from '@/components/onboarding/McpSetupStep'
import { GitHubSetupStep } from '@/components/onboarding/GitHubSetupStep'
import { CompletionStep } from '@/components/onboarding/CompletionStep'

const TOTAL_STEPS = 5

export function Onboarding() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { checkAuth } = useAuthStore()
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(true)

  // Load user's onboarding progress on mount
  useEffect(() => {
    const loadProgress = async () => {
      try {
        await checkAuth()
        const currentUser = useAuthStore.getState().user
        // Restore step from user's onboarding_step
        if (currentUser?.onboarding_step) {
          // Map backend step (0-5) to frontend step (1-5)
          // 0=not_started -> 1, 1=welcome -> 1, 2=team_setup -> 2, 3=mcp_key -> 3, 4=mcp_verified -> 3, 5=github -> 4, 6=complete -> 5
          const stepMap: Record<number, number> = {
            0: 1, // not_started -> Welcome
            1: 1, // welcome -> Welcome
            2: 2, // team_setup -> Team Setup (for team leaders)
            3: 3, // mcp_key -> MCP Setup
            4: 3, // mcp_verified -> MCP Setup (waiting for verify)
            5: 4, // github -> GitHub Setup
            6: 5, // complete -> Completion
          }
          const restoredStep = stepMap[currentUser.onboarding_step] || 1
          setCurrentStep(restoredStep)
        }
      } catch (error) {
        console.error('Failed to load onboarding progress:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadProgress()
  }, [checkAuth])

  // Redirect if setup is already completed
  useEffect(() => {
    const checkAndRedirect = () => {
      const currentUser = useAuthStore.getState().user
      if (currentUser?.setup_completed) {
        navigate('/')
      }
    }
    
    // Check immediately
    checkAndRedirect()
    
    // Also subscribe to store changes
    const unsubscribe = useAuthStore.subscribe((state) => {
      if (state.user?.setup_completed) {
        navigate('/')
      }
    })
    
    return unsubscribe
  }, [navigate])

  const handleNext = () => {
    if (currentStep < TOTAL_STEPS) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Welcome to InTracker</CardTitle>
          <CardDescription>Let's get you set up in just a few steps</CardDescription>
          <div className="mt-4">
            <ProgressBar currentStep={currentStep} totalSteps={TOTAL_STEPS} />
          </div>
        </CardHeader>
        <CardContent>
          {/* Step content */}
          {currentStep === 1 && <WelcomeScreen onNext={handleNext} />}
          {currentStep === 2 && <TeamSetupStep onNext={handleNext} onBack={handleBack} />}
          {currentStep === 3 && <McpSetupStep onNext={handleNext} onBack={handleBack} />}
          {currentStep === 4 && <GitHubSetupStep onNext={handleNext} onBack={handleBack} />}
          {currentStep === 5 && <CompletionStep onComplete={() => navigate('/')} onBack={handleBack} />}
        </CardContent>
      </Card>
    </div>
  )
}
