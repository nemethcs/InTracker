"""GitHub service for repository and branch management."""
from typing import Optional, List, Dict, Any, Callable
from uuid import UUID
from github import Github
from github.GithubException import GithubException
from src.config import settings
from src.services.github_token_service import github_token_service
from src.services.github_rate_limit import GitHubRateLimitHandler
from src.database.base import SessionLocal
import logging
import time

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for GitHub operations."""

    def __init__(self, user_id: Optional[UUID] = None):
        """Initialize GitHub client.
        
        Args:
            user_id: Optional user ID to use user's OAuth token instead of global token
        """
        self.client: Optional[Github] = None
        self.user_id = user_id
        self.token_key = str(user_id) if user_id else "global"
        
        # If user_id is provided, try to use user's OAuth token
        if user_id:
            db = SessionLocal()
            try:
                token = github_token_service.get_user_token(db, user_id)
                if token:
                    try:
                        self.client = Github(token)
                        logger.info(f"GitHub client initialized with user {user_id} OAuth token")
                        return
                    except Exception as e:
                        logger.warning(f"GitHub client initialization with user token failed: {e}")
                else:
                    logger.warning(f"No GitHub OAuth token found for user {user_id}")
            finally:
                db.close()
        
        # Fallback to global token or no client
        if settings.GITHUB_TOKEN:
            try:
                self.client = Github(settings.GITHUB_TOKEN)
                logger.info("GitHub client initialized with global GITHUB_TOKEN")
            except Exception as e:
                logger.warning(f"GitHub client initialization failed: {e}")
        else:
            logger.warning("No GitHub token available (neither user OAuth nor global GITHUB_TOKEN)")

    def _execute_with_rate_limit_handling(
        self,
        operation: Callable,
        operation_name: str,
        max_retries: int = 3,
    ) -> Any:
        """Execute a GitHub API operation with rate limit handling.
        
        Args:
            operation: Function to execute (should be a GitHub API call)
            operation_name: Name of the operation for logging
            max_retries: Maximum number of retries
            
        Returns:
            Result of the operation, or None if failed after retries
        """
        if not self.client:
            return None
        
        # Check if we should wait for rate limit reset
        wait_time = GitHubRateLimitHandler.should_wait_for_rate_limit(
            self.token_key,
            self.client
        )
        if wait_time and wait_time > 0:
            logger.info(f"Waiting {wait_time:.0f}s for GitHub rate limit reset before {operation_name}")
            time.sleep(min(wait_time, 60))  # Max 60 seconds wait
        
        for attempt in range(max_retries + 1):
            try:
                result = operation()
                # Update rate limit info after successful request
                GitHubRateLimitHandler.update_rate_limit_after_request(
                    self.token_key,
                    self.client
                )
                return result
            except GithubException as e:
                if GitHubRateLimitHandler.is_rate_limit_error(e):
                    if attempt < max_retries:
                        should_retry = GitHubRateLimitHandler.handle_rate_limit_error(
                            e,
                            self.token_key,
                            max_retries=1,  # Already in retry loop
                        )
                        if should_retry:
                            logger.info(f"Retrying {operation_name} after rate limit error (attempt {attempt + 1}/{max_retries + 1})")
                            continue
                    logger.error(f"GitHub API rate limit exceeded for {operation_name} after {max_retries + 1} attempts")
                    return None
                else:
                    # Non-rate-limit error, log and return None
                    logger.warning(f"GitHub API error in {operation_name}: {e.status} - {e.data}")
                    return None
            except Exception as e:
                logger.warning(f"Error in {operation_name}: {e}")
                return None
        
        return None
    
    def validate_repo_access(self, owner: str, repo: str) -> bool:
        """Validate access to a GitHub repository."""
        if not self.client:
            logger.warning(f"GitHub client not initialized for repo access validation: {owner}/{repo}")
            return False

        def _validate():
            repository = self.client.get_repo(f"{owner}/{repo}")
            _ = repository.name  # Try to access repo info
            return True
        
        result = self._execute_with_rate_limit_handling(
            _validate,
            f"validate_repo_access({owner}/{repo})"
        )
        
        if result:
            logger.info(f"GitHub repo access validated: {owner}/{repo}")
            return True
        return False

    def get_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        if not self.client:
            return None

        def _get_repo_info():
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
        
        return self._execute_with_rate_limit_handling(
            _get_repo_info,
            f"get_repo_info({owner}/{repo})"
        )

    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List branches for a repository."""
        if not self.client:
            return []

        def _list_branches():
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
        
        result = self._execute_with_rate_limit_handling(
            _list_branches,
            f"list_branches({owner}/{repo})"
        )
        return result if result is not None else []

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

        def _create_branch():
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
        
        return self._execute_with_rate_limit_handling(
            _create_branch,
            f"create_branch({owner}/{repo}, {branch_name})"
        )

    def get_branch(self, owner: str, repo: str, branch_name: str) -> Optional[Dict[str, Any]]:
        """Get branch information."""
        if not self.client:
            return None

        def _get_branch():
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
        
        return self._execute_with_rate_limit_handling(
            _get_branch,
            f"get_branch({owner}/{repo}, {branch_name})"
        )

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

        def _create_issue():
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
        
        return self._execute_with_rate_limit_handling(
            _create_issue,
            f"create_issue({owner}/{repo})"
        )

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

        def _create_pull_request():
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
        
        return self._execute_with_rate_limit_handling(
            _create_pull_request,
            f"create_pull_request({owner}/{repo})"
        )

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get GitHub issue by number."""
        if not self.client:
            return None

        def _get_issue():
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
        
        return self._execute_with_rate_limit_handling(
            _get_issue,
            f"get_issue({owner}/{repo}, #{issue_number})"
        )

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get GitHub pull request by number."""
        if not self.client:
            return None

        def _get_pull_request():
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
        
        return self._execute_with_rate_limit_handling(
            _get_pull_request,
            f"get_pull_request({owner}/{repo}, #{pr_number})"
        )


    @staticmethod
    def parse_github_url(github_url: str) -> tuple[Optional[str], Optional[str]]:
        """Parse GitHub repository URL to extract owner and repo name.
        
        Supports formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo) or (None, None) if parsing fails
        """
        if not github_url:
            return None, None
        
        try:
            # Remove protocol and domain
            if "github.com/" in github_url:
                # Handle https://github.com/owner/repo or git@github.com:owner/repo
                if github_url.startswith("https://github.com/"):
                    parts = github_url.replace("https://github.com/", "").split("/")
                elif github_url.startswith("git@github.com:"):
                    parts = github_url.replace("git@github.com:", "").split("/")
                else:
                    # Fallback: try to extract from any github.com URL
                    parts = github_url.split("github.com/")[-1].split("/")
                
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = parts[1].replace(".git", "").strip()
                    return owner, repo
        except Exception:
            pass
        
        return None, None


# Global instance
github_service = GitHubService()
