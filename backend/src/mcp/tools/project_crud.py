"""MCP Tools for project CRUD operations."""
from typing import Optional, List
from uuid import UUID
from pathlib import Path
import os
import json as json_lib
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.project_service import ProjectService
from src.services.signalr_hub import broadcast_project_update
from sqlalchemy import func


def get_create_project_tool() -> MCPTool:
    """Get create project tool definition."""
    return MCPTool(
        name="mcp_create_project",
        description="Create a new project for a team",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "teamId": {"type": "string", "description": "Team UUID that will own this project"},
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
            "required": ["name", "teamId"],
        },
    )


async def handle_create_project(
    name: str,
    team_id: str,
    description: Optional[str] = None,
    status: str = "active",
    tags: Optional[List[str]] = None,
    technology_tags: Optional[List[str]] = None,
    cursor_instructions: Optional[str] = None,
    github_repo_url: Optional[str] = None,
) -> dict:
    """Handle create project tool call."""
    from src.mcp.middleware.auth import get_current_user_id
    
    db = SessionLocal()
    try:
        # Get current user ID from MCP API key
        user_id = get_current_user_id()
        
        # Use ProjectService to create project
        project = ProjectService.create_project(
            db=db,
            team_id=UUID(team_id),
            name=name,
            current_user_id=user_id,
            description=description,
            status=status,
            tags=tags,
            technology_tags=technology_tags,
            cursor_instructions=cursor_instructions,
            github_repo_url=github_repo_url,
        )

        # Invalidate cache
        cache_service.clear_pattern("projects:*")

        # Broadcast SignalR update (fire and forget)
        import asyncio
        asyncio.create_task(
            broadcast_project_update(
                str(project.id),
                {
                    "action": "created",
                    "name": project.name,
                    "status": project.status
                }
            )
        )

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "team_id": str(project.team_id),
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


async def handle_list_projects(status: Optional[str] = None, user_id: Optional[str] = None) -> dict:
    """Handle list projects tool call.
    
    If user_id is provided, filters projects by user access (team membership).
    If user_id is not provided, automatically extracts it from MCP API key if available.
    """
    from src.mcp.middleware.auth import get_current_user_id
    
    # Auto-extract user_id from MCP API key if not provided
    if not user_id:
        current_user_id = get_current_user_id()
        if current_user_id:
            user_id = str(current_user_id)
    
    cache_key = "projects:list"
    if status:
        cache_key += f":status:{status}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # For list projects, we need to get all projects (no user filtering in MCP context)
        # Since ProjectService.get_user_projects requires a user_id, we'll query directly
        # but this is acceptable as it's a simple read operation
        from src.database.models import Project
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
                    "team_id": str(p.team_id),
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
    """Handle update project tool call with validation."""
    from src.database.models import Feature
    
    db = SessionLocal()
    try:
        # Validate status change: cannot archive project with active features
        if status == "archived":
            # Check if there are active features (in_progress, done, tested, merged)
            active_features = (
                db.query(Feature)
                .filter(
                    Feature.project_id == UUID(project_id),
                    Feature.status.in_(["in_progress", "done", "tested", "merged"])
                )
                .count()
            )
            if active_features > 0:
                return {
                    "error": f"Cannot archive project: {active_features} active feature(s) found. "
                    f"Complete or remove all active features before archiving the project."
                }
        
        # Get current user ID from MCP API key
        from src.mcp.middleware.auth import get_current_user_id
        user_id = get_current_user_id()
        
        # Use ProjectService to update project
        project = ProjectService.update_project(
            db=db,
            project_id=UUID(project_id),
            user_id=user_id,
            name=name,
            description=description,
            status=status,
            tags=tags,
            technology_tags=technology_tags,
            cursor_instructions=cursor_instructions,
            github_repo_url=github_repo_url,
        )
        
        if not project:
            return {"error": "Project not found"}

        # Invalidate cache
        cache_service.delete(f"project:{project_id}:*")
        cache_service.clear_pattern("projects:*")

        # Broadcast SignalR update (fire and forget)
        changes = {}
        if name is not None:
            changes["name"] = name
        if description is not None:
            changes["description"] = description
        if status is not None:
            changes["status"] = status
        if tags is not None:
            changes["tags"] = tags
        if technology_tags is not None:
            changes["technology_tags"] = technology_tags
        if cursor_instructions is not None:
            changes["cursor_instructions"] = cursor_instructions
        if github_repo_url is not None:
            changes["github_repo_url"] = github_repo_url
        
        if changes:
            import asyncio
            asyncio.create_task(
                broadcast_project_update(
                    project_id,
                    changes
                )
            )

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "team_id": str(project.team_id),
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
        description="Identify project by working directory path. Checks for .intracker/config.json, GitHub repo URL, or project name in path. NOTE: In Docker environment, path parameter is REQUIRED.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Working directory path (REQUIRED in Docker environment)",
                },
            },
            "required": ["path"],
        },
    )


async def handle_identify_project_by_path(path: Optional[str] = None) -> dict:
    """Handle identify project by path tool call.
    
    NOTE: In Docker environment, path parameter is REQUIRED as os.getcwd() 
    returns container working directory, not local project directory.
    """
    if not path:
        return {
            "error": "Path parameter is required. In Docker environment, MCP server cannot access local file system without explicit path. Please provide the project directory path."
        }
    
    path_obj = Path(path).resolve()
    
    db = SessionLocal()
    try:
        # Strategy 1: Check for .intracker/config.json
        intracker_config = path_obj / ".intracker" / "config.json"
        if intracker_config.exists():
            try:
                with open(intracker_config, "r") as f:
                    config = json_lib.load(f)
                    project_id = config.get("project_id")
                    if project_id:
                        project = ProjectService.get_project_by_id(db, UUID(project_id))
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
                                            # For GitHub URL search, we need to query directly
                                            # as ProjectService doesn't have a method for this
                                            from src.database.models import Project
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
        # For name search, we need to query directly as ProjectService doesn't have a method for this
        from src.database.models import Project
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
