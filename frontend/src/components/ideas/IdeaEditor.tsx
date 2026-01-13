import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { adminService, type Team } from '@/services/adminService'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { Idea, IdeaCreate, IdeaUpdate } from '@/services/ideaService'
import { toast } from '@/hooks/useToast'
import { FormField, FormInput, FormTextarea, FormSelect } from '@/components/ui/form'

interface IdeaEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  idea?: Idea | null
  onSave: (data: IdeaCreate | IdeaUpdate) => Promise<void>
}

export function IdeaEditor({ open, onOpenChange, idea, onSave }: IdeaEditorProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<'draft' | 'active' | 'archived'>('draft')
  const [teamId, setTeamId] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [teams, setTeams] = useState<Team[]>([])
  const [isLoadingTeams, setIsLoadingTeams] = useState(false)

  useEffect(() => {
    if (open) {
      // Load teams when dialog opens
      loadTeams()
    }
    
    if (idea) {
      setTitle(idea.title)
      setDescription(idea.description || '')
      setStatus(idea.status)
      setTeamId(idea.team_id)
      setTags(idea.tags || [])
    } else {
      setTitle('')
      setDescription('')
      setStatus('draft')
      setTeamId('')
      setTags([])
    }
    setTagInput('')
  }, [idea, open])

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

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()])
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const handleSave = async () => {
    if (!teamId && !idea) {
      toast.warning('Team required', 'Please select a team before creating an idea.')
      return
    }

    setIsSaving(true)
    try {
      const data: IdeaCreate | IdeaUpdate = idea
        ? {
            title,
            description: description || undefined,
            status,
            tags: tags.length > 0 ? tags : undefined,
          }
        : {
            title,
            team_id: teamId,
            description: description || undefined,
            status,
            tags: tags.length > 0 ? tags : undefined,
          }
      await onSave(data)
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save idea:', error)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{idea ? 'Edit Idea' : 'New Idea'}</DialogTitle>
          <DialogDescription>
            {idea ? 'Update your idea details' : 'Create a new idea to track'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {!idea && (
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
          )}
          <FormField label="Title" required>
            <FormInput
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter idea title"
            />
          </FormField>
          <FormField label="Description">
            <FormTextarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your idea"
              rows={4}
            />
          </FormField>
          <FormField label="Status">
            <Select value={status} onValueChange={(value: 'draft' | 'active' | 'archived') => setStatus(value)}>
              <FormSelect>
                <SelectValue />
              </FormSelect>
              <SelectContent>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
          </FormField>
          <FormField label="Tags">
            <div className="flex gap-2">
              <FormInput
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleAddTag()
                  }
                }}
                placeholder="Add a tag and press Enter"
              />
              <Button type="button" variant="outline" onClick={handleAddTag}>
                Add
              </Button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="cursor-pointer" onClick={() => handleRemoveTag(tag)}>
                    {tag} ×
                  </Badge>
                ))}
              </div>
            )}
          </FormField>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!title.trim() || isSaving || (!idea && !teamId)}>
            {isSaving ? 'Saving...' : idea ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
