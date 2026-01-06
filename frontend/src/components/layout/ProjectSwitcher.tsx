import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface Project {
  id: string
  name: string
  description?: string
}

interface ProjectSwitcherProps {
  projects: Project[]
  currentProjectId?: string
  onProjectChange?: (projectId: string) => void
}

export function ProjectSwitcher({ 
  projects, 
  currentProjectId, 
  onProjectChange 
}: ProjectSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)
  const currentProject = projects.find(p => p.id === currentProjectId)

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full justify-between"
      >
        <span className="truncate">
          {currentProject?.name || 'Select project'}
        </span>
        <ChevronDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
      {isOpen && (
        <Card className="absolute top-full mt-2 w-full z-50">
          <CardHeader>
            <CardTitle>Switch Project</CardTitle>
            <CardDescription>Select a project to work on</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {projects.map((project) => (
              <Button
                key={project.id}
                variant={project.id === currentProjectId ? "default" : "ghost"}
                className="w-full justify-start"
                onClick={() => {
                  onProjectChange?.(project.id)
                  setIsOpen(false)
                }}
              >
                <div className="flex flex-col items-start">
                  <span className="font-medium">{project.name}</span>
                  {project.description && (
                    <span className="text-xs text-muted-foreground">
                      {project.description}
                    </span>
                  )}
                </div>
              </Button>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
