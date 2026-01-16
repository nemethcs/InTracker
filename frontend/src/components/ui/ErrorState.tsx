import { ReactNode } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  title?: string
  message: string
  icon?: ReactNode
  action?: {
    label: string
    onClick: () => void
  }
  variant?: 'default' | 'compact' | 'inline'
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  icon,
  action,
  variant = 'default',
  className,
}: ErrorStateProps) {
  const defaultIcon = <AlertCircle className="h-6 w-6" />

  if (variant === 'inline') {
    return (
      <div className={cn('p-3 text-sm text-destructive bg-destructive/10 rounded-md', className)}>
        <div className="flex items-center gap-2">
          {icon || defaultIcon}
          <span>{message}</span>
        </div>
      </div>
    )
  }

  return (
    <Card className={cn(
      'border-destructive/50 bg-destructive/5',
      variant === 'compact' ? 'py-6' : 'py-12',
      className
    )}>
      <CardHeader className={cn(
        'text-center',
        variant === 'compact' ? 'space-y-2' : 'space-y-4'
      )}>
        <div className={cn(
          'mx-auto flex items-center justify-center text-destructive',
          variant === 'compact' ? 'mb-2' : 'mb-4'
        )}>
          {icon || defaultIcon}
        </div>
        <CardTitle className={cn(
          variant === 'compact' ? 'text-lg' : 'text-xl',
          'text-destructive'
        )}>
          {title}
        </CardTitle>
        <CardDescription className={cn(
          variant === 'compact' ? 'text-sm' : 'text-base',
          'max-w-md mx-auto'
        )}>
          {message}
        </CardDescription>
      </CardHeader>
      {action && (
        <CardContent className={cn(
          'flex justify-center',
          variant === 'compact' ? 'pt-2' : 'pt-4'
        )}>
          <Button onClick={action.onClick} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            {action.label}
          </Button>
        </CardContent>
      )}
    </Card>
  )
}
