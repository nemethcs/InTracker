import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'muted'
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
}

const variantClasses = {
  default: 'text-primary',
  muted: 'text-muted-foreground',
}

export function LoadingSpinner({ className, size = 'md', variant = 'default' }: LoadingSpinnerProps) {
  return (
    <Loader2 className={cn('animate-spin', sizeClasses[size], variantClasses[variant], className)} />
  )
}
