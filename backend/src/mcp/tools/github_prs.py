"""MCP Tools for GitHub pull requests."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.github_service import GitHubService
from src.services.project_service import ProjectService
from src.services.element_service import ElementService
from src.services.todo_service import TodoService
from github.GithubException import GithubException
from .github_repository import get_github_service


def get_link_todo_to_pr_tool() -> MCPTool:
    """Get link todo to PR tool definition."""
    return MCPTool(
        name="mcp_link_todo_to_pr",
        description="Link a todo to a GitHub pull request",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "prNumber": {"type": "integer", "description": "GitHub PR number"},
            },
            "required": ["todoId", "prNumber"],
        },
    )


async def handle_link_todo_to_pr(todo_id: str, pr_number: int) -> dict:
    """Handle link todo to PR tool call."""
    db = SessionLocal()
    try:
        # Use TodoService to get todo
        todo = TodoService.get_todo_by_id(db, UUID(todo_id))
        if not todo:
            return {"error": "Todo not found"}
        
        # Validate: todo must be 'done' before linking to PR
        if todo.status != "done":
            return {
                "error": f"Cannot link todo to PR: todo must be 'done' status (current: '{todo.status}'). "
                f"Complete the todo first before linking it to a pull request."
            }

        # Use ElementService to get element
        element = ElementService.get_element_by_id(db, todo.element_id)
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

        # Get PR from GitHub to validate
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            pr_url = pr.html_url
        except GithubException as e:
            return {"error": f"GitHub PR not found: {e}"}

        # Update todo directly (TodoService doesn't have update method for GitHub fields)
        from src.database.models import Todo
        todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
        todo.github_pr_number = pr_number
        todo.github_pr_url = pr_url
        db.commit()
        db.refresh(todo)

        # Invalidate cache
        cache_service.delete(f"project:{project.id}:*")

        return {
            "todo_id": todo_id,
            "pr_number": pr_number,
            "pr_url": pr_url,
        }
    finally:
        db.close()


def get_get_github_pr_tool() -> MCPTool:
    """Get GitHub PR tool definition."""
    return MCPTool(
        name="mcp_get_github_pr",
        description="Get GitHub pull request information",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "prNumber": {"type": "integer", "description": "GitHub PR number"},
            },
            "required": ["projectId", "prNumber"],
        },
    )


async def handle_get_github_pr(project_id: str, pr_number: int) -> dict:
    """Handle get GitHub PR tool call."""
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

        # Get PR from GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            return {
                "project_id": project_id,
                "pr": {
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
                },
            }
        except GithubException as e:
            return {"error": f"GitHub PR not found: {e}"}
    finally:
        db.close()


def get_create_github_pr_tool() -> MCPTool:
    """Get create GitHub PR tool definition."""
    return MCPTool(
        name="mcp_create_github_pr",
        description="Create a GitHub pull request",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "title": {"type": "string", "description": "PR title"},
                "body": {"type": "string", "description": "PR body/description"},
                "head": {"type": "string", "description": "Head branch name"},
                "base": {"type": "string", "description": "Base branch name (default: main)"},
                "todoId": {"type": "string", "description": "Optional todo ID to link"},
            },
            "required": ["projectId", "title", "head"],
        },
    )


async def handle_create_github_pr(
    project_id: str,
    title: str,
    head: str,
    body: Optional[str] = None,
    base: str = "main",
    todo_id: Optional[str] = None,
) -> dict:
    """Handle create GitHub PR tool call."""
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

        # Create PR on GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            pr = repository.create_pull(
                title=title,
                body=body or "",
                head=head,
                base=base,
            )

            # Link to todo if provided
            if todo_id:
                todo = TodoService.get_todo_by_id(db, UUID(todo_id))
                if todo:
                    # Validate: todo must be 'done' before linking to PR
                    if todo.status != "done":
                        return {
                            "error": f"Cannot link todo to PR: todo must be 'done' status (current: '{todo.status}'). "
                            f"Complete the todo first before creating a PR for it."
                        }
                    
                    element = ElementService.get_element_by_id(db, todo.element_id)
                    if element and element.project_id == project.id:
                        # Update todo directly (TodoService doesn't have update method for GitHub fields)
                        from src.database.models import Todo
                        todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
                        todo.github_pr_number = pr.number
                        todo.github_pr_url = pr.html_url
                        db.commit()

            # Invalidate cache
            cache_service.delete(f"project:{project_id}:*")

            return {
                "project_id": project_id,
                "pr": {
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url,
                    "state": pr.state,
                },
                "todo_id": todo_id if todo_id else None,
            }
        except GithubException as e:
            return {"error": f"Failed to create GitHub PR: {e}"}
    finally:
        db.close()
