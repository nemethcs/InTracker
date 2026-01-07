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
import type { Feature, FeatureCreate, FeatureUpdate } from '@/services/featureService'

interface FeatureEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  feature?: Feature | null
  projectId: string
  onSave: (data: FeatureCreate | FeatureUpdate) => Promise<void>
}

export function FeatureEditor({
  open,
  onOpenChange,
  feature,
  projectId,
  onSave,
}: FeatureEditorProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<Feature['status']>('new')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (feature) {
      setName(feature.name)
      setDescription(feature.description || '')
      setStatus(feature.status)
    } else {
      setName('')
      setDescription('')
      setStatus('new')
    }
  }, [feature, open])

  const handleSave = async () => {
    if (!name.trim()) {
      return
    }

    setIsSaving(true)
    try {
      if (feature) {
        // Update existing feature
        await onSave({
          name,
          description: description || undefined,
          status,
        } as FeatureUpdate)
      } else {
        // Create new feature
        await onSave({
          project_id: projectId,
          name,
          description: description || undefined,
        } as FeatureCreate)
      }
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save feature:', error)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{feature ? 'Edit Feature' : 'Create Feature'}</DialogTitle>
          <DialogDescription>
            {feature ? 'Update the feature details' : 'Add a new feature to your project'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter feature name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter feature description"
              rows={4}
            />
          </div>
          {feature && (
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={(value) => setStatus(value as Feature['status'])}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="tested">Tested</SelectItem>
                  <SelectItem value="done">Done</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || !name.trim()}>
            {isSaving ? 'Saving...' : feature ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
