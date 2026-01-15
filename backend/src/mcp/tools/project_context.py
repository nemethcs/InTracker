"""MCP Tools for project context retrieval."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.project_service import ProjectService
from src.services.element_service import ElementService
from src.services.feature_service import FeatureService
from src.services.todo_service import TodoService
from src.services.session_service import SessionService


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
