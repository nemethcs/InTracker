"""GitHub service for repository and branch management."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from github import Github
from github.GithubException import GithubException
from src.config import settings
from src.services.github_token_service import github_token_service
from src.database.base import SessionLocal


class GitHubService:
    """Service for GitHub operations."""

    def __init__(self, user_id: Optional[UUID] = None):
        """Initialize GitHub client.
        
        Args:
            user_id: Optional user ID to use user's OAuth token instead of global token
        """
        self.client: Optional[Github] = None
        self.user_id = user_id
        
        # If user_id is provided, try to use user's OAuth token
        if user_id:
            db = SessionLocal()
            try:
                token = github_token_service.get_user_token(db, user_id)
                if token:
                    try:
                        self.client = Github(token)
                        print(f"✅ GitHub client initialized with user {user_id} OAuth token")
                        return
                    except Exception as e:
                        print(f"⚠️  GitHub client initialization with user token failed: {e}")
                else:
                    print(f"⚠️  No GitHub OAuth token found for user {user_id}")
            finally:
                db.close()
        
        # Fallback to global token or no client
        if settings.GITHUB_TOKEN:
            try:
                self.client = Github(settings.GITHUB_TOKEN)
                print(f"ℹ️  GitHub client initialized with global GITHUB_TOKEN")
            except Exception as e:
                print(f"⚠️  GitHub client initialization failed: {e}")
        else:
            print(f"⚠️  No GitHub token available (neither user OAuth nor global GITHUB_TOKEN)")

    def validate_repo_access(self, owner: str, repo: str) -> bool:
        """Validate access to a GitHub repository."""
        if not self.client:
            print(f"⚠️  GitHub client not initialized for repo access validation: {owner}/{repo}")
            return False

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            # Try to access repo info
            _ = repository.name
            print(f"✅ GitHub repo access validated: {owner}/{repo}")
            return True
        except GithubException as e:
            print(f"⚠️  GitHub API error validating access to {owner}/{repo}: {e.status} - {e.data}")
            return False
        except Exception as e:
            print(f"⚠️  Error validating access to {owner}/{repo}: {e}")
            return False

    def get_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            return {
                "id": repository.id,
                "name": repository.name,
                "full_name": repository.full_name,
                "owner": repository.owner.login,
                "private": repository.private,
                "default_branch": repository.default_branch,
                "url": repository.html_url,
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None

    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List branches for a repository."""
        if not self.client:
            return []

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            branches = repository.get_branches()
            return [
                {
                    "name": branch.name,
                    "sha": branch.commit.sha,
                    "protected": branch.protected,
                }
                for branch in branches
            ]
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return []
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return []

    def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_branch: str = "main",
    ) -> Optional[Dict[str, Any]]:
        """Create a new branch."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            source_branch = repository.get_branch(from_branch)
            ref = repository.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source_branch.commit.sha,
            )
            return {
                "name": branch_name,
                "sha": ref.object.sha,
                "ref": ref.ref,
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None

    def get_branch(self, owner: str, repo: str, branch_name: str) -> Optional[Dict[str, Any]]:
        """Get branch information."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            branch = repository.get_branch(branch_name)
            return {
                "name": branch.name,
                "sha": branch.commit.sha,
                "protected": branch.protected,
                "commit": {
                    "sha": branch.commit.sha,
                    "message": branch.commit.commit.message,
                    "author": branch.commit.commit.author.name if branch.commit.commit.author else None,
                },
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a GitHub issue."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            issue = repository.create_issue(
                title=title,
                body=body,
                labels=labels or [],
            )
            return {
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
                "state": issue.state,
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> Optional[Dict[str, Any]]:
        """Create a pull request."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            pr = repository.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
            )
            return {
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get GitHub issue by number."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            issue = repository.get_issue(issue_number)
            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "url": issue.html_url,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get GitHub pull request by number."""
        if not self.client:
            return None

        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "url": pr.html_url,
                "state": pr.state,
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha,
                },
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha,
                },
                "labels": [label.name for label in pr.labels],
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            }
        except GithubException as e:
            print(f"⚠️  GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")
            return None


# Global instance
github_service = GitHubService()
