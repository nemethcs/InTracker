import { LoadingSpinner } from './LoadingSpinner'
import { Skeleton } from './skeleton'
import { cn } from '@/lib/utils'

interface LoadingStateProps {
  variant?: 'spinner' | 'skeleton' | 'combined'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  skeletonCount?: number
  skeletonClassName?: string
}

/**
 * Combined loading state component that can show spinner, skeleton, or both
 * Use 'combined' variant for better UX - shows skeleton for content structure and spinner for loading indicator
 */
export function LoadingState({
  variant = 'combined',
  size = 'md',
  className,
  skeletonCount = 3,
  skeletonClassName,
}: LoadingStateProps) {
  if (variant === 'spinner') {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <LoadingSpinner size={size} />
      </div>
    )
  }

  if (variant === 'skeleton') {
    return (
      <div className={cn('space-y-3', className)}>
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <Skeleton key={i} className={cn('h-4 w-full', skeletonClassName)} />
        ))}
      </div>
    )
  }

  // Combined variant: skeleton + spinner
  return (
    <div className={cn('space-y-4', className)}>
      <div className="space-y-3">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <Skeleton key={i} className={cn('h-4 w-full', skeletonClassName)} />
        ))}
      </div>
      <div className="flex items-center justify-center py-4">
        <LoadingSpinner size={size} variant="muted" />
      </div>
    </div>
  )
}
