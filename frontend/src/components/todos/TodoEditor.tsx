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
import type { Todo, TodoCreate, TodoUpdate } from '@/services/todoService'

interface TodoEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  todo?: Todo | null
  featureId?: string
  elementId: string
  onSave: (data: TodoCreate | TodoUpdate) => Promise<void>
}

export function TodoEditor({
  open,
  onOpenChange,
  todo,
  featureId,
  elementId,
  onSave,
}: TodoEditorProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<Todo['status']>('new')
  const [priority, setPriority] = useState<Todo['priority']>('medium')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (todo) {
      setTitle(todo.title)
      setDescription(todo.description || '')
      setStatus(todo.status)
      setPriority(todo.priority || 'medium')
    } else {
      setTitle('')
      setDescription('')
      setStatus('new')
      setPriority('medium')
    }
  }, [todo, open])

  const handleSave = async () => {
    if (!title.trim()) {
      return
    }

    setIsSaving(true)
    try {
      if (todo) {
        // Update existing todo
        await onSave({
          title,
          description: description || undefined,
          status,
          priority,
          expected_version: todo.version,
        } as TodoUpdate)
      } else {
        // Create new todo
        await onSave({
          element_id: elementId,
          title,
          description: description || undefined,
          feature_id: featureId,
          priority,
        } as TodoCreate)
      }
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save todo:', error)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{todo ? 'Edit Todo' : 'Create Todo'}</DialogTitle>
          <DialogDescription>
            {todo ? 'Update the todo details' : 'Add a new todo to track your work'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter todo title"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter todo description"
              rows={4}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select value={status} onValueChange={(value) => setStatus(value as Todo['status'])}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="done">Done</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Select value={priority || 'medium'} onValueChange={(value) => setPriority(value as Todo['priority'])}>
              <SelectTrigger id="priority">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || !title.trim()}>
            {isSaving ? 'Saving...' : todo ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
