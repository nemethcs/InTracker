"""MCP Tools for todo management."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.signalr_hub import broadcast_todo_update, broadcast_feature_update
from src.services.todo_service import TodoService
from src.services.feature_service import FeatureService
from src.database.models import ProjectElement


def get_create_todo_tool() -> MCPTool:
    """Get create todo tool definition."""
    return MCPTool(
        name="mcp_create_todo",
        description="Create a new todo item linked to a project element. The todo will be created with status 'new' and can optionally be linked to a feature. Returns the created todo with its ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "elementId": {"type": "string", "description": "Element UUID"},
                "title": {"type": "string", "description": "Todo title"},
                "description": {"type": "string", "description": "Todo description"},
                "featureId": {"type": "string", "description": "Optional feature UUID"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Priority level"},
            },
            "required": ["elementId", "title"],
        },
    )


async def handle_create_todo(
    element_id: str,
    title: str,
    description: Optional[str] = None,
    feature_id: Optional[str] = None,
    priority: Optional[str] = "medium",
) -> dict:
    """Handle create todo tool call."""
    db = SessionLocal()
    try:
        # Get current user ID from MCP API key
        from src.mcp.middleware.auth import get_current_user_id
        user_id = get_current_user_id()
        
        # Use TodoService to create todo
        feature_uuid = UUID(feature_id) if feature_id else None
        todo = TodoService.create_todo(
            db=db,
            element_id=UUID(element_id),
            title=title,
            description=description,
            status="new",
            feature_id=feature_uuid,
            priority=priority or "medium",
            current_user_id=user_id,
        )

        # Get element for project_id and broadcast
        element = db.query(ProjectElement).filter(ProjectElement.id == UUID(element_id)).first()
        if not element:
            return {"error": "Element not found after todo creation"}

        # Get feature progress if linked
        feature_progress = None
        if feature_id:
            from src.services.feature_service import FeatureService
            feature = FeatureService.get_feature_by_id(db, feature_uuid)
            if feature:
                feature_progress = feature.progress_percentage

        # Invalidate cache
        cache_service.clear_pattern(f"project:{element.project_id}:*")
        if feature_id:
            cache_service.delete(f"feature:{feature_id}")

        # Broadcast SignalR update (fire and forget)
        # For MCP-created todos, we don't have a user_id, so use a placeholder
        # The frontend will handle this gracefully
        user_id = todo.assigned_to or todo.created_by
        if user_id:
            import asyncio
            asyncio.create_task(
                broadcast_todo_update(
                    str(element.project_id),
                    str(todo.id),
                    user_id,
                    {
                        "title": todo.title,
                        "status": todo.status,
                        "action": "created"
                    }
                )
            )
        else:
            # If no user_id, still broadcast but with a system user ID
            # Frontend will handle this as a system update
            import asyncio
            # Use a placeholder UUID for system updates (UUID already imported at top of file)
            system_user_id = UUID("00000000-0000-0000-0000-000000000000")
            asyncio.create_task(
                broadcast_todo_update(
                    str(element.project_id),
                    str(todo.id),
                    system_user_id,
                    {
                        "title": todo.title,
                        "status": todo.status,
                        "action": "created"
                    }
                )
            )
        
        # Broadcast feature progress update if feature exists
        if feature_id and feature_progress is not None:
            import asyncio
            # Get feature to include status in broadcast
            feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
            asyncio.create_task(
                broadcast_feature_update(
                    str(element.project_id),
                    feature_id,
                    feature_progress,
                    feature.status if feature else None
                )
            )

        return {
            "id": str(todo.id),
            "title": todo.title,
            "description": todo.description,
            "status": todo.status,
            "element_id": str(todo.element_id),
            "feature_id": str(todo.feature_id) if todo.feature_id else None,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()


def get_update_todo_status_tool() -> MCPTool:
    """Get update todo status tool definition."""
    return MCPTool(
        name="mcp_update_todo_status",
        description="Update a todo's status (new → in_progress → done) with optimistic locking to prevent conflicts. Always provide expectedVersion from the previous read to avoid conflicts. Returns updated todo with new version number.",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "status": {
                    "type": "string",
                    "enum": ["new", "in_progress", "done"],
                    "description": "New status",
                },
                "expectedVersion": {"type": "integer", "description": "Expected version for optimistic locking"},
            },
            "required": ["todoId", "status"],
        },
    )


async def handle_update_todo_status(
    todo_id: str,
    status: str,
    expected_version: Optional[int] = None,
) -> dict:
    """Handle update todo status tool call with validation."""
    from src.mcp.utils.validation import validate_todo_status_transition, ValidationError
    
    db = SessionLocal()
    try:
        # Validate the status transition before updating
        try:
            validate_todo_status_transition(
                db=db,
                todo_id=UUID(todo_id),
                new_status=status,
            )
        except ValidationError as e:
            return {"error": str(e)}
        
        # Use TodoService to update todo status
        updated_todo = TodoService.update_todo_status(
            db=db,
            todo_id=UUID(todo_id),
            status=status,
            expected_version=expected_version,
        )

        if not updated_todo:
            # Check if it was a version conflict
            todo = TodoService.get_todo_by_id(db, UUID(todo_id))
            if todo and expected_version is not None and todo.version != expected_version:
                return {
                    "error": "Conflict",
                    "message": "Todo was modified by another user. Please refresh and try again.",
                    "current_version": todo.version,
                }
            return {"error": "Todo not found"}

        # Get element for project_id and user_id for broadcast
        element = db.query(ProjectElement).filter(ProjectElement.id == updated_todo.element_id).first()
        
        # Get feature progress if linked
        feature_progress = None
        if updated_todo.feature_id:
            feature = FeatureService.get_feature_by_id(db, updated_todo.feature_id)
            if feature:
                feature_progress = feature.progress_percentage

        # Invalidate cache
        if element:
            cache_service.clear_pattern(f"project:{element.project_id}:*")
        if updated_todo.feature_id:
            cache_service.delete(f"feature:{updated_todo.feature_id}")

        # Broadcast SignalR update (fire and forget)
        if element:
            # Get user_id from todo (created_by or assigned_to)
            user_id = updated_todo.assigned_to or updated_todo.created_by
            if user_id:
                import asyncio
                asyncio.create_task(
                    broadcast_todo_update(
                        str(element.project_id),
                        str(updated_todo.id),
                        user_id,
                        {"status": status}
                    )
                )
            else:
                # If no user_id, use system user ID for MCP updates
                import asyncio
                # Use a placeholder UUID for system updates (UUID already imported at top of file)
                system_user_id = UUID("00000000-0000-0000-0000-000000000000")
                asyncio.create_task(
                    broadcast_todo_update(
                        str(element.project_id),
                        str(updated_todo.id),
                        system_user_id,
                        {"status": status}
                    )
                )
            
            # Broadcast feature progress update if feature exists
            if updated_todo.feature_id and feature_progress is not None:
                import asyncio
                # Get feature to include status in broadcast
                feature = FeatureService.get_feature_by_id(db, updated_todo.feature_id)
                asyncio.create_task(
                    broadcast_feature_update(
                        str(element.project_id),
                        str(updated_todo.feature_id),
                        feature_progress,
                        feature.status if feature else None
                    )
                )

        return {
            "id": str(updated_todo.id),
            "status": updated_todo.status,
            "version": updated_todo.version,
        }
    except ValueError as e:
        if "modified by another user" in str(e):
            todo = TodoService.get_todo_by_id(db, UUID(todo_id))
            return {
                "error": "Conflict",
                "message": str(e),
                "current_version": todo.version if todo else None,
            }
        return {"error": str(e)}
    finally:
        db.close()


def get_list_todos_tool() -> MCPTool:
    """Get list todos tool definition."""
    return MCPTool(
        name="mcp_list_todos",
        description="List todos for a project with optional filters. If userId is provided, excludes todos that are in_progress and assigned to other users.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "status": {
                    "type": "string",
                    "enum": ["new", "in_progress", "done"],
                    "description": "Filter by status",
                },
                "featureId": {"type": "string", "description": "Filter by feature ID"},
                "userId": {
                    "type": "string",
                    "description": "Optional: User UUID to filter out todos assigned to other users (in_progress status)",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_list_todos(
    project_id: str,
    status: Optional[str] = None,
    feature_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Handle list todos tool call.
    
    If user_id is provided, excludes todos that are in_progress and assigned to other users.
    """
    cache_key = f"project:{project_id}:todos"
    if status:
        cache_key += f":status:{status}"
    if feature_id:
        cache_key += f":feature:{feature_id}"
    if user_id:
        cache_key += f":user:{user_id}"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use TodoService to get todos by project
        todos, total = TodoService.get_todos_by_project(
            db=db,
            project_id=UUID(project_id),
            status=status,
            skip=0,
            limit=1000,  # Large limit for MCP tools
        )

        # Filter by feature_id if provided
        if feature_id:
            todos = [t for t in todos if t.feature_id == UUID(feature_id)]

        # If user_id is provided, exclude todos that are in_progress and assigned to other users
        # Workflow: new → in_progress → done (simplified)
        if user_id:
            user_uuid = UUID(user_id)
            filtered_todos = []
            for t in todos:
                # All statuses except in_progress are visible to everyone
                if t.status in ["new", "done"]:
                    filtered_todos.append(t)
                elif t.status == "in_progress":
                    # Only show in_progress todos if unassigned or assigned to this user
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
                }
                for t in todos
            ],
            "count": len(todos),
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_assign_todo_tool() -> MCPTool:
    """Get assign todo tool definition."""
    return MCPTool(
        name="mcp_assign_todo",
        description="Assign a todo to a specific user. When a todo is assigned and in 'in_progress' status, it will be hidden from other users' 'next todos' lists. If userId is null, the assignment is cleared (todo becomes unassigned).",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "userId": {"type": "string", "description": "Optional user UUID (auto-assign if null)"},
            },
            "required": ["todoId"],
        },
    )


