"""MCP Tools for project context."""
from typing import Optional, List
from uuid import UUID
from pathlib import Path
import os
import json as json_lib
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import get_db_session
from src.mcp.services.cache import cache_service
from src.database.models import Project, ProjectElement, Feature, Todo, Session as SessionModel, User, UserProject
from sqlalchemy import func, and_, or_
import json


def get_project_context_tool() -> MCPTool:
    """Get project context tool definition."""
    return MCPTool(
        name="mcp_get_project_context",
        description="Get comprehensive project information including project metadata, element structure tree, all features, active todos (new/in_progress/tested), and cached resume context. Use this for initial project exploration.",
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


async def handle_get_project_context(project_id: str) -> dict:
    """Handle get project context tool call."""
    cache_key = f"project:{project_id}:context"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}

        # Get elements tree
        elements = db.query(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id)
        ).all()

        # Get features
        features = db.query(Feature).filter(
            Feature.project_id == UUID(project_id)
        ).all()

        # Get active todos (no user filtering in project context - shows all)
        todos = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
            Todo.status.in_(["new", "in_progress", "tested"]),
        ).all()

        # Build response
        context = {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "tags": project.tags,
                "technology_tags": project.technology_tags,
                "cursor_instructions": project.cursor_instructions,
            },
            "structure": [
                {
                    "id": str(e.id),
                    "type": e.type,
                    "title": e.title,
                    "description": e.description,
                    "status": e.status,
                    "parent_id": str(e.parent_id) if e.parent_id else None,
                }
                for e in elements
            ],
            "features": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "description": f.description,
                    "status": f.status,
                    "progress_percentage": f.progress_percentage,
                    "total_todos": f.total_todos,
                    "completed_todos": f.completed_todos,
                }
                for f in features
            ],
            "active_todos": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "element_id": str(t.element_id),
                    "feature_id": str(t.feature_id) if t.feature_id else None,
                }
                for t in todos
            ],
            "resume_context": project.resume_context or {},
        }

        # Cache for 5 minutes
        cache_service.set(cache_key, context, ttl=300)

        return context
    finally:
        db.close()


def get_resume_context_tool() -> MCPTool:
    """Get resume context tool definition."""
    return MCPTool(
        name="mcp_get_resume_context",
        description="Get resume context package (Last, Now, Blockers, Constraints) for a project. If userId is provided, excludes todos that are in_progress and assigned to other users.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "userId": {
                    "type": "string",
                    "description": "Optional: User UUID to filter out todos assigned to other users (in_progress status)",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_get_resume_context(project_id: str, user_id: Optional[str] = None) -> dict:
    """Handle get resume context tool call.
    
    If user_id is provided, excludes todos that are in_progress and assigned to other users.
    """
    cache_key = f"project:{project_id}:resume"
    if user_id:
        cache_key += f":user:{user_id}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}

        resume_context = project.resume_context or {}

        # If resume context exists, return it (but filter if user_id provided)
        if resume_context:
            # If user_id is provided, filter the next_todos in resume_context
            if user_id and "now" in resume_context and "next_todos" in resume_context["now"]:
                # Re-query to get filtered todos
                next_todos_query = db.query(Todo).join(ProjectElement).filter(
                    ProjectElement.project_id == UUID(project_id),
                )
                # Exclude todos that are in_progress and assigned to other users
                next_todos_query = next_todos_query.filter(
                    or_(
                        Todo.status == "new",  # New todos are always available
                        and_(
                            Todo.status == "in_progress",
                            or_(
                                Todo.assigned_to.is_(None),  # Unassigned in_progress todos
                                Todo.assigned_to == UUID(user_id),  # Assigned to this user
                            )
                        )
                    )
                )
                next_todos = next_todos_query.order_by(Todo.position, Todo.created_at).limit(3).all()
                resume_context["now"]["next_todos"] = [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "description": t.description,
                    }
                    for t in next_todos
                ]
            cache_service.set(cache_key, resume_context, ttl=60)  # 1 min TTL
            return resume_context

        # Otherwise, generate basic resume context
        # Get last session
        last_session = db.query(SessionModel).filter(
            SessionModel.project_id == UUID(project_id),
            SessionModel.ended_at.isnot(None),
        ).order_by(SessionModel.ended_at.desc()).first()

        # Get next todos - only show "new" todos, or "in_progress" todos assigned to this user
        next_todos_query = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
            Todo.status.in_(["new", "in_progress"]),
        )
        
        # If user_id is provided, exclude todos that are in_progress and assigned to other users
        if user_id:
            next_todos_query = next_todos_query.filter(
                or_(
                    Todo.status == "new",  # New todos are always available
                    and_(
                        Todo.status == "in_progress",
                        or_(
                            Todo.assigned_to.is_(None),  # Unassigned in_progress todos
                            Todo.assigned_to == UUID(user_id),  # Assigned to this user
                        )
                    )
                )
            )
        else:
            # If no user_id, only show "new" todos
            next_todos_query = next_todos_query.filter(Todo.status == "new")
        
        next_todos = next_todos_query.order_by(Todo.position, Todo.created_at).limit(3).all()

        resume = {
            "last": {
                "session_id": str(last_session.id) if last_session else None,
                "session_summary": last_session.summary if last_session else None,
                "completed_todos": last_session.todos_completed if last_session else [],
                "updated_elements": last_session.elements_updated if last_session else [],
                "timestamp": last_session.ended_at.isoformat() if last_session and last_session.ended_at else None,
            },
            "now": {
                "next_todos": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "description": t.description,
                    }
                    for t in next_todos
                ],
                "active_elements": [],
                "immediate_goals": [],
            },
            "next_blockers": {
                "blocked_todos": [],  # Removed - "blocked" status does not exist for todos
                "waiting_for": [],
                "technical_blocks": [],
            },
            "constraints": {
                "rules": [],
                "architecture_decisions": [],
                "technical_limits": [],
            },
            "cursor_instructions": project.cursor_instructions or "",
        }

        cache_service.set(cache_key, resume, ttl=60)  # 1 min TTL
        return resume
    finally:
        db.close()


