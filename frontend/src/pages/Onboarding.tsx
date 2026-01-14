import { useState, useEffect, useRef } from 'react'
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

const TOTAL_STEPS_TEAM_LEADER = 5
const TOTAL_STEPS_MEMBER = 4

export function Onboarding() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { checkAuth } = useAuthStore()
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(true)

  // Calculate total steps based on user role
  const totalSteps = user?.role === 'team_leader' ? TOTAL_STEPS_TEAM_LEADER : TOTAL_STEPS_MEMBER

  // Track if we've already loaded progress to prevent re-loading on every checkAuth call
  const hasLoadedProgressRef = useRef(false)

  // Load user's onboarding progress on mount
  useEffect(() => {
    const loadProgress = async () => {
      // Only load progress once on mount, not on every checkAuth call
      if (hasLoadedProgressRef.current) {
        return
      }

      try {
        await checkAuth()
        const currentUser = useAuthStore.getState().user
        // Restore step from user's onboarding_step
        if (currentUser?.onboarding_step) {
          // Map backend step (0-5) to frontend step (1-5)
          // Backend: 0=not_started, 1=welcome, 2=mcp_key, 3=mcp_verified, 4=github, 5=complete
          // Frontend steps depend on user role:
          //   Team leader: 1=Welcome, 2=Team Setup, 3=MCP Setup, 4=GitHub Setup, 5=Completion
          //   Member: 1=Welcome, 2=MCP Setup (Team Setup skipped), 3=GitHub Setup, 4=Completion
          const isTeamLeader = currentUser.role === 'team_leader'
          
          if (isTeamLeader) {
            // Team leader flow: Team Setup is step 2
            const stepMap: Record<number, number> = {
              0: 1, // not_started -> Welcome
              1: 1, // welcome -> Welcome
              2: 3, // mcp_key -> MCP Setup (step 3)
              3: 3, // mcp_verified -> MCP Setup (step 3, waiting for verify)
              4: 4, // github -> GitHub Setup (step 4)
              5: 5, // complete -> Completion (step 5)
            }
            const restoredStep = stepMap[currentUser.onboarding_step] || 1
            setCurrentStep(restoredStep)
          } else {
            // Member flow: Team Setup is skipped, so steps are shifted
            const stepMap: Record<number, number> = {
              0: 1, // not_started -> Welcome
              1: 1, // welcome -> Welcome
              2: 2, // mcp_key -> MCP Setup (step 2, no Team Setup)
              3: 2, // mcp_verified -> MCP Setup (step 2, waiting for verify)
              4: 3, // github -> GitHub Setup (step 3, no Team Setup)
              5: 4, // complete -> Completion (step 4, no Team Setup)
            }
            const restoredStep = stepMap[currentUser.onboarding_step] || 1
            setCurrentStep(restoredStep)
          }
        }
        hasLoadedProgressRef.current = true
      } catch (error) {
        console.error('Failed to load onboarding progress:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadProgress()
  }, [checkAuth])

  // Redirect if setup is already completed (but only if not actively in onboarding flow)
  useEffect(() => {
    const checkAndRedirect = () => {
      const currentUser = useAuthStore.getState().user
      // Only redirect if setup is completed AND user is not on the last step (completion step)
      // This allows user to complete the onboarding flow even if setup_completed is true
      const currentTotalSteps = currentUser?.role === 'team_leader' ? TOTAL_STEPS_TEAM_LEADER : TOTAL_STEPS_MEMBER
      if (currentUser?.setup_completed && currentStep !== currentTotalSteps) {
        // Only redirect if user is not actively progressing through onboarding
        // Check if user is on completion step - if so, let them finish
        if (currentStep < currentTotalSteps) {
          // User completed setup but hasn't reached completion step yet
          // This can happen if they manually navigate back or if setup_completed was set externally
          // In this case, we should still allow them to continue to completion step
          // So we don't redirect, just update the step to completion
          if (currentUser.onboarding_step === 5) {
            setCurrentStep(currentTotalSteps)
          }
        }
      }
    }
    
    // Check immediately
    checkAndRedirect()
    
    // Also subscribe to store changes, but be more careful about redirects
    const unsubscribe = useAuthStore.subscribe((state) => {
      // Only redirect if setup is completed AND we're not on the completion step
      // This prevents redirecting while user is actively completing onboarding
      const currentTotalSteps = state.user?.role === 'team_leader' ? TOTAL_STEPS_TEAM_LEADER : TOTAL_STEPS_MEMBER
      if (state.user?.setup_completed && currentStep < currentTotalSteps) {
        // If onboarding_step is 5 (complete), move to completion step instead of redirecting
        if (state.user.onboarding_step === 5) {
          setCurrentStep(currentTotalSteps)
        }
      }
    })
    
    return unsubscribe
  }, [navigate, currentStep])

  const handleNext = () => {
    if (currentStep < totalSteps) {
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
            <ProgressBar currentStep={currentStep} totalSteps={totalSteps} />
          </div>
        </CardHeader>
        <CardContent>
          {/* Step content */}
          {/* Step mapping depends on user role:
              Team leader: 1=Welcome, 2=Team Setup, 3=MCP Setup, 4=GitHub Setup, 5=Completion
              Member: 1=Welcome, 2=MCP Setup (Team Setup skipped), 3=GitHub Setup, 4=Completion */}
          {currentStep === 1 && <WelcomeScreen onNext={handleNext} />}
          {currentStep === 2 && (
            user?.role === 'team_leader' ? (
              <TeamSetupStep onNext={handleNext} onBack={handleBack} />
            ) : (
              <McpSetupStep onNext={handleNext} onBack={handleBack} />
            )
          )}
          {currentStep === 3 && (
            user?.role === 'team_leader' ? (
              <McpSetupStep onNext={handleNext} onBack={handleBack} />
            ) : (
              <GitHubSetupStep onNext={handleNext} onBack={handleBack} />
            )
          )}
          {currentStep === 4 && (
            user?.role === 'team_leader' ? (
              <GitHubSetupStep onNext={handleNext} onBack={handleBack} />
            ) : (
              <CompletionStep onComplete={() => navigate('/')} onBack={handleBack} />
            )
          )}
          {currentStep === 5 && user?.role === 'team_leader' && (
            <CompletionStep onComplete={() => navigate('/')} onBack={handleBack} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
