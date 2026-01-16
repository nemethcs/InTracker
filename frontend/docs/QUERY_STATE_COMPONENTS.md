# Query State Components

Reusable components for handling loading, error, and empty states in data queries.

## Components

### `ErrorState`

A component for displaying error states with optional retry action.

**Props:**
- `title?: string` - Error title (default: "Something went wrong")
- `message: string` - Error message (required)
- `icon?: ReactNode` - Custom icon (default: AlertCircle)
- `action?: { label: string; onClick: () => void }` - Optional retry action
- `variant?: 'default' | 'compact' | 'inline'` - Display variant
- `className?: string` - Additional CSS classes

**Example:**
```tsx
<ErrorState
  message="Failed to load projects"
  action={{
    label: "Retry",
    onClick: () => refetch(),
  }}
/>
```

### `QueryState<T>`

A unified component for handling loading, error, and empty states in data queries. Works with React Query, Zustand stores, or any async data fetching pattern.

**Props:**
- `isLoading: boolean` - Loading state
- `error: Error | string | null | undefined` - Error state
- `data: T | undefined` - Data to display
- `empty?: { ... }` - Empty state configuration
- `loading?: { variant?, size?, skeletonCount? }` - Loading state configuration
- `errorAction?: { label: string; onClick: () => void }` - Error retry action
- `children: (data: T) => ReactNode` - Render function that receives the data
- `className?: string` - Additional CSS classes

**Example:**
```tsx
<QueryState
  isLoading={isLoading}
  error={error}
  data={projects}
  loading={{ variant: 'combined', size: 'md', skeletonCount: 6 }}
  errorAction={{
    label: 'Retry',
    onClick: () => refetch(),
  }}
  empty={{
    title: 'No projects found',
    description: 'Create your first project to get started.',
    action: {
      label: 'Create Project',
      onClick: () => setProjectEditorOpen(true),
    },
  }}
>
  {(projects) => (
    <div>
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  )}
</QueryState>
```

## Migration Guide

### Before (Manual State Handling)

```tsx
if (isLoading) {
  return <LoadingState />
}

if (error) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Error</CardTitle>
        <CardDescription>{error}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button onClick={() => refetch()}>Retry</Button>
      </CardContent>
    </Card>
  )
}

if (!data || data.length === 0) {
  return <EmptyState title="No items" />
}

return <ItemsList items={data} />
```

### After (Using QueryState)

```tsx
<QueryState
  isLoading={isLoading}
  error={error}
  data={data}
  errorAction={{ label: 'Retry', onClick: () => refetch() }}
  empty={{ title: 'No items' }}
>
  {(items) => <ItemsList items={items} />}
</QueryState>
```

## Benefits

1. **Consistency**: All loading/error/empty states look the same across the app
2. **Less Boilerplate**: No need to write the same if/else blocks everywhere
3. **Type Safety**: TypeScript ensures data is available in the render function
4. **Flexibility**: Can customize each state independently
5. **Reusability**: Works with any data fetching pattern (React Query, Zustand, etc.)
