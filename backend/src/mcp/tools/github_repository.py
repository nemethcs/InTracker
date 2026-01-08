"""MCP Tools for GitHub repository management."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.github_service import GitHubService
from src.services.project_service import ProjectService


# GitHub service instance (shared across all github modules)
_github_service: Optional[GitHubService] = None


def get_github_service() -> Optional[GitHubService]:
    """Get GitHub service instance (shared singleton)."""
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service


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
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}

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
