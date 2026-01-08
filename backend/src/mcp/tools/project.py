"""MCP Tools for project context."""
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
from src.services.element_service import ElementService
from src.services.feature_service import FeatureService
from src.services.todo_service import TodoService
from src.services.session_service import SessionService
from src.services.signalr_hub import broadcast_project_update
from src.database.models import User
from sqlalchemy import func, and_, or_
import json


def get_project_context_tool() -> MCPTool:
    """Get project context tool definition."""
    return MCPTool(
        name="mcp_get_project_context",
        description="Get comprehensive project information with optional filtering for large projects. Returns project metadata, element structure tree, features, active todos (new/in_progress/done), and cached resume context. Use optional parameters to reduce response size for large projects. Use summaryOnly=true for quick overview with just statistics.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "includeFeatures": {
                    "type": "boolean",
                    "description": "Include features list (default: true). Set to false to exclude features from response.",
                    "default": True,
                },
                "includeTodos": {
                    "type": "boolean",
                    "description": "Include active todos list (default: true). Set to false to exclude todos from response.",
                    "default": True,
                },
                "includeStructure": {
                    "type": "boolean",
                    "description": "Include element structure tree (default: true). Set to false to exclude structure from response.",
                    "default": True,
                },
                "includeResumeContext": {
                    "type": "boolean",
                    "description": "Include resume context (default: true). Set to false to exclude resume context from response.",
                    "default": True,
                },
                "featuresLimit": {
                    "type": "integer",
                    "description": "Maximum number of features to return (default: 20). Use 0 for no limit. Lower values improve performance for large projects.",
                    "default": 20,
                },
                "todosLimit": {
                    "type": "integer",
                    "description": "Maximum number of active todos to return (default: 50). Use 0 for no limit. Lower values improve performance for large projects.",
                    "default": 50,
                },
                "summaryOnly": {
                    "type": "boolean",
                    "description": "Return only summary statistics (counts) instead of full data (default: false). Useful for quick overviews without loading all details.",
                    "default": False,
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_get_project_context(
    project_id: str,
    include_features: bool = True,
    include_todos: bool = True,
    include_structure: bool = True,
    include_resume_context: bool = True,
    features_limit: int = 20,
    todos_limit: int = 50,
    summary_only: bool = False,
) -> dict:
    """Handle get project context tool call with optional filtering for large projects."""
    # Build cache key based on parameters to prevent cache collisions
    # Use string concatenation for deterministic cache keys
    cache_key_parts = [
        f"project:{project_id}:context",
        f"f:{int(include_features)}",
        f"t:{int(include_todos)}",
        f"s:{int(include_structure)}",
        f"r:{int(include_resume_context)}",
        f"fl:{features_limit}",
        f"tl:{todos_limit}",
        f"sum:{int(summary_only)}",
    ]
    cache_key = ":".join(cache_key_parts)
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}

        # Always include project metadata
        project_data = {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "cursor_instructions": project.cursor_instructions,
        }

        # If summary_only, return just counts
        if summary_only:
            # Get counts efficiently
            from sqlalchemy import func
            from src.database.models import Feature, Todo, ProjectElement
            
            feature_count = db.query(func.count(Feature.id)).filter(Feature.project_id == UUID(project_id)).scalar()
            todo_count = (
                db.query(func.count(Todo.id))
                .join(ProjectElement)
                .filter(
                    ProjectElement.project_id == UUID(project_id),
                    Todo.status.in_(["new", "in_progress", "done"])
                )
                .scalar()
            )
            element_count = db.query(func.count(ProjectElement.id)).filter(ProjectElement.project_id == UUID(project_id)).scalar()
            
            context = {
                "project": project_data,
                "summary": {
                    "feature_count": feature_count,
                    "active_todo_count": todo_count,
                    "element_count": element_count,
                },
            }
            
            # Cache summary for 5 minutes
            cache_service.set(cache_key, context, ttl=300)
            return context

        # Build response based on include flags
        context = {"project": project_data}

        # Include structure if requested
        if include_structure:
            elements = ElementService.get_project_elements_tree(db, UUID(project_id))
            context["structure"] = [
                {
                    "id": str(e.id),
                    "type": e.type,
                    "title": e.title,
                    "description": e.description,
                    "status": e.status,
                    "parent_id": str(e.parent_id) if e.parent_id else None,
                }
                for e in elements
            ]

        # Include features if requested
        if include_features:
            # Get features with limit
            features, total_features = FeatureService.get_features_by_project(
                db=db,
                project_id=UUID(project_id),
                status=None,
                skip=0,
                limit=features_limit if features_limit > 0 else None,
            )
            context["features"] = [
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
            ]
            # Include total count if limited
            if features_limit > 0 and total_features > len(features):
                context["features_total"] = total_features
                context["features_shown"] = len(features)

        # Include todos if requested
        if include_todos:
            # Get active todos with limit
            todos, total_todos = TodoService.get_todos_by_project(
                db=db,
                project_id=UUID(project_id),
                status=None,  # We'll filter manually for active statuses
                skip=0,
                limit=todos_limit if todos_limit > 0 else None,
            )
            # Filter for active statuses (todos: new, in_progress, done - tested/merged are feature-level)
            active_todos = [t for t in todos if t.status in ["new", "in_progress", "done"]]
            
            # Apply limit after filtering
            if todos_limit > 0 and len(active_todos) > todos_limit:
                active_todos = active_todos[:todos_limit]
            
            context["active_todos"] = [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "element_id": str(t.element_id),
                    "feature_id": str(t.feature_id) if t.feature_id else None,
                }
                for t in active_todos
            ]
            # Include total count if limited
            if todos_limit > 0:
                # Count all active todos for total
                from sqlalchemy import func
                from src.database.models import Todo, ProjectElement
                total_active = (
                    db.query(func.count(Todo.id))
                    .join(ProjectElement)
                    .filter(
                        ProjectElement.project_id == UUID(project_id),
                        Todo.status.in_(["new", "in_progress", "done"])
                    )
                    .scalar()
                )
                if total_active > len(active_todos):
                    context["active_todos_total"] = total_active
                    context["active_todos_shown"] = len(active_todos)

        # Include resume context if requested
        if include_resume_context:
            context["resume_context"] = project.resume_context or {}

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
    If user_id is not provided, automatically extracts it from MCP API key if available.
    """
    from src.mcp.middleware.auth import get_current_user_id
    
    # Auto-extract user_id from MCP API key if not provided
    if not user_id:
        current_user_id = get_current_user_id()
        if current_user_id:
            user_id = str(current_user_id)
    
    cache_key = f"project:{project_id}:resume"
    if user_id:
        cache_key += f":user:{user_id}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}

        resume_context = project.resume_context or {}

        # If resume context exists, return it (but filter if user_id provided)
        if resume_context:
            # If user_id is provided, filter the next_todos in resume_context
            if user_id and "now" in resume_context and "next_todos" in resume_context["now"]:
                # Use TodoService to get filtered todos
                all_todos, _ = TodoService.get_todos_by_project(
                    db=db,
                    project_id=UUID(project_id),
                    status=None,
                    skip=0,
                    limit=1000,
                )
                # Filter for new and in_progress, and exclude in_progress assigned to other users
                user_uuid = UUID(user_id)
                next_todos = [
                    t for t in all_todos
                    if t.status in ["new", "in_progress"]
                    and (t.status == "new" or t.assigned_to is None or t.assigned_to == user_uuid)
                ]
                # Sort and limit
                next_todos = sorted(next_todos, key=lambda t: (t.position or 0, t.created_at))[:3]
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
        # Get last session - query directly as SessionService doesn't have this method
        from src.database.models import Session as SessionModel
        last_session = db.query(SessionModel).filter(
            SessionModel.project_id == UUID(project_id),
            SessionModel.ended_at.isnot(None),
        ).order_by(SessionModel.ended_at.desc()).first()

        # Use TodoService to get next todos
        all_todos, _ = TodoService.get_todos_by_project(
            db=db,
            project_id=UUID(project_id),
            status=None,
            skip=0,
            limit=1000,
        )
        
        # Filter for new and in_progress todos
        if user_id:
            user_uuid = UUID(user_id)
            next_todos = [
                t for t in all_todos
                if t.status in ["new", "in_progress"]
                and (t.status == "new" or t.assigned_to is None or t.assigned_to == user_uuid)
            ]
        else:
            # If no user_id, only show "new" todos
            next_todos = [t for t in all_todos if t.status == "new"]
        
        # Sort and limit
        next_todos = sorted(next_todos, key=lambda t: (t.position or 0, t.created_at))[:3]

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

    db = SessionLocal()
    try:
        # Use ElementService to get elements
        elements = ElementService.get_project_elements_tree(db, UUID(project_id))

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
                    "enum": ["new", "in_progress", "done"],
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
    If user_id is not provided, automatically extracts it from MCP API key if available.
    """
    from src.mcp.middleware.auth import get_current_user_id
    
    # Auto-extract user_id from MCP API key if not provided
    if not user_id:
        current_user_id = get_current_user_id()
        if current_user_id:
            user_id = str(current_user_id)
    
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

    db = SessionLocal()
    try:
        # Use TodoService to get todos by project
        todos, _ = TodoService.get_todos_by_project(
            db=db,
            project_id=UUID(project_id),
            status=status if status else None,
            skip=0,
            limit=1000,
        )

        # Filter by feature_id if provided
        if feature_id:
            todos = [t for t in todos if t.feature_id == UUID(feature_id)]
        
        # Filter for active statuses if no status filter
        if not status:
            todos = [t for t in todos if t.status in ["new", "in_progress", "done"]]

        # If user_id is provided, exclude todos that are in_progress and assigned to other users
        if user_id:
            user_uuid = UUID(user_id)
            filtered_todos = []
            for t in todos:
                if t.status in ["new", "done"]:
                    filtered_todos.append(t)
                elif t.status == "in_progress":
                    if t.assigned_to is None or t.assigned_to == user_uuid:
                        filtered_todos.append(t)
            todos = filtered_todos

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
    db = SessionLocal()
    try:
        # Use ProjectService to create project
        project = ProjectService.create_project(
            db=db,
            team_id=UUID(team_id),
            name=name,
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
        
        # Use ProjectService to update project
        project = ProjectService.update_project(
            db=db,
            project_id=UUID(project_id),
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


def get_enforce_workflow_tool() -> MCPTool:
    """Get enforce workflow tool definition."""
    return MCPTool(
        name="mcp_enforce_workflow",
        description="""MANDATORY: Call this at the START of EVERY session to ensure proper workflow.
        
        This tool automatically:
        1. Identifies the current project (by path or auto-detection)
        2. Loads resume context (Last/Now/Blockers/Constraints)
        3. Loads cursor rules (project-specific rules)
        4. Returns a workflow checklist of what you MUST do
        
        ALWAYS call this first before doing any work! This ensures you never forget the workflow.
        
        If no project is found, it will return instructions to create one first.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Current working directory path (optional, auto-detected if not provided)",
                },
            },
        },
    )


async def handle_enforce_workflow(path: Optional[str] = None) -> dict:
    """Handle enforce workflow tool call.
    
    This function enforces the InTracker workflow by:
    1. Identifying the project
    2. Loading resume context
    3. Loading cursor rules
    4. Returning a workflow checklist
    """
    # Step 1: Identify project
    project_info = await handle_identify_project_by_path(path)
    
    if not project_info.get("project_id"):
        return {
            "error": "No project found",
            "message": "No project found in current directory. Create one first with mcp_create_project",
            "workflow": [
                "1. Create project: mcp_create_project(name, teamId, description?, ...)",
                "2. Call mcp_enforce_workflow() again after project creation"
            ],
            "workflow_enforced": False
        }
    
    project_id = project_info["project_id"]
    
    # Step 2: Get resume context
    resume_context = await handle_get_resume_context(project_id, None)
    
    # Step 3: Load cursor rules (try to load, but don't fail if it doesn't exist)
    cursor_rules_loaded = False
    cursor_rules_error = None
    try:
        cursor_rules_result = await handle_load_cursor_rules(project_id, path)
        cursor_rules_loaded = bool(cursor_rules_result.get("rules") or cursor_rules_result.get("content"))
    except Exception as e:
        cursor_rules_error = str(e)
        # Don't fail if cursor rules can't be loaded
    
    # Step 4: Build workflow checklist
    workflow_checklist = [
        "✅ Project identified",
        "✅ Resume context loaded",
        f"{'✅' if cursor_rules_loaded else '⚠️'} Cursor rules {'loaded' if cursor_rules_loaded else 'not found (will be generated if needed)'}",
        "📋 Next: Work on todos from resume_context.now.todos",
        "📋 Next: Update todo status with mcp_update_todo_status(todoId, 'in_progress') when starting",
        "📋 Next: Follow git workflow before committing (git status → git diff → git add → git commit → git push)",
        "📋 Next: Update todo status after commit: mcp_update_todo_status(todoId, 'tested') (only if tested!)",
        "📋 Next: Update todo status after merge: mcp_update_todo_status(todoId, 'done') (only if tested AND merged!)",
        "📋 Next: Use commit message format: {type}({scope}): {description} [feature:{featureId}]"
    ]
    
    # Extract next todos from resume context
    next_todos = []
    if isinstance(resume_context, dict):
        now = resume_context.get("now", {})
        if isinstance(now, dict):
            todos = now.get("todos", [])
            if isinstance(todos, list):
                next_todos = todos[:5]  # Get first 5 todos
    
    return {
        "workflow_enforced": True,
        "project": {
            "id": project_id,
            "name": project_info.get("name"),
            "description": project_info.get("description"),
            "status": project_info.get("status"),
        },
        "resume_context": resume_context,
        "cursor_rules_loaded": cursor_rules_loaded,
        "cursor_rules_error": cursor_rules_error,
        "workflow_checklist": workflow_checklist,
        "next_todos": next_todos,
        "active_elements": resume_context.get("now", {}).get("active_elements", []) if isinstance(resume_context, dict) else [],
        "blockers": resume_context.get("blockers", []) if isinstance(resume_context, dict) else [],
        "constraints": resume_context.get("constraints", []) if isinstance(resume_context, dict) else [],
        "reminder": """⚠️ WORKFLOW REMINDER:
        
        MANDATORY steps for this session:
        1. ✅ Project identified - DONE
        2. ✅ Resume context loaded - DONE
        3. ✅ Cursor rules loaded - DONE
        4. 📋 Work on todos from resume_context.now.todos
        5. 📋 Update todo status: in_progress → tested → done
        6. 📋 Follow git workflow: status → diff → add → commit → push
        7. 📋 Use commit format: {type}({scope}): {description} [feature:{featureId}]
        
        NEVER skip these steps!"""
    }