async def handle_assign_todo(todo_id: str, user_id: Optional[str] = None) -> dict:
    """Handle assign todo tool call."""
    db = SessionLocal()
    try:
        # TODO: Implement load balancing if user_id is None
        # For now, just assign if user_id provided
        if user_id:
            # Use TodoService to update assigned_to
            updated_todo = TodoService.update_todo(
                db=db,
                todo_id=UUID(todo_id),
                assigned_to=UUID(user_id),
            )
            
            if not updated_todo:
                return {"error": "Todo not found"}
            
            todo = updated_todo
        else:
            # Get todo to return current assignment
            todo = TodoService.get_todo_by_id(db, UUID(todo_id))
            if not todo:
                return {"error": "Todo not found"}

        # Invalidate cache
        element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
        if element:
            cache_service.clear_pattern(f"project:{element.project_id}:*")
            
            # Broadcast SignalR update (fire and forget)
            if user_id:  # Only broadcast if assignment changed
                import asyncio
                # Get user_id from todo (assigned_to or created_by)
                broadcast_user_id = todo.assigned_to or todo.created_by
                if not broadcast_user_id:
                    # Use system user ID for MCP updates
                    broadcast_user_id = UUID("00000000-0000-0000-0000-000000000000")
                asyncio.create_task(
                    broadcast_todo_update(
                        str(element.project_id),
                        str(todo.id),
                        broadcast_user_id,
                        {
                            "assigned_to": str(user_id) if user_id else None
                        }
                    )
                )

        return {
            "id": str(todo.id),
            "assigned_to": str(todo.assigned_to) if todo.assigned_to else None,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()


def get_link_todo_to_feature_tool() -> MCPTool:
    """Get link todo to feature tool definition."""
    return MCPTool(
        name="mcp_link_todo_to_feature",
        description="Link or unlink a todo to/from a feature. If featureId is provided, links the todo to that feature. If featureId is null, unlinks the todo from its current feature.",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "featureId": {
                    "type": "string",
                    "description": "Feature UUID to link to, or null to unlink",
                },
                "expectedVersion": {"type": "integer", "description": "Expected version for optimistic locking"},
            },
            "required": ["todoId"],
        },
    )


