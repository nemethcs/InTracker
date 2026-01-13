import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from '@/hooks/useToast'
import { adminService, type Team } from '@/services/adminService'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { Project, ProjectCreate, ProjectUpdate } from '@/services/projectService'

interface ProjectEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  project?: Project | null
  onSave: (data: ProjectCreate | ProjectUpdate) => Promise<void>
}

export function ProjectEditor({
  open,
  onOpenChange,
  project,
  onSave,
}: ProjectEditorProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<Project['status']>('active')
  const [teamId, setTeamId] = useState('')
  const [tags, setTags] = useState('')
  const [technologyTags, setTechnologyTags] = useState('')
  const [cursorInstructions, setCursorInstructions] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoadingTeams, setIsLoadingTeams] = useState(false)

  useEffect(() => {
    if (open) {
      // Load teams when dialog opens
      loadTeams()
    }
    
    if (project) {
      setName(project.name)
      setDescription(project.description || '')
      setStatus(project.status)
      setTeamId(project.team_id)
      setTags(project.tags?.join(', ') || '')
      setTechnologyTags(project.technology_tags?.join(', ') || '')
      setCursorInstructions(project.cursor_instructions || '')
    } else {
      setName('')
      setDescription('')
      setStatus('active')
      setTeamId('')
      setTags('')
      setTechnologyTags('')
      setCursorInstructions('')
    }
  }, [project, open])

  const loadTeams = async () => {
    setIsLoadingTeams(true)
    try {
      const response = await adminService.getTeams()
      setTeams(response.teams)
      // If no team selected and teams exist, select first team
      if (!teamId && response.teams.length > 0) {
        setTeamId(response.teams[0].id)
      }
    } catch (error) {
      console.error('Failed to load teams:', error)
    } finally {
      setIsLoadingTeams(false)
    }
  }

  const handleSave = async () => {
    if (!name.trim()) {
      return
    }

    setIsSaving(true)
    try {
      const tagsArray = tags.split(',').map(t => t.trim()).filter(t => t.length > 0)
      const technologyTagsArray = technologyTags.split(',').map(t => t.trim()).filter(t => t.length > 0)

      if (!teamId && !project) {
        toast.warning('Team required', 'Please select a team before creating a project.')
        return
      }

      if (project) {
        // Update existing project
        await onSave({
          name,
          description: description || undefined,
          status,
          tags: tagsArray.length > 0 ? tagsArray : undefined,
          technology_tags: technologyTagsArray.length > 0 ? technologyTagsArray : undefined,
          cursor_instructions: cursorInstructions || undefined,
        } as ProjectUpdate)
      } else {
        // Create new project
        await onSave({
          name,
          team_id: teamId,
          description: description || undefined,
          tags: tagsArray.length > 0 ? tagsArray : undefined,
          technology_tags: technologyTagsArray.length > 0 ? technologyTagsArray : undefined,
          cursor_instructions: cursorInstructions || undefined,
        } as ProjectCreate)
      }
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save project:', error)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{project ? 'Edit Project' : 'Create Project'}</DialogTitle>
          <DialogDescription>
            {project ? 'Update the project details' : 'Create a new project to organize your work'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {!project && (
            <div className="space-y-2">
              <Label htmlFor="team">Team *</Label>
              {isLoadingTeams ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Select value={teamId} onValueChange={setTeamId}>
                  <SelectTrigger id="team">
                    <SelectValue placeholder="Select a team" />
                  </SelectTrigger>
                  <SelectContent>
                    {teams.map((team) => (
                      <SelectItem key={team.id} value={team.id}>
                        {team.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter project name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter project description"
              rows={3}
            />
          </div>
          {project && (
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={(value) => setStatus(value as Project['status'])}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                  <SelectItem value="blocked">Blocked</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Enter tags separated by commas (e.g., ai, project-management, mcp)"
            />
            <p className="text-xs text-muted-foreground">Separate multiple tags with commas</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="technologyTags">Technology Tags</Label>
            <Input
              id="technologyTags"
              value={technologyTags}
              onChange={(e) => setTechnologyTags(e.target.value)}
              placeholder="Enter technology tags separated by commas (e.g., react, typescript, python)"
            />
            <p className="text-xs text-muted-foreground">Separate multiple tags with commas</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="cursorInstructions">Cursor Instructions</Label>
            <Textarea
              id="cursorInstructions"
              value={cursorInstructions}
              onChange={(e) => setCursorInstructions(e.target.value)}
              placeholder="Enter specific instructions for AI assistants working on this project"
              rows={4}
            />
            <p className="text-xs text-muted-foreground">Optional instructions for AI context</p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || !name.trim() || (!project && !teamId)}>
            {isSaving ? 'Saving...' : project ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
