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
import { FormField, FormInput, FormTextarea, FormSelect } from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Document, DocumentCreate, DocumentUpdate } from '@/services/documentService'

interface DocumentEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  document?: Document | null
  projectId: string
  elementId?: string
  onSave: (data: DocumentCreate | DocumentUpdate) => Promise<void>
}

export function DocumentEditor({
  open,
  onOpenChange,
  document,
  projectId,
  elementId,
  onSave,
}: DocumentEditorProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [type, setType] = useState<Document['type']>('architecture')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (document) {
      setTitle(document.title)
      setContent(document.content)
      setType(document.type)
    } else {
      setTitle('')
      setContent('')
      setType('architecture')
    }
  }, [document, open])

  const handleSave = async () => {
    if (!title.trim()) {
      return
    }

    setIsSaving(true)
    try {
      if (document) {
        await onSave({
          title,
          content,
        } as DocumentUpdate)
      } else {
        await onSave({
          project_id: projectId,
          element_id: elementId,
          type,
          title,
          content,
        } as DocumentCreate)
      }
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save document:', error)
      // Error is handled by parent component
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{document ? 'Edit Document' : 'Create Document'}</DialogTitle>
          <DialogDescription>
            {document ? 'Update the document details' : 'Create a new document for your project'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {!document && (
            <FormField label="Type" required>
              <Select value={type} onValueChange={(value) => setType(value as Document['type'])}>
                <FormSelect>
                  <SelectValue />
                </FormSelect>
                <SelectContent>
                  <SelectItem value="architecture">Architecture</SelectItem>
                  <SelectItem value="adr">ADR (Architecture Decision Record)</SelectItem>
                  <SelectItem value="domain">Domain</SelectItem>
                  <SelectItem value="constraints">Constraints</SelectItem>
                  <SelectItem value="runbook">Runbook</SelectItem>
                  <SelectItem value="ai_instructions">AI Instructions</SelectItem>
                </SelectContent>
              </Select>
            </FormField>
          )}
          <FormField label="Title" required>
            <FormInput
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title"
            />
          </FormField>
          <FormField label="Content">
            <FormTextarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter document content (Markdown supported)"
              rows={12}
              className="font-mono text-sm"
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || !title.trim()}>
            {isSaving ? 'Saving...' : document ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
