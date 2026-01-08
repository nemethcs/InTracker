"""MCP Tools for GitHub integration - refactored into smaller modules.

This module re-exports functions from:
- github_repository: Repository connection and info
- github_issues: Issue management
- github_prs: Pull request management
- github_branches: Branch management
- github_commits: Commit parsing
"""

# Re-export from github_repository
from .github_repository import (
    get_github_service,
    get_connect_github_repo_tool,
    handle_connect_github_repo,
    get_get_repo_info_tool,
    handle_get_repo_info,
)

# Re-export from github_issues
from .github_issues import (
    get_link_element_to_issue_tool,
    handle_link_element_to_issue,
    get_get_github_issue_tool,
    handle_get_github_issue,
    get_create_github_issue_tool,
    handle_create_github_issue,
)

# Re-export from github_prs
from .github_prs import (
    get_link_todo_to_pr_tool,
    handle_link_todo_to_pr,
    get_get_github_pr_tool,
    handle_get_github_pr,
    get_create_github_pr_tool,
    handle_create_github_pr,
)

# Re-export from github_branches
from .github_branches import (
    get_get_branches_tool,
    handle_get_branches,
    get_create_branch_for_feature_tool,
    handle_create_branch_for_feature,
    get_get_active_branch_tool,
    handle_get_active_branch,
    get_link_branch_to_feature_tool,
    handle_link_branch_to_feature,
    get_get_feature_branches_tool,
    handle_get_feature_branches,
    get_get_branch_status_tool,
    handle_get_branch_status,
    get_get_commits_for_feature_tool,
    handle_get_commits_for_feature,
)

# Re-export from github_commits
from .github_commits import (
    get_parse_commit_message_tool,
    handle_parse_commit_message,
)

# Backward compatibility: get_github_client (deprecated, use get_github_service().client)
def get_github_client():
    """Get GitHub client (deprecated - use get_github_service().client instead)."""
    github_service = get_github_service()
    return github_service.client if github_service else None

__all__ = [
    # Repository tools
    "get_github_service",
    "get_connect_github_repo_tool",
    "handle_connect_github_repo",
    "get_get_repo_info_tool",
    "handle_get_repo_info",
    # Issue tools
    "get_link_element_to_issue_tool",
    "handle_link_element_to_issue",
    "get_get_github_issue_tool",
    "handle_get_github_issue",
    "get_create_github_issue_tool",
    "handle_create_github_issue",
    # PR tools
    "get_link_todo_to_pr_tool",
    "handle_link_todo_to_pr",
    "get_get_github_pr_tool",
    "handle_get_github_pr",
    "get_create_github_pr_tool",
    "handle_create_github_pr",
    # Branch tools
    "get_get_branches_tool",
    "handle_get_branches",
    "get_create_branch_for_feature_tool",
    "handle_create_branch_for_feature",
    "get_get_active_branch_tool",
    "handle_get_active_branch",
    "get_link_branch_to_feature_tool",
    "handle_link_branch_to_feature",
    "get_get_feature_branches_tool",
    "handle_get_feature_branches",
    "get_get_branch_status_tool",
    "handle_get_branch_status",
    "get_get_commits_for_feature_tool",
    "handle_get_commits_for_feature",
    # Commit tools
    "get_parse_commit_message_tool",
    "handle_parse_commit_message",
    # Backward compatibility
    "get_github_client",
]
