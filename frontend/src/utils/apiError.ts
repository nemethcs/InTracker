/**
 * Standardized API error handling utilities
 */

export interface ApiError extends Error {
  status?: number
  statusText?: string
  response?: {
    data?: {
      detail?: string | Array<{ loc?: string[]; msg?: string; message?: string }> | Record<string, unknown>
      message?: string
      current_version?: number
    }
    status?: number
    statusText?: string
  }
  isConflict?: boolean
  currentVersion?: number
}

/**
 * Extract error message from various error formats
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Check if it's an API error with response
    const apiError = error as ApiError
    if (apiError.response?.data) {
      const data = apiError.response.data

      // Handle FastAPI validation errors (422)
      if (data.detail) {
        if (typeof data.detail === 'string') {
          return data.detail
        } else if (Array.isArray(data.detail)) {
          // Pydantic validation errors
          return data.detail
            .map((e) => {
              if (typeof e === 'string') return e
              const field = e.loc?.join('.') || 'field'
              const msg = e.msg || e.message || 'Invalid value'
              return `${field}: ${msg}`
            })
            .join(', ')
        } else if (typeof data.detail === 'object') {
          return JSON.stringify(data.detail)
        }
      }

      // Handle standard error message
      if (data.message) {
        return data.message
      }
    }

    // Return the error message
    return error.message
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error
  }

  // Fallback
  return 'An unexpected error occurred'
}

/**
 * Check if error is a conflict (409) error
 */
export function isConflictError(error: unknown): boolean {
  if (error instanceof Error) {
    const apiError = error as ApiError
    return apiError.isConflict === true || apiError.response?.status === 409
  }
  return false
}

/**
 * Get current version from conflict error
 */
export function getCurrentVersion(error: unknown): number | undefined {
  if (error instanceof Error) {
    const apiError = error as ApiError
    if (apiError.isConflict || apiError.response?.status === 409) {
      return apiError.currentVersion || apiError.response?.data?.current_version
    }
  }
  return undefined
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    const apiError = error as ApiError
    // Network errors typically don't have a response
    return !apiError.response && error.message.includes('Network')
  }
  return false
}

/**
 * Check if error is an authentication error (401)
 */
export function isAuthError(error: unknown): boolean {
  if (error instanceof Error) {
    const apiError = error as ApiError
    return apiError.response?.status === 401
  }
  return false
}

/**
 * Check if error is a not found error (404)
 */
export function isNotFoundError(error: unknown): boolean {
  if (error instanceof Error) {
    const apiError = error as ApiError
    return apiError.response?.status === 404
  }
  return false
}

/**
 * Check if error is a validation error (422)
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof Error) {
    const apiError = error as ApiError
    return apiError.response?.status === 422
  }
  return false
}

/**
 * Create a standardized API error
 */
export function createApiError(
  message: string,
  status?: number,
  response?: ApiError['response']
): ApiError {
  const error = new Error(message) as ApiError
  error.status = status
  error.response = response
  return error
}