async def handle_link_todo_to_feature(
    todo_id: str,
    feature_id: Optional[str] = None,
    expected_version: Optional[int] = None,
) -> dict:
    """Handle link todo to feature tool call."""
    from src.services.todo_service import TodoService
    
    db = SessionLocal()
    try:
        todo = TodoService.get_todo_by_id(db, UUID(todo_id))
        if not todo:
            return {"error": "Todo not found"}

        # Use TodoService to update feature_id
        # If expected_version is not provided, use current version
        feature_uuid = UUID(feature_id) if feature_id else None
        updated_todo = TodoService.update_todo(
            db=db,
            todo_id=UUID(todo_id),
            feature_id=feature_uuid,
            expected_version=expected_version if expected_version is not None else todo.version,
        )

        if not updated_todo:
            return {"error": "Todo not found or version conflict"}

        # Get element for project_id and broadcast
        element = db.query(ProjectElement).filter(ProjectElement.id == updated_todo.element_id).first()
        
        # Invalidate cache
        if element:
            cache_service.clear_pattern(f"project:{element.project_id}:*")
        if updated_todo.feature_id:
            cache_service.delete(f"feature:{updated_todo.feature_id}")
        if todo.feature_id:  # Old feature_id
            cache_service.delete(f"feature:{todo.feature_id}")

        # Broadcast SignalR update (fire and forget)
        if element:
            import asyncio
            # Get user_id from todo (assigned_to or created_by)
            user_id = updated_todo.assigned_to or updated_todo.created_by
            if not user_id:
                # Use system user ID for MCP updates
                user_id = UUID("00000000-0000-0000-0000-000000000000")
            
            asyncio.create_task(
                broadcast_todo_update(
                    str(element.project_id),
                    str(updated_todo.id),
                    user_id,
                    {
                        "feature_id": str(feature_id) if feature_id else None
                    }
                )
            )
            
            # Broadcast feature progress update for both old and new features
            if updated_todo.feature_id:
                feature = FeatureService.get_feature_by_id(db, updated_todo.feature_id)
                if feature:
                    progress = FeatureService.calculate_feature_progress(db, updated_todo.feature_id)
                    asyncio.create_task(
                        broadcast_feature_update(
                            str(element.project_id),
                            str(updated_todo.feature_id),
                            progress["percentage"],
                            feature.status
                        )
                    )
            
            # Also update old feature if it was unlinked
            if todo.feature_id and not updated_todo.feature_id:
                old_feature = FeatureService.get_feature_by_id(db, todo.feature_id)
                if old_feature:
                    progress = FeatureService.calculate_feature_progress(db, todo.feature_id)
                    asyncio.create_task(
                        broadcast_feature_update(
                            str(element.project_id),
                            str(todo.feature_id),
                            progress["percentage"],
                            old_feature.status
                        )
                    )

        return {
            "id": str(updated_todo.id),
            "feature_id": str(updated_todo.feature_id) if updated_todo.feature_id else None,
            "version": updated_todo.version,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()
