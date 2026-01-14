import { useState, useEffect } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export function Register() {
  const navigate = useNavigate()
  const { register, isAuthenticated } = useAuth()
  const [searchParams] = useSearchParams()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [invitationCode, setInvitationCode] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load invitation code and email from URL query parameters
  useEffect(() => {
    const code = searchParams.get('code')
    if (code) {
      setInvitationCode(code)
    }
    
    const emailParam = searchParams.get('email')
    if (emailParam) {
      setEmail(emailParam)
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      // Clear any existing tokens before registration to avoid conflicts
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      await register(email, password, name || undefined, invitationCode)
      
      // Verify that the user state is set correctly
      const currentUser = useAuthStore.getState().user
      if (!currentUser) {
        throw new Error('Registration succeeded but user state was not set')
      }
      
      // Use window.location.href for a full page reload to ensure all state is properly initialized
      // This is necessary because the ProtectedRoute and useAuth hook might not have updated yet
      window.location.href = '/onboarding'
    } catch (err: any) {
      // Handle different error formats
      let errorMessage = 'Registration failed'
      if (err instanceof Error) {
        errorMessage = err.message
      } else if (err?.response?.data?.detail) {
        // FastAPI validation error format
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail
        } else if (Array.isArray(err.response.data.detail)) {
          // Pydantic validation errors
          errorMessage = err.response.data.detail.map((e: any) => {
            if (typeof e === 'string') return e
            return `${e.loc?.join('.')}: ${e.msg || e.message || 'Invalid value'}`
          }).join(', ')
        } else if (typeof err.response.data.detail === 'object') {
          errorMessage = JSON.stringify(err.response.data.detail)
        }
      } else if (err?.message) {
        errorMessage = err.message
      }
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Register</CardTitle>
          <CardDescription>Create a new account to get started</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="name">Name (optional)</Label>
              <Input
                id="name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invitationCode">Invitation Code</Label>
              <Input
                id="invitationCode"
                type="text"
                placeholder="Enter your invitation code"
                value={invitationCode}
                onChange={(e) => setInvitationCode(e.target.value)}
                required
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                You need an invitation code to register. Contact your administrator or team leader.
              </p>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? <LoadingSpinner className="mr-2" /> : null}
              Register
            </Button>
            <div className="text-sm text-center text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:underline">
                Login
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
