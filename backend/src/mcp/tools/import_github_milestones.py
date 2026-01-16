"""MCP Tools for GitHub milestones import."""
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.database.models import Project, Todo
from src.mcp.services.cache import cache_service
from src.services.element_service import ElementService
from src.services.todo_service import TodoService
from src.services.feature_service import FeatureService
from github.GithubException import GithubException
from .github_repository import get_github_service
from src.mcp.utils.project_access import validate_project_access


def get_import_github_milestones_tool() -> MCPTool:
    """Get import GitHub milestones tool definition."""
    return MCPTool(
        name="mcp_import_github_milestones",
        description="Import GitHub milestones as features for a project. Creates features from GitHub milestones and links related issues as todos. Useful for migrating existing projects to InTracker.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Milestone state to import (default: open)",
                    "default": "open",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_import_github_milestones(
    project_id: str,
    state: str = "open",
) -> dict:
    """Handle import GitHub milestones tool call."""
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
        from src.services.github_service import GitHubService
        owner, repo = GitHubService.parse_github_url(project.github_repo_url)
        if not owner or not repo:
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
        
        # Get milestones
        milestones = []
        try:
            if state == "all":
                github_milestones = github_repo.get_milestones(state="all")
            else:
                github_milestones = github_repo.get_milestones(state=state)
            
            for milestone in github_milestones:
                milestones.append(milestone)
        except Exception as e:
            return {"error": f"Failed to fetch GitHub milestones: {str(e)}"}
        
        # Import milestones as features
        features_created = []
        
        for milestone in milestones:
            # Use FeatureService to create feature from milestone
            feature = FeatureService.create_feature(
                db=db,
                project_id=UUID(project_id),
                name=milestone.title,
                description=milestone.description or f"GitHub Milestone: {milestone.title}",
                status="new" if milestone.state == "open" else "done",
            )
            
            # Get issues for this milestone and create todos
            todos_count = 0
            try:
                issues = github_repo.get_issues(milestone=milestone, state="all")
                for issue in issues:
                    if issue.pull_request:
                        continue
                    
                    # Find or create element for this todo using ElementService
                    root_elements_list = ElementService.get_project_elements_tree(
                        db=db,
                        project_id=UUID(project_id),
                        parent_id=None,
                    )
                    root_elements = root_elements_list[0] if root_elements_list else None
                    
                    if root_elements:
                        # Use TodoService to create todo
                        todo = TodoService.create_todo(
                            db=db,
                            element_id=root_elements.id,
                            feature_id=feature.id,
                            title=issue.title,
                            description=issue.body or f"GitHub Issue #{issue.number}",
                            status="new" if issue.state == "open" else "done",
                            priority="high" if any(label.name.lower() in ["bug", "critical", "urgent"] for label in issue.labels) else "medium",
                        )
                        # Update GitHub fields directly (TodoService doesn't handle these)
                        todo = db.query(Todo).filter(Todo.id == todo.id).first()
                        todo.github_issue_number = issue.number
                        todo.github_issue_url = issue.html_url
                        db.commit()
                        todos_count += 1
                        
                        # Use FeatureService to update feature progress
                        FeatureService.calculate_feature_progress(db, feature.id)
            except Exception as e:
                print(f"Warning: Failed to import issues for milestone {milestone.title}: {e}")
            
            features_created.append({
                "id": str(feature.id),
                "name": feature.name,
                "todos_created": todos_count,
            })
        
        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        
        return {
            "success": True,
            "project_id": project_id,
            "features_created": len(features_created),
            "features": features_created,
            "message": f"Imported {len(features_created)} GitHub milestones as features",
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        db.close()
