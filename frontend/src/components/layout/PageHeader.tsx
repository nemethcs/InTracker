import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string | ReactNode
  description?: string | ReactNode
  actions?: ReactNode
  className?: string
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6", className)}>
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        {description && (
          <div className="text-muted-foreground text-sm">
            {typeof description === 'string' ? (
              <p>{description}</p>
            ) : (
              description
            )}
          </div>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  )
}
