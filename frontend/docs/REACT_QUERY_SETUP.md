# React Query Setup & Migration Guide

## Overview

React Query (TanStack Query) has been integrated into the frontend to provide:
- Automatic request caching
- Request deduplication
- Background refetching
- Optimistic updates
- Better error handling
- Loading state management

## Setup

React Query is configured in `App.tsx` with the following defaults:
- **staleTime**: 5 minutes - data is considered fresh for 5 minutes
- **gcTime**: 10 minutes - cached data is kept for 10 minutes
- **retry**: 2 attempts for queries, 1 for mutations
- **refetchOnWindowFocus**: false - don't refetch when window regains focus
- **refetchOnReconnect**: true - refetch when network reconnects

## Query Keys

Query keys are organized hierarchically for easy invalidation:

```typescript
featureKeys = {
  all: ['features'],
  lists: () => ['features', 'list'],
  list: (projectId, sort) => ['features', 'list', projectId, sort],
  details: () => ['features', 'detail'],
  detail: (id) => ['features', 'detail', id],
}
```

## Usage Examples

### Fetching Data

```typescript
import { useFeaturesQuery } from '@/hooks/useFeaturesQuery'

function MyComponent() {
  const { data: features, isLoading, error, refetch } = useFeaturesQuery(projectId, 'updated_at_desc')
  
  if (isLoading) return <LoadingSpinner />
  if (error) return <Error message={error.message} />
  
  return <FeaturesList features={features} />
}
```

### Mutations

```typescript
import { useCreateFeature, useUpdateFeature, useDeleteFeature } from '@/hooks/useFeaturesQuery'

function FeatureForm() {
  const createFeature = useCreateFeature()
  const updateFeature = useUpdateFeature()
  const deleteFeature = useDeleteFeature()
  
  const handleCreate = async (data) => {
    try {
      await createFeature.mutateAsync(data)
      // Cache is automatically updated
    } catch (error) {
      // Handle error
    }
  }
  
  return (
    <form onSubmit={handleCreate}>
      {/* form fields */}
    </form>
  )
}
```

## Migration Strategy

### Phase 1: Setup (✅ Complete)
- Install React Query
- Configure QueryClient in App.tsx
- Create example hooks (useFeaturesQuery)

### Phase 2: Gradual Migration
1. Create React Query hooks for each service
2. Update components to use React Query hooks alongside Zustand
3. Keep Zustand for SignalR real-time updates
4. Use React Query cache invalidation when SignalR updates arrive

### Phase 3: Full Migration (Optional)
- Replace all Zustand store data fetching with React Query
- Keep Zustand only for UI state (not server state)
- Use React Query mutations for all write operations

## Integration with SignalR

When SignalR updates arrive, invalidate React Query cache:

```typescript
signalrService.on('featureUpdated', (data) => {
  queryClient.invalidateQueries({ queryKey: featureKeys.lists() })
  queryClient.invalidateQueries({ queryKey: featureKeys.detail(data.featureId) })
})
```

## Benefits

1. **Automatic Caching**: Data is cached automatically, reducing API calls
2. **Request Deduplication**: Multiple components requesting the same data only trigger one API call
3. **Background Refetching**: Data is refreshed in the background when stale
4. **Optimistic Updates**: UI can update immediately while mutation is in progress
5. **Better Error Handling**: Centralized error handling and retry logic
6. **Loading States**: Built-in loading and error states

## Next Steps

1. Create React Query hooks for:
   - Projects (useProjectsQuery)
   - Todos (useTodosQuery)
   - Ideas (useIdeasQuery)
   - Documents (useDocumentsQuery)
2. Update components to use React Query hooks
3. Integrate SignalR updates with React Query cache invalidation
