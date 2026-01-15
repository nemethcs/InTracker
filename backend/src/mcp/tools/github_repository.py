"""MCP Tools for GitHub repository management."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.github_service import GitHubService
from src.services.project_service import ProjectService
from src.mcp.utils.project_access import validate_project_access


# GitHub service instance cache (per user)
_github_service_cache: dict[Optional[UUID], GitHubService] = {}


def get_github_service() -> Optional[GitHubService]:
    """Get GitHub service instance using current user's OAuth token.
    
    If user is authenticated and has a GitHub OAuth token, uses that token.
    Otherwise, falls back to global GITHUB_TOKEN.
    """
    from src.mcp.middleware.auth import get_current_user_id
    
    user_id = get_current_user_id()
    
    # Check cache first
    if user_id in _github_service_cache:
        return _github_service_cache[user_id]
    
    # Create new GitHubService with user_id (will use user's OAuth token if available)
    github_service = GitHubService(user_id=user_id)
    
    # Cache the service instance for this user
    _github_service_cache[user_id] = github_service
    
    return github_service


def get_connect_github_repo_tool() -> MCPTool:
    """Get connect GitHub repo tool definition."""
    return MCPTool(
        name="mcp_connect_github_repo",
        description="Connect a GitHub repository to a project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "owner": {"type": "string", "description": "GitHub repository owner"},
                "repo": {"type": "string", "description": "GitHub repository name"},
            },
            "required": ["projectId", "owner", "repo"],
        },
    )


async def handle_connect_github_repo(project_id: str, owner: str, repo: str) -> dict:
    """Handle connect GitHub repo tool call."""
    from src.mcp.middleware.auth import get_current_user_id
    
    db = SessionLocal()
    try:
        # Get current user ID from MCP API key
        user_id = get_current_user_id()
        
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}

        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, project_id)
        if not has_access:
            return error_dict or {"error": "Cannot access project"}

        # Use GitHubService to validate and get repo info
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        if not github_service.validate_repo_access(owner, repo):
            return {"error": "Cannot access GitHub repository"}

        repo_info = github_service.get_repo_info(owner, repo)
        if not repo_info:
            return {"error": "Failed to get repository information"}

        # Use ProjectService to update project
        updated_project = ProjectService.update_project(
            db=db,
            project_id=UUID(project_id),
            user_id=user_id,
            github_repo_url=repo_info["url"],
            github_repo_id=str(repo_info["id"]),
        )
        
        if not updated_project:
            return {"error": "Failed to update project"}
        
        project = updated_project

        # Invalidate cache
        cache_service.delete(f"project:{project_id}:*")

        return {
            "project_id": project_id,
            "github_repo_url": project.github_repo_url,
            "github_repo_id": project.github_repo_id,
            "repo_info": repo_info,
        }
    finally:
        db.close()


def get_get_repo_info_tool() -> MCPTool:
    """Get repo info tool definition."""
    return MCPTool(
        name="mcp_get_repo_info",
        description="Get GitHub repository information for a project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_get_repo_info(project_id: str) -> dict:
    """Handle get repo info tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, project_id)
        if not has_access:
            return error_dict or {"error": "Cannot access project"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Use GitHubService to get repo info
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        repo_info = github_service.get_repo_info(owner, repo)
        if not repo_info:
            return {"error": "Failed to fetch repository information"}

        return {
            "project_id": project_id,
            "repo_info": repo_info,
        }
    finally:
        db.close()
