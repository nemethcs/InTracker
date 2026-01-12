"""MCP Tools for GitHub issues."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.github_service import GitHubService
from src.services.project_service import ProjectService
from src.services.element_service import ElementService
from github.GithubException import GithubException
from .github_repository import get_github_service
from src.mcp.utils.project_access import validate_project_access


def get_link_element_to_issue_tool() -> MCPTool:
    """Get link element to issue tool definition."""
    return MCPTool(
        name="mcp_link_element_to_issue",
        description="Link a project element to a GitHub issue",
        inputSchema={
            "type": "object",
            "properties": {
                "elementId": {"type": "string", "description": "Element UUID"},
                "issueNumber": {"type": "integer", "description": "GitHub issue number"},
            },
            "required": ["elementId", "issueNumber"],
        },
    )


async def handle_link_element_to_issue(element_id: str, issue_number: int) -> dict:
    """Handle link element to issue tool call."""
    db = SessionLocal()
    try:
        # Use ElementService to get element
        element = ElementService.get_element_by_id(db, UUID(element_id))
        if not element:
            return {"error": "Element not found"}

        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, element.project_id)
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get issue from GitHub to validate
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            issue = repository.get_issue(issue_number)
            issue_url = issue.html_url
        except GithubException as e:
            return {"error": f"GitHub issue not found: {e}"}

        # Update element directly (ElementService doesn't have update method for GitHub fields)
        from src.database.models import ProjectElement
        element = db.query(ProjectElement).filter(ProjectElement.id == UUID(element_id)).first()
        element.github_issue_number = issue_number
        element.github_issue_url = issue_url
        db.commit()
        db.refresh(element)

        # Invalidate cache
        cache_service.delete(f"project:{project.id}:*")

        return {
            "element_id": element_id,
            "issue_number": issue_number,
            "issue_url": issue_url,
        }
    finally:
        db.close()


def get_get_github_issue_tool() -> MCPTool:
    """Get GitHub issue tool definition."""
    return MCPTool(
        name="mcp_get_github_issue",
        description="Get GitHub issue information",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "issueNumber": {"type": "integer", "description": "GitHub issue number"},
            },
            "required": ["projectId", "issueNumber"],
        },
    )


async def handle_get_github_issue(project_id: str, issue_number: int) -> dict:
    """Handle get GitHub issue tool call."""
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

        # Get issue from GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            issue = repository.get_issue(issue_number)
            return {
                "project_id": project_id,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "url": issue.html_url,
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "assignees": [assignee.login for assignee in issue.assignees],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                },
            }
        except GithubException as e:
            return {"error": f"GitHub issue not found: {e}"}
    finally:
        db.close()


def get_create_github_issue_tool() -> MCPTool:
    """Get create GitHub issue tool definition."""
    return MCPTool(
        name="mcp_create_github_issue",
        description="Create a GitHub issue",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body/description"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional labels"},
                "elementId": {"type": "string", "description": "Optional element ID to link"},
            },
            "required": ["projectId", "title"],
        },
    )


async def handle_create_github_issue(
    project_id: str,
    title: str,
    body: Optional[str] = None,
    labels: Optional[List[str]] = None,
    element_id: Optional[str] = None,
) -> dict:
    """Handle create GitHub issue tool call."""
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

        # Create issue on GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            issue = repository.create_issue(
                title=title,
                body=body or "",
                labels=labels or [],
            )

            # Link to element if provided
            if element_id:
                element = ElementService.get_element_by_id(db, UUID(element_id))
                if element and element.project_id == project.id:
                    # Update element directly (ElementService doesn't have update method for GitHub fields)
                    from src.database.models import ProjectElement
                    element = db.query(ProjectElement).filter(ProjectElement.id == UUID(element_id)).first()
                    element.github_issue_number = issue.number
                    element.github_issue_url = issue.html_url
                    db.commit()

            # Invalidate cache
            cache_service.delete(f"project:{project_id}:*")

            return {
                "project_id": project_id,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "state": issue.state,
                },
                "element_id": element_id if element_id else None,
            }
        except GithubException as e:
            return {"error": f"Failed to create GitHub issue: {e}"}
    finally:
        db.close()
