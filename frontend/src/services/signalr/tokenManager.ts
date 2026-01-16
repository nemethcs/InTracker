/**
 * Token management utilities for SignalR connection
 */

/**
 * Check if token is expired or about to expire
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const expiresAt = payload.exp * 1000 // Convert to milliseconds
    const now = Date.now()
    // Consider token expired if it expires within 1 minute
    return expiresAt - now < 60000
  } catch {
    return true // If we can't parse, consider it expired
  }
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(): Promise<string | null> {
  try {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      return null
    }

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) {
      return null
    }

    const data = await response.json()
    const { access_token, refresh_token: newRefreshToken } = data.tokens

    localStorage.setItem('access_token', access_token)
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken)
    }

    return access_token
  } catch (error) {
    console.error('Failed to refresh token:', error)
    return null
  }
}

/**
 * Get current token from localStorage or parameter
 */
export function getCurrentToken(token?: string): string {
  return token || localStorage.getItem('access_token') || ''
}
