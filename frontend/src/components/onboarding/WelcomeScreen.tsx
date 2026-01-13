import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FolderKanban, Sparkles, CheckSquare, Bot, Github, ArrowRight } from 'lucide-react'

interface WelcomeScreenProps {
  onNext: () => void
}

export function WelcomeScreen({ onNext }: WelcomeScreenProps) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Mi az InTracker?</h2>
        <p className="text-muted-foreground">
          Az InTracker egy intelligens projektmenedzsment eszköz, amely segít a Cursor AI-val
          nagy projekteket hatékonyan kezelni és követni.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <FolderKanban className="h-8 w-8 mb-2 text-primary" />
            <CardTitle>Projects</CardTitle>
            <CardDescription>Organize your work</CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <Sparkles className="h-8 w-8 mb-2 text-primary" />
            <CardTitle>Features</CardTitle>
            <CardDescription>Group related tasks</CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CheckSquare className="h-8 w-8 mb-2 text-primary" />
            <CardTitle>Todos</CardTitle>
            <CardDescription>Track progress</CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <Bot className="h-8 w-8 mb-2 text-primary" />
            <CardTitle>MCP</CardTitle>
            <CardDescription>Cursor AI integration</CardDescription>
          </CardHeader>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <Github className="h-8 w-8 mb-2 text-primary" />
            <CardTitle>GitHub</CardTitle>
            <CardDescription>Version control sync</CardDescription>
          </CardHeader>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button onClick={onNext} size="lg">
          Start Setup
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
