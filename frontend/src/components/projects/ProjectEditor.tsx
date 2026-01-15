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
import { FormField, FormInput, FormTextarea, FormSelect } from '@/components/ui/form'
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
import { githubService, type GitHubRepository } from '@/services/githubService'
import { Github } from 'lucide-react'

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
  const [showGitHubImport, setShowGitHubImport] = useState(false)
  const [githubRepos, setGithubRepos] = useState<GitHubRepository[]>([])
  const [selectedRepo, setSelectedRepo] = useState<string>('')
  const [isLoadingRepos, setIsLoadingRepos] = useState(false)
  const [isGeneratingDeeplink, setIsGeneratingDeeplink] = useState(false)

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
      setShowGitHubImport(false)
      setSelectedRepo('')
    } else {
      setName('')
      setDescription('')
      setStatus('active')
      setTeamId('')
      setTags('')
      setTechnologyTags('')
      setCursorInstructions('')
      setShowGitHubImport(false)
      setSelectedRepo('')
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

  const loadGitHubRepos = async () => {
    setIsLoadingRepos(true)
    try {
      const repos = await githubService.listRepositories()
      setGithubRepos(repos)
    } catch (error: any) {
      console.error('Failed to load GitHub repositories:', error)
      toast.error(
        'Failed to load repositories',
        error.response?.data?.detail || 'Please connect your GitHub account in Settings.'
      )
    } finally {
      setIsLoadingRepos(false)
    }
  }

  const handleGitHubImportClick = async () => {
    if (!showGitHubImport) {
      setShowGitHubImport(true)
      if (githubRepos.length === 0) {
        await loadGitHubRepos()
      }
    } else {
      setShowGitHubImport(false)
    }
  }

  const handleGenerateDeeplink = async () => {
    if (!selectedRepo) {
      toast.warning('No repository selected', 'Please select a GitHub repository first.')
      return
    }

    setIsGeneratingDeeplink(true)
    try {
      const repo = githubRepos.find(r => r.full_name === selectedRepo)
      if (!repo) {
        toast.error('Repository not found', 'Selected repository not found in list.')
        return
      }

      const response = await githubService.generateCursorDeeplink(repo.url)
      
      // Open the deeplink
      window.open(response.deeplink, '_blank')
      
      toast.success(
        'Cursor deeplink generated',
        `Opening Cursor chat with import instructions for ${repo.full_name}`
      )
      
      // Close the dialog
      onOpenChange(false)
    } catch (error: any) {
      console.error('Failed to generate deeplink:', error)
      toast.error(
        'Failed to generate deeplink',
        error.response?.data?.detail || 'Please try again later.'
      )
    } finally {
      setIsGeneratingDeeplink(false)
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
            <>
              <FormField label="Team" required>
                {isLoadingTeams ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Select value={teamId} onValueChange={setTeamId}>
                    <FormSelect>
                      <SelectValue placeholder="Select a team" />
                    </FormSelect>
                    <SelectContent>
                      {teams.map((team) => (
                        <SelectItem key={team.id} value={team.id}>
                          {team.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </FormField>
              
              <div className="flex items-center gap-2 py-2">
                <div className="flex-1 border-t"></div>
                <span className="text-sm text-muted-foreground">or</span>
                <div className="flex-1 border-t"></div>
              </div>
              
              <Button
                type="button"
                variant="outline"
                onClick={handleGitHubImportClick}
                className="w-full"
              >
                <Github className="mr-2 h-4 w-4" />
                {showGitHubImport ? 'Cancel GitHub Import' : 'Import from GitHub'}
              </Button>
              
              {showGitHubImport && (
                <div className="space-y-2 p-4 border rounded-lg bg-muted/50">
                  <FormField label="Select GitHub Repository">
                    {isLoadingRepos ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <Select value={selectedRepo} onValueChange={setSelectedRepo}>
                        <FormSelect>
                          <SelectValue placeholder="Select a repository" />
                        </FormSelect>
                        <SelectContent>
                          {githubRepos.map((repo) => (
                            <SelectItem key={repo.id} value={repo.full_name}>
                              <div className="flex flex-col">
                                <span className="font-medium">{repo.name}</span>
                                <span className="text-xs text-muted-foreground">{repo.full_name}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </FormField>
                  
                  {selectedRepo && (
                    <Button
                      type="button"
                      onClick={handleGenerateDeeplink}
                      disabled={isGeneratingDeeplink}
                      className="w-full"
                    >
                      {isGeneratingDeeplink ? 'Generating...' : 'Generate Cursor Deeplink'}
                    </Button>
                  )}
                </div>
              )}
            </>
          )}
          <FormField label="Name" required>
            <FormInput
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter project name"
            />
          </FormField>
          <FormField label="Description">
            <FormTextarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter project description"
              rows={3}
            />
          </FormField>
          {project && (
            <FormField label="Status">
              <Select value={status} onValueChange={(value) => setStatus(value as Project['status'])}>
                <FormSelect>
                  <SelectValue />
                </FormSelect>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                  <SelectItem value="blocked">Blocked</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </FormField>
          )}
          <FormField 
            label="Tags" 
            description="Separate multiple tags with commas"
          >
            <FormInput
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Enter tags separated by commas (e.g., ai, project-management, mcp)"
            />
          </FormField>
          <FormField 
            label="Technology Tags" 
            description="Separate multiple tags with commas"
          >
            <FormInput
              value={technologyTags}
              onChange={(e) => setTechnologyTags(e.target.value)}
              placeholder="Enter technology tags separated by commas (e.g., react, typescript, python)"
            />
          </FormField>
          <FormField 
            label="Cursor Instructions" 
            description="Optional instructions for AI context"
          >
            <FormTextarea
              value={cursorInstructions}
              onChange={(e) => setCursorInstructions(e.target.value)}
              placeholder="Enter specific instructions for AI assistants working on this project"
              rows={4}
            />
          </FormField>
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
