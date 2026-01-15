import api from './api'

export interface GitHubRepository {
  id: number
  name: string
  full_name: string
  owner: string
  private: boolean
  url: string
  description: string
  default_branch: string
}

export interface CursorDeeplinkResponse {
  deeplink: string
  repo_url: string
  owner: string
  repo_name: string
  feature_branches: string[]
}

export const githubService = {
  async listRepositories(): Promise<GitHubRepository[]> {
    const response = await api.get('/github/repositories')
    return response.data.repositories || []
  },

  async generateCursorDeeplink(repoUrl: string, teamId?: string): Promise<CursorDeeplinkResponse> {
    const response = await api.post('/github/generate-cursor-deeplink', {
      repo_url: repoUrl,
      team_id: teamId,
    })
    return response.data
  },
}
