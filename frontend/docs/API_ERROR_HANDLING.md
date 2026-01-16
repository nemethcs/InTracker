# API Error Handling Standardization

## Overview

All API services use a standardized error handling pattern to ensure consistent error messages and behavior across the application.

## Error Handling Architecture

### 1. Axios Interceptor (`api.ts`)

The main error handling happens in the Axios response interceptor:

- **401 Unauthorized**: Automatically attempts token refresh
- **422 Validation Errors**: Extracts Pydantic validation errors
- **Network Errors**: Provides user-friendly network error messages
- **Other Errors**: Extracts error messages from response data

### 2. Error Utility (`utils/apiError.ts`)

Provides standardized error handling utilities:

- `getErrorMessage(error)`: Extract user-friendly error message from any error format
- `isConflictError(error)`: Check if error is a conflict (409)
- `getCurrentVersion(error)`: Get current version from conflict error
- `isNetworkError(error)`: Check if error is a network error
- `isAuthError(error)`: Check if error is authentication error (401)
- `isNotFoundError(error)`: Check if error is not found (404)
- `isValidationError(error)`: Check if error is validation error (422)

### 3. Service Layer

Services use the `api` instance directly. Errors are automatically handled by the interceptor, but services can add custom error handling for specific cases (e.g., conflict errors).

## Usage Examples

### Basic Service Method

```typescript
export const projectService = {
  async getProject(id: string): Promise<Project> {
    const response = await api.get(`/projects/${id}`)
    return response.data
  },
}
```

Errors are automatically handled by the interceptor. The error will be:
- Transformed to a user-friendly message
- Re-thrown as an Error with the message
- Can be caught and displayed to the user

### Handling Specific Error Types

```typescript
import { getErrorMessage, isConflictError, getCurrentVersion } from '@/utils/apiError'

try {
  await todoService.updateTodo(id, data)
} catch (error) {
  if (isConflictError(error)) {
    const currentVersion = getCurrentVersion(error)
    // Handle conflict - show user-friendly message and retry with current version
    toast.error('Todo was modified. Please refresh and try again.')
  } else {
    toast.error(getErrorMessage(error))
  }
}
```

### Using Error Utilities in Components

```typescript
import { getErrorMessage, isNetworkError, isAuthError } from '@/utils/apiError'

const handleAction = async () => {
  try {
    await someService.doSomething()
  } catch (error) {
    if (isNetworkError(error)) {
      toast.error('Network error. Please check your connection.')
    } else if (isAuthError(error)) {
      // Auth error is handled by interceptor (redirects to login)
      return
    } else {
      toast.error(getErrorMessage(error))
    }
  }
}
```

## Error Types

### ApiError Interface

```typescript
interface ApiError extends Error {
  status?: number
  statusText?: string
  response?: {
    data?: {
      detail?: string | Array<{ loc?: string[]; msg?: string }> | Record<string, unknown>
      message?: string
      current_version?: number
    }
    status?: number
    statusText?: string
  }
  isConflict?: boolean
  currentVersion?: number
}
```

## Error Message Extraction

The `getErrorMessage` function handles various error formats:

1. **FastAPI Validation Errors (422)**:
   ```json
   {
     "detail": [
       {"loc": ["body", "name"], "msg": "field required"}
     ]
   }
   ```
   → `"body.name: field required"`

2. **String Detail**:
   ```json
   {
     "detail": "Project not found"
   }
   ```
   → `"Project not found"`

3. **Standard Message**:
   ```json
   {
     "message": "An error occurred"
   }
   ```
   → `"An error occurred"`

4. **Error Object**:
   ```typescript
   new Error("Something went wrong")
   ```
   → `"Something went wrong"`

## Best Practices

1. **Don't catch errors in services** unless you need to transform them (e.g., conflict errors)
2. **Use error utilities** in components to get user-friendly messages
3. **Check error types** before handling (e.g., `isConflictError`, `isNetworkError`)
4. **Show user-friendly messages** using `getErrorMessage(error)`
5. **Handle conflicts specially** for optimistic locking scenarios

## Migration Guide

### Before

```typescript
try {
  await service.doSomething()
} catch (error: any) {
  const message = error.response?.data?.detail || error.message || 'An error occurred'
  toast.error(message)
}
```

### After

```typescript
import { getErrorMessage } from '@/utils/apiError'

try {
  await service.doSomething()
} catch (error) {
  toast.error(getErrorMessage(error))
}
```

## Special Cases

### Conflict Errors (409)

Conflict errors are handled specially for optimistic locking:

```typescript
import { isConflictError, getCurrentVersion } from '@/utils/apiError'

try {
  await todoService.updateTodo(id, data)
} catch (error) {
  if (isConflictError(error)) {
    const currentVersion = getCurrentVersion(error)
    // Retry with current version
    await todoService.updateTodo(id, { ...data, expected_version: currentVersion })
  }
}
```

### Network Errors

Network errors are automatically detected and provide user-friendly messages:

```typescript
import { isNetworkError } from '@/utils/apiError'

if (isNetworkError(error)) {
  // Show network error message
  toast.error('Network error. Please check your connection.')
}
```
