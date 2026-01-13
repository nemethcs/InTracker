/** Settings service for GitHub OAuth and user preferences. */
import api from './api'

export interface GitHubOAuthStatus {
  connected: boolean
  github_username?: string
  avatar_url?: string
  connected_at?: string
  accessible_projects?: Array<{
    project_id: string
    project_name: string
    team_id: string
    team_name: string
    github_repo_url?: string
    has_access: boolean
    access_level?: string
  }>
}

export const settingsService = {
  /**
   * Get GitHub OAuth authorization URL.
   * Returns the URL to redirect the user to GitHub for OAuth authorization.
   * 
   * @param redirectPath - Frontend path for OAuth callback (default: /settings, can be /onboarding)
   */
  async getGitHubOAuthUrl(redirectPath: string = '/settings'): Promise<{ authorization_url: string; state: string }> {
    const response = await api.get('/auth/github/authorize', {
      params: { redirect_path: redirectPath },
    })
    return response.data
  },

  /**
   * Handle OAuth callback by sending authorization code to backend.
   * This should be called after GitHub redirects back to the app.
   */
  async handleOAuthCallback(code: string, state: string): Promise<{
    message: string
    github_username?: string
    avatar_url?: string
    redirect_path?: string
  }> {
    const response = await api.get('/auth/github/callback', {
      params: { code, state },
    })
    return response.data
  },

  /**
   * Get GitHub OAuth connection status and accessible projects.
   */
  async getGitHubStatus(): Promise<GitHubOAuthStatus> {
    try {
      // Get user info (includes github_username and avatar_url if connected)
      const userResponse = await api.get('/auth/me')
      const user = userResponse.data

      // Try to get accessible projects (endpoint might not exist yet)
      let accessibleProjects: any[] = []
      try {
        const projectsResponse = await api.get('/github/projects/access')
        accessibleProjects = projectsResponse.data || []
      } catch (error) {
        // Endpoint doesn't exist yet, that's okay
        console.log('GitHub projects access endpoint not available yet')
      }

      return {
        connected: !!user.github_username,
        github_username: user.github_username,
        avatar_url: user.avatar_url,
        connected_at: user.github_connected_at,
        accessible_projects: accessibleProjects,
      }
    } catch (error) {
      console.error('Failed to get GitHub status:', error)
      throw error
    }
  },

  /**
   * Disconnect GitHub OAuth by clearing tokens.
   */
  async disconnectGitHub(): Promise<void> {
    try {
      await api.post('/auth/github/disconnect')
    } catch (error) {
      // If endpoint doesn't exist yet, that's okay for now
      console.log('GitHub disconnect endpoint not available yet')
      throw error
    }
  },
}
