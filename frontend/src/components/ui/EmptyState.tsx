import { ReactNode } from 'react'
import { Button } from './button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  variant?: 'default' | 'compact'
  className?: string
}

export function EmptyState({ 
  icon, 
  title, 
  description, 
  action, 
  variant = 'default',
  className 
}: EmptyStateProps) {
  return (
    <Card className={cn(
      "border-dashed border-2 border-muted/50 bg-muted/20",
      variant === 'compact' ? 'py-6' : 'py-12',
      className
    )}>
      <CardHeader className={cn(
        "text-center",
        variant === 'compact' ? 'space-y-2' : 'space-y-4'
      )}>
        {icon && (
          <div className={cn(
            "mx-auto flex items-center justify-center",
            variant === 'compact' ? 'mb-2' : 'mb-4'
          )}>
            <div className="text-muted-foreground/60">
              {icon}
            </div>
          </div>
        )}
        <CardTitle className={cn(
          variant === 'compact' ? 'text-lg' : 'text-xl'
        )}>
          {title}
        </CardTitle>
        {description && (
          <CardDescription className={cn(
            variant === 'compact' ? 'text-sm' : 'text-base',
            "max-w-md mx-auto"
          )}>
            {description}
          </CardDescription>
        )}
      </CardHeader>
      {action && (
        <CardFooter className={cn(
          "justify-center",
          variant === 'compact' ? 'pt-2' : 'pt-4'
        )}>
          <Button onClick={action.onClick} variant="default">
            {action.label}
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
