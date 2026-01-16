import { ReactNode } from 'react'
import { LoadingState } from './LoadingState'
import { ErrorState } from './ErrorState'
import { EmptyState } from './EmptyState'

interface QueryStateProps<T> {
  isLoading: boolean
  error: Error | string | null | undefined
  data: T | undefined
  empty?: {
    condition?: (data: T) => boolean
    icon?: ReactNode
    title: string
    description?: string
    action?: {
      label: string
      onClick: () => void
    }
  }
  loading?: {
    variant?: 'spinner' | 'skeleton' | 'combined'
    size?: 'sm' | 'md' | 'lg'
    skeletonCount?: number
  }
  errorAction?: {
    label: string
    onClick: () => void
  }
  children: (data: T) => ReactNode
  className?: string
}

/**
 * Unified component for handling loading, error, and empty states in data queries.
 * Works with React Query, Zustand stores, or any async data fetching pattern.
 * 
 * @example
 * ```tsx
 * <QueryState
 *   isLoading={isLoading}
 *   error={error}
 *   data={projects}
 *   empty={{
 *     title: "No projects found",
 *     description: "Create your first project to get started",
 *     action: {
 *       label: "Create Project",
 *       onClick: () => setProjectEditorOpen(true)
 *     }
 *   }}
 * >
 *   {(projects) => <ProjectsList projects={projects} />}
 * </QueryState>
 * ```
 */
export function QueryState<T>({
  isLoading,
  error,
  data,
  empty,
  loading,
  errorAction,
  children,
  className,
}: QueryStateProps<T>) {
  // Loading state
  if (isLoading) {
    return (
      <LoadingState
        variant={loading?.variant}
        size={loading?.size}
        skeletonCount={loading?.skeletonCount}
        className={className}
      />
    )
  }

  // Error state
  if (error) {
    const errorMessage = error instanceof Error ? error.message : error || 'An error occurred'
    return (
      <ErrorState
        message={errorMessage}
        action={errorAction ? {
          label: errorAction.label,
          onClick: errorAction.onClick,
        } : undefined}
        className={className}
      />
    )
  }

  // Empty state
  if (!data || (empty && empty.condition && empty.condition(data))) {
    // Check if data is an array and empty
    if (Array.isArray(data) && data.length === 0) {
      return (
        <EmptyState
          icon={empty?.icon}
          title={empty?.title || 'No items found'}
          description={empty?.description}
          action={empty?.action}
          className={className}
        />
      )
    }

    // Check custom empty condition
    if (empty?.condition && data && empty.condition(data)) {
      return (
        <EmptyState
          icon={empty?.icon}
          title={empty?.title || 'No items found'}
          description={empty?.description}
          action={empty?.action}
          className={className}
        />
      )
    }

    // No data at all
    if (!data) {
      return (
        <EmptyState
          icon={empty?.icon}
          title={empty?.title || 'No data available'}
          description={empty?.description}
          action={empty?.action}
          className={className}
        />
      )
    }
  }

  // Render children with data
  return <>{children(data as T)}</>
}