def get_project_structure_tool() -> MCPTool:
    """Get project structure tool definition."""
    return MCPTool(
        name="mcp_get_project_structure",
        description="Get the hierarchical element tree structure for a project. Elements are organized in a tree with parent-child relationships. Useful for understanding project organization and dependencies.",
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


def build_element_tree(elements: list, parent_id: Optional[UUID] = None) -> list:
    """Build hierarchical element tree."""
    tree = []
    for element in elements:
        if (parent_id is None and element.parent_id is None) or (
            parent_id and element.parent_id == parent_id
        ):
            children = build_element_tree(elements, element.id)
            tree.append({
                "id": str(element.id),
                "type": element.type,
                "title": element.title,
                "description": element.description,
                "status": element.status,
                "children": children,
            })
    return tree


async def handle_get_project_structure(project_id: str) -> dict:
    """Handle get project structure tool call."""
    cache_key = f"project:{project_id}:structure"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        elements = db.query(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id)
        ).order_by(ProjectElement.position, ProjectElement.created_at).all()

        tree = build_element_tree(elements)

        result = {
            "project_id": project_id,
            "structure": tree,
        }

        cache_service.set(cache_key, result, ttl=300)  # 5 min TTL
        return result
    finally:
        db.close()


def get_active_todos_tool() -> MCPTool:
    """Get active todos tool definition."""
    return MCPTool(
        name="mcp_get_active_todos",
        description="Get active todos for a project with optional filters. If userId is provided, excludes todos that are in_progress and assigned to other users.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "status": {
                    "type": "string",
                    "enum": ["new", "in_progress", "tested", "done"],
                    "description": "Filter by status",
                },
                "featureId": {
                    "type": "string",
                    "description": "Filter by feature ID",
                },
                "userId": {
                    "type": "string",
                    "description": "Optional: User UUID to filter out todos assigned to other users (in_progress status)",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_get_active_todos(
    project_id: str,
    status: Optional[str] = None,
    feature_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Handle get active todos tool call.
    
    If user_id is provided, excludes todos that are in_progress and assigned to other users.
    """
    cache_key = f"project:{project_id}:todos:active"
    if status:
        cache_key += f":status:{status}"
    if feature_id:
        cache_key += f":feature:{feature_id}"
    if user_id:
        cache_key += f":user:{user_id}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        query = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
        )

        if status:
            query = query.filter(Todo.status == status)
        else:
            query = query.filter(Todo.status.in_(["new", "in_progress", "tested"]))

        if feature_id:
            query = query.filter(Todo.feature_id == UUID(feature_id))

        # If user_id is provided, exclude todos that are in_progress and assigned to other users
        if user_id:
            query = query.filter(
                or_(
                    Todo.status == "new",  # New todos are always available
                    Todo.status == "tested",  # Tested todos are always available
                    and_(
                        Todo.status == "in_progress",
                        or_(
                            Todo.assigned_to.is_(None),  # Unassigned in_progress todos
                            Todo.assigned_to == UUID(user_id),  # Assigned to this user
                        )
                    )
                )
            )

        todos = query.order_by(Todo.position, Todo.created_at).all()

        result = {
            "project_id": project_id,
            "todos": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "element_id": str(t.element_id),
                    "feature_id": str(t.feature_id) if t.feature_id else None,
                    "assigned_to": str(t.assigned_to) if t.assigned_to else None,
                }
                for t in todos
            ],
            "count": len(todos),
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_create_project_tool() -> MCPTool:
    """Get create project tool definition."""
    return MCPTool(
        name="mcp_create_project",
        description="Create a new project",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Project description"},
                "status": {
                    "type": "string",
                    "enum": ["active", "paused", "blocked", "completed", "archived"],
                    "description": "Project status",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Project tags",
                },
                "technologyTags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Technology tags",
                },
                "cursorInstructions": {
                    "type": "string",
                    "description": "Cursor-specific instructions for this project",
                },
                "githubRepoUrl": {
                    "type": "string",
                    "description": "GitHub repository URL",
                },
            },
            "required": ["name"],
        },
    )


async def handle_create_project(
    name: str,
    description: Optional[str] = None,
    status: str = "active",
    tags: Optional[List[str]] = None,
    technology_tags: Optional[List[str]] = None,
    cursor_instructions: Optional[str] = None,
    github_repo_url: Optional[str] = None,
) -> dict:
    """Handle create project tool call."""
    db = get_db_session()
    try:
        # Get first available user (for MCP context, we need a user)
        # In a real scenario, this would come from the MCP context/authentication
        user = db.query(User).first()
        if not user:
            return {"error": "No user available for project creation"}

        # Create project directly
        project = Project(
            name=name,
            description=description,
            status=status,
            tags=tags or [],
            technology_tags=technology_tags or [],
            cursor_instructions=cursor_instructions,
            github_repo_url=github_repo_url,
        )
        db.add(project)
        db.flush()

        # Assign owner role
        user_project = UserProject(
            user_id=user.id,
            project_id=project.id,
            role="owner",
        )
        db.add(user_project)
        db.commit()
        db.refresh(project)

        # Invalidate cache
        cache_service.clear_pattern("projects:*")

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "cursor_instructions": project.cursor_instructions,
            "github_repo_url": project.github_repo_url,
        }
    finally:
        db.close()


def get_list_projects_tool() -> MCPTool:
    """Get list projects tool definition."""
    return MCPTool(
        name="mcp_list_projects",
        description="List projects with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "paused", "blocked", "completed", "archived"],
                    "description": "Filter by status",
                },
            },
        },
    )


async def handle_list_projects(status: Optional[str] = None) -> dict:
    """Handle list projects tool call."""
    cache_key = "projects:list"
    if status:
        cache_key += f":status:{status}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        query = db.query(Project)

        if status:
            query = query.filter(Project.status == status)

        projects = query.order_by(Project.updated_at.desc()).all()

        result = {
            "projects": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "status": p.status,
                    "tags": p.tags,
                    "technology_tags": p.technology_tags,
                    "cursor_instructions": p.cursor_instructions,
                    "github_repo_url": p.github_repo_url,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                    "last_session_at": p.last_session_at.isoformat() if p.last_session_at else None,
                }
                for p in projects
            ],
            "count": len(projects),
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_update_project_tool() -> MCPTool:
    """Get update project tool definition."""
    return MCPTool(
        name="mcp_update_project",
        description="Update project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Project description"},
                "status": {
                    "type": "string",
                    "enum": ["active", "paused", "blocked", "completed", "archived"],
                    "description": "Project status",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Project tags",
                },
                "technologyTags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Technology tags",
                },
                "cursorInstructions": {
                    "type": "string",
                    "description": "Cursor-specific instructions for this project",
                },
                "githubRepoUrl": {
                    "type": "string",
                    "description": "GitHub repository URL",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_update_project(
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    technology_tags: Optional[List[str]] = None,
    cursor_instructions: Optional[str] = None,
    github_repo_url: Optional[str] = None,
) -> dict:
    """Handle update project tool call."""
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}

        # Update fields
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        if tags is not None:
            project.tags = tags
        if technology_tags is not None:
            project.technology_tags = technology_tags
        if cursor_instructions is not None:
            project.cursor_instructions = cursor_instructions
        if github_repo_url is not None:
            project.github_repo_url = github_repo_url

        db.commit()
        db.refresh(project)

        # Invalidate cache
        cache_service.delete(f"project:{project_id}:*")
        cache_service.clear_pattern("projects:*")

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "cursor_instructions": project.cursor_instructions,
            "github_repo_url": project.github_repo_url,
        }
    finally:
        db.close()

def get_identify_project_by_path_tool() -> MCPTool:
    """Get identify project by path tool definition."""
    return MCPTool(
        name="mcp_identify_project_by_path",
        description="Identify project by working directory path. Checks for .intracker/config.json, GitHub repo URL, or project name in path",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Working directory path (defaults to current working directory if not provided)",
                },
            },
        },
    )


async def handle_identify_project_by_path(path: Optional[str] = None) -> dict:
    """Handle identify project by path tool call."""
    if not path:
        path = os.getcwd()
    
    path_obj = Path(path).resolve()
    
    db = get_db_session()
    try:
        # Strategy 1: Check for .intracker/config.json
        intracker_config = path_obj / ".intracker" / "config.json"
        if intracker_config.exists():
            try:
                with open(intracker_config, "r") as f:
                    config = json_lib.load(f)
                    project_id = config.get("project_id")
                    if project_id:
                        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
                        if project:
                            return {
                                "project_id": str(project.id),
                                "name": project.name,
                                "description": project.description,
                                "status": project.status,
                                "method": ".intracker/config.json",
                                "path": str(path_obj),
                            }
            except Exception:
                # Continue to next strategy if config read fails
                pass
        
        # Strategy 2: Check for GitHub repo URL in .git/config or from git remote
        # Try to find .git directory (could be in current dir or parent)
        current_path = path_obj
        for _ in range(5):  # Check up to 5 levels up
            git_config = current_path / ".git" / "config"
            if git_config.exists():
                try:
                    with open(git_config, "r") as f:
                        content = f.read()
                        # Look for remote URL
                        for line in content.split("\n"):
                            if "url = " in line:
                                url = line.split("url = ")[1].strip()
                                # Extract owner/repo from GitHub URL
                                if "github.com" in url:
                                    # Format: https://github.com/owner/repo.git or git@github.com:owner/repo.git
                                    if "github.com/" in url:
                                        parts = url.replace("https://github.com/", "").replace("git@github.com:", "").replace(".git", "").split("/")
                                        if len(parts) >= 2:
                                            owner, repo = parts[0], parts[1]
                                            # Search for project with this GitHub repo URL
                                            github_url = f"https://github.com/{owner}/{repo}"
                                            project = db.query(Project).filter(
                                                Project.github_repo_url == github_url
                                            ).first()
                                            if project:
                                                return {
                                                    "project_id": str(project.id),
                                                    "name": project.name,
                                                    "description": project.description,
                                                    "status": project.status,
                                                    "method": "GitHub repo URL",
                                                    "github_repo_url": project.github_repo_url,
                                                    "path": str(path_obj),
                                                }
                except Exception:
                    pass
            
            # Also check if .git is a file (submodule case)
            git_file = current_path / ".git"
            if git_file.is_file():
                try:
                    with open(git_file, "r") as f:
                        content = f.read()
                        if "gitdir:" in content:
                            # This is a git submodule, skip for now
                            pass
                except Exception:
                    pass
            
            # Move up one level
            parent = current_path.parent
            if parent == current_path:  # Reached root
                break
            current_path = parent
        
        # Strategy 3: Try to match project name from path
        # Extract potential project name from path (last directory name)
        potential_name = path_obj.name
        
        # Search for projects with similar name (case-insensitive)
        projects = db.query(Project).filter(
            func.lower(Project.name) == func.lower(potential_name)
        ).all()
        
        if len(projects) == 1:
            # Exact match found
            project = projects[0]
            return {
                "project_id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "method": "Project name match",
                "matched_name": potential_name,
                "path": str(path_obj),
            }
        elif len(projects) > 1:
            # Multiple matches - return list
            return {
                "matches": [
                    {
                        "project_id": str(p.id),
                        "name": p.name,
                        "description": p.description,
                        "status": p.status,
                    }
                    for p in projects
                ],
                "method": "Project name match (multiple)",
                "matched_name": potential_name,
                "path": str(path_obj),
                "message": "Multiple projects found with this name. Please specify project_id.",
            }
        
        # No project found
        return {
            "error": "Project not found",
            "path": str(path_obj),
            "tried_methods": [
                ".intracker/config.json",
                "GitHub repo URL",
                "Project name match",
            ],
            "suggestion": "Create a .intracker/config.json file with 'project_id' field, or connect a GitHub repository to your project.",
        }
    finally:
        db.close()


def get_load_cursor_rules_tool() -> MCPTool:
    """Get load cursor rules tool definition."""
    return MCPTool(
        name="mcp_load_cursor_rules",
        description="Load Cursor Rules from project and save to .cursor/rules/intracker-project-rules.mdc file in the project directory. Works both locally and when MCP server is on Azure.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Project directory path where .cursor/rules/ directory exists. If not provided, will try to auto-detect from .intracker/config.json or use current working directory.",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_load_cursor_rules(project_id: str, project_path: Optional[str] = None) -> dict:
    """Handle load cursor rules tool call.
    
    This function returns the cursor rules content and automatically saves it to the project directory.
    Works both locally (Docker) and when MCP server is on Azure - in Azure case, returns content
    for Cursor to save locally.
    """
    from src.mcp.resources.project_resources import read_cursor_rules_resource
    
    try:
        # Get cursor rules content from resource
        content = await read_cursor_rules_resource(project_id)
        
        # Determine project directory
        project_dir = None
        
        if project_path:
            # Use provided path (from Cursor working directory)
            project_dir = Path(project_path)
        else:
            # Try to find project directory
            # In Docker, check /workspace (mounted project root)
            docker_project_dir = Path("/workspace")
            if docker_project_dir.exists() and (docker_project_dir / ".intracker" / "config.json").exists():
                try:
                    config_file = docker_project_dir / ".intracker" / "config.json"
                    with open(config_file) as f:
                        config = json_lib.load(f)
                        if config.get("project_id") == project_id:
                            project_dir = docker_project_dir
                except Exception:
                    pass
            
            # If not found in Docker mount, try current directory and parents
            if not project_dir:
                current_dir = Path.cwd()
                check_dir = current_dir
                for _ in range(5):  # Check up to 5 levels up
                    config_file = check_dir / ".intracker" / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file) as f:
                                config = json_lib.load(f)
                                if config.get("project_id") == project_id:
                                    project_dir = check_dir
                                    break
                        except Exception:
                            pass
                    check_dir = check_dir.parent
                    if check_dir == check_dir.parent:  # Reached root
                        break
                
                if not project_dir:
                    project_dir = current_dir
        
        # Try to write file if we have access to the directory
        file_written = False
        file_path = None
        file_size = None
        error_message = None
        
        try:
            # Create .cursor/rules directory if it doesn't exist
            rules_dir = project_dir / ".cursor" / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            
            # Write cursor rules file
            rules_file = rules_dir / "intracker-project-rules.mdc"
            rules_file.write_text(content, encoding="utf-8")
            
            file_written = True
            file_path = str(rules_file)
            file_size = rules_file.stat().st_size
        except (PermissionError, OSError, FileNotFoundError) as e:
            # If we can't write (e.g., MCP server on Azure), return content for Cursor to save
            error_message = f"Could not write file directly: {e}. Content returned for Cursor to save locally."
            file_path = ".cursor/rules/intracker-project-rules.mdc"
        
        # Always return the content, even if we couldn't write it
        # This allows Cursor to save it locally when MCP server is on Azure
        result = {
            "success": True,
            "project_id": project_id,
            "content": content,
            "target_path": file_path or ".cursor/rules/intracker-project-rules.mdc",
            "instructions": "Save the content to .cursor/rules/intracker-project-rules.mdc in your project directory",
        }
        
        if file_written:
            result["file_written"] = True
            result["file_path"] = file_path
            result["file_size"] = file_size
            result["message"] = f"Cursor Rules saved to {file_path}"
        else:
            result["file_written"] = False
            result["message"] = error_message or "File not written by server. Use the 'content' field to save it locally."
            result["note"] = "When MCP server is on Azure, Cursor should save the file locally using the 'content' field."
        
        return result
    except Exception as e:
        import traceback
        return {
            "success": False,
            "project_id": project_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
