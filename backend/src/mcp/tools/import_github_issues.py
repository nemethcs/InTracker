"""MCP Tools for GitHub issues import."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.database.models import Project, Todo
from src.mcp.services.cache import cache_service
from src.services.element_service import ElementService
from src.services.todo_service import TodoService
from github.GithubException import GithubException
from .github_repository import get_github_service
from src.mcp.utils.project_access import validate_project_access


def get_import_github_issues_tool() -> MCPTool:
    """Get import GitHub issues tool definition."""
    return MCPTool(
        name="mcp_import_github_issues",
        description="Import GitHub issues as todos for a project. Creates todos from open GitHub issues and optionally links them to project elements. Useful for migrating existing projects to InTracker.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Only import issues with these labels",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Issue state to import (default: open)",
                    "default": "open",
                },
                "createElements": {
                    "type": "boolean",
                    "description": "Create project elements for issues without matching elements (default: true)",
                    "default": True,
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_import_github_issues(
    project_id: str,
    labels: Optional[List[str]] = None,
    state: str = "open",
    create_elements: bool = True,
) -> dict:
    """Handle import GitHub issues tool call."""
    db = SessionLocal()
    try:
        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, project_id)
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
        # Verify project exists and has GitHub repo
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}
        
        if not project.github_repo_url:
            return {"error": "Project does not have a GitHub repository connected"}
        
        # Parse GitHub URL
        github_url = project.github_repo_url
        if "github.com/" in github_url:
            parts = github_url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) < 2:
                return {"error": "Invalid GitHub repository URL"}
            owner, repo = parts[0], parts[1]
        else:
            return {"error": "Invalid GitHub repository URL format"}
        
        # Get GitHub client (fix: use get_github_service().client)
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}
        client = github_service.client
        
        # Get repository
        try:
            github_repo = client.get_repo(f"{owner}/{repo}")
        except Exception as e:
            return {"error": f"Failed to access GitHub repository: {str(e)}"}
        
        # Get issues
        issues = []
        try:
            if state == "all":
                github_issues = github_repo.get_issues(state="all")
            else:
                github_issues = github_repo.get_issues(state=state)
            
            for issue in github_issues:
                # Skip pull requests
                if issue.pull_request:
                    continue
                
                # Filter by labels if provided
                if labels:
                    issue_labels = [label.name for label in issue.labels]
                    if not any(label in issue_labels for label in labels):
                        continue
                
                issues.append(issue)
        except Exception as e:
            return {"error": f"Failed to fetch GitHub issues: {str(e)}"}
        
        # Import issues as todos
        todos_created = []
        elements_created = []
        
        # Get or create root element for issues without specific element
        root_elements_list = ElementService.get_project_elements_tree(
            db=db,
            project_id=UUID(project_id),
            parent_id=None,
        )
        root_elements = next((e for e in root_elements_list if e.type == "module"), None)
        
        if not root_elements and create_elements:
            # Use ElementService to create root element
            root_elements = ElementService.create_element(
                db=db,
                project_id=UUID(project_id),
                type="module",
                title="GitHub Issues",
                description="Imported from GitHub issues",
                status="new",
                parent_id=None,
            )
            elements_created.append({
                "id": str(root_elements.id),
                "title": "GitHub Issues",
            })
        
        for issue in issues:
            # Determine element (try to match by title or create new)
            element_id = root_elements.id if root_elements else None
            
            # Use TodoService to create todo from issue
            todo = TodoService.create_todo(
                db=db,
                element_id=element_id,
                title=issue.title,
                description=issue.body or f"GitHub Issue #{issue.number}",
                status="new" if issue.state == "open" else "done",
                priority="high" if any(label.name.lower() in ["bug", "critical", "urgent"] for label in issue.labels) else "medium",
                feature_id=None,
            )
            # Update GitHub fields directly (TodoService doesn't handle these)
            todo = db.query(Todo).filter(Todo.id == todo.id).first()
            todo.github_issue_number = issue.number
            todo.github_issue_url = issue.html_url
            db.commit()
            db.refresh(todo)
            
            todos_created.append({
                "id": str(todo.id),
                "title": todo.title,
                "github_issue_number": issue.number,
                "github_issue_url": issue.html_url,
            })
        
        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        
        return {
            "success": True,
            "project_id": project_id,
            "todos_created": len(todos_created),
            "elements_created": len(elements_created),
            "todos": todos_created,
            "elements": elements_created,
            "message": f"Imported {len(todos_created)} GitHub issues as todos",
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        db.close()
