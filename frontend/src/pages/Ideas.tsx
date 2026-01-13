import { useState, useEffect } from 'react'
import { useIdeas } from '@/hooks/useIdeas'
import { useIdeaStore } from '@/stores/ideaStore'
import { useProjectStore } from '@/stores/projectStore'
import { adminService, type Team } from '@/services/adminService'
import { signalrService } from '@/services/signalrService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { IdeaCard } from '@/components/ideas/IdeaCard'
import { IdeaEditor } from '@/components/ideas/IdeaEditor'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Lightbulb, Plus, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Idea, IdeaConvertRequest } from '@/services/ideaService'
import { PageHeader } from '@/components/layout/PageHeader'
import { toast } from '@/hooks/useToast'

export function Ideas() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [selectedTeamId, setSelectedTeamId] = useState<string | undefined>(undefined)
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoadingTeams, setIsLoadingTeams] = useState(false)
  const { ideas, isLoading, error, refetch } = useIdeas(statusFilter, selectedTeamId)
  const { createIdea, updateIdea, deleteIdea, convertIdeaToProject } = useIdeaStore()
  const { createProject } = useProjectStore()
  const [ideaEditorOpen, setIdeaEditorOpen] = useState(false)
  const [editingIdea, setEditingIdea] = useState<Idea | null>(null)
  const [convertDialogOpen, setConvertDialogOpen] = useState(false)
  const [ideaToConvert, setIdeaToConvert] = useState<Idea | null>(null)
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const [isConverting, setIsConverting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadTeams()
  }, [])

  // Subscribe to SignalR real-time updates for ideas
  useEffect(() => {
    const { fetchIdeaSilently } = useIdeaStore.getState()
    
    const handleIdeaUpdate = (data: { ideaId: string; teamId: string; changes: any }) => {
      const { ideas } = useIdeaStore.getState()
      
      // Handle different update actions efficiently without triggering loading states
      if (data.changes?.action === 'created') {
        // New idea created - fetch it silently if not already in store
        const existingIndex = ideas.findIndex(i => i.id === data.ideaId)
        if (existingIndex === -1) {
          // Idea not in store, fetch it silently (without loading state)
          fetchIdeaSilently(data.ideaId).catch(error => {
            console.error('Failed to fetch new idea:', error)
          })
        }
      } else if (data.changes?.action === 'deleted') {
        // Idea deleted - remove from local state
        useIdeaStore.setState({ 
          ideas: ideas.filter(i => i.id !== data.ideaId) 
        })
      } else {
        // Idea updated - update the idea in store directly from changes or fetch silently
        const existingIndex = ideas.findIndex(i => i.id === data.ideaId)
        if (existingIndex >= 0) {
          // Update existing idea with changes directly (no API call needed)
          const updatedIdeas = [...ideas]
          updatedIdeas[existingIndex] = {
            ...updatedIdeas[existingIndex],
            ...data.changes,
            updated_at: new Date().toISOString() // Update timestamp
          }
          useIdeaStore.setState({ ideas: updatedIdeas })
        } else {
          // Idea not in store, fetch it silently (without loading state)
          fetchIdeaSilently(data.ideaId).catch(error => {
            console.error('Failed to fetch updated idea:', error)
          })
        }
      }
    }

    // Subscribe to idea updates
    signalrService.on('ideaUpdated', handleIdeaUpdate)

    // Cleanup: unsubscribe when component unmounts
    return () => {
      signalrService.off('ideaUpdated', handleIdeaUpdate)
    }
  }, []) // No dependencies - handler is stable

  const loadTeams = async () => {
    setIsLoadingTeams(true)
    try {
      const response = await adminService.getTeams()
      setTeams(response.teams)
    } catch (error) {
      console.error('Failed to load teams:', error)
    } finally {
      setIsLoadingTeams(false)
    }
  }

  const handleSaveIdea = async (data: any) => {
    if (editingIdea) {
      await updateIdea(editingIdea.id, data)
    } else {
      await createIdea(data)
    }
    refetch()
  }

  const handleDeleteIdea = async (idea: Idea) => {
    if (confirm(`Are you sure you want to delete "${idea.title}"?`)) {
      await deleteIdea(idea.id)
      refetch()
    }
  }

  const handleConvertClick = (idea: Idea) => {
    setIdeaToConvert(idea)
    setProjectName(idea.title)
    setProjectDescription(idea.description || '')
    setConvertDialogOpen(true)
  }

  const handleConvert = async () => {
    if (!ideaToConvert) return

    setIsConverting(true)
    try {
      const convertData: IdeaConvertRequest = {
        project_name: projectName || ideaToConvert.title,
        project_description: projectDescription || ideaToConvert.description,
        project_status: 'active',
        project_tags: ideaToConvert.tags,
        technology_tags: [],
      }
      const project = await convertIdeaToProject(ideaToConvert.id, convertData)
      setConvertDialogOpen(false)
      navigate(`/projects/${project.id}`)
    } catch (error) {
      console.error('Failed to convert idea:', error)
      toast.error('Failed to convert idea to project', error instanceof Error ? error.message : 'An error occurred')
    } finally {
      setIsConverting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card>
          <CardHeader>
            <CardTitle>Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => refetch()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const ideasList = Array.isArray(ideas) ? ideas : []

  return (
    <div className="space-y-6">
      <PageHeader
        title={
          <span className="flex items-center gap-2">
            <Sparkles className="h-8 w-8" />
            Ideas
          </span>
        }
        description="Capture and organize your project ideas"
        actions={
          <Button onClick={() => {
            setEditingIdea(null)
            setIdeaEditorOpen(true)
          }}>
            <Plus className="mr-2 h-4 w-4" />
            New Idea
          </Button>
        }
      />

      <div className="flex items-center gap-4">
        <Select value={statusFilter || 'all'} onValueChange={(value) => setStatusFilter(value === 'all' ? undefined : value)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Ideas</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
        {teams.length > 0 && (
          <Select 
            value={selectedTeamId || 'all'} 
            onValueChange={(value) => setSelectedTeamId(value === 'all' ? undefined : value)}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by team" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Teams</SelectItem>
              {teams.map((team) => (
                <SelectItem key={team.id} value={team.id}>
                  {team.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {ideasList.length === 0 ? (
        <EmptyState
          icon={<Lightbulb className="h-12 w-12 text-muted-foreground" />}
          title="No ideas yet"
          description="Get started by creating your first idea"
          action={{
            label: 'Create Idea',
            onClick: () => {
              setEditingIdea(null)
              setIdeaEditorOpen(true)
            },
          }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ideasList.map((idea) => (
            <div key={idea.id} className="relative group">
              <IdeaCard
                idea={idea}
                teams={teams}
                onConvert={() => handleConvertClick(idea)}
              />
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingIdea(idea)
                    setIdeaEditorOpen(true)
                  }}
                >
                  Edit
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Idea Editor Dialog */}
      <IdeaEditor
        open={ideaEditorOpen}
        onOpenChange={(open) => {
          setIdeaEditorOpen(open)
          if (!open) {
            setEditingIdea(null)
          }
        }}
        idea={editingIdea}
        onSave={handleSaveIdea}
      />

      {/* Convert to Project Dialog */}
      <Dialog open={convertDialogOpen} onOpenChange={setConvertDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Convert Idea to Project</DialogTitle>
            <DialogDescription>
              Create a new project from this idea
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="project-name">Project Name *</Label>
              <Input
                id="project-name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Enter project name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-description">Project Description</Label>
              <Textarea
                id="project-description"
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                placeholder="Enter project description"
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConvertDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleConvert} disabled={!projectName.trim() || isConverting}>
              {isConverting ? 'Converting...' : 'Convert to Project'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
