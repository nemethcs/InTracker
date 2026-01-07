"""MCP Tools for todo management."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.signalr_hub import broadcast_todo_update, broadcast_feature_update
from src.database.models import Todo, ProjectElement, Feature
from sqlalchemy import func, or_, and_


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
        # Verify element exists
        element = db.query(ProjectElement).filter(ProjectElement.id == UUID(element_id)).first()
        if not element:
            return {"error": "Element not found"}

        todo = Todo(
            element_id=UUID(element_id),
            feature_id=UUID(feature_id) if feature_id else None,
            title=title,
            description=description,
            status="new",
            priority=priority or "medium",
            version=1,
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)

        # Update feature progress if linked
        feature_progress = None
        if feature_id:
            feature = db.query(Feature).filter(Feature.id == UUID(feature_id)).first()
            if feature:
                total = db.query(func.count(Todo.id)).filter(Todo.feature_id == UUID(feature_id)).scalar()
                completed = (
                    db.query(func.count(Todo.id))
                    .filter(Todo.feature_id == UUID(feature_id), Todo.status == "done")
                    .scalar()
                )
                percentage = int((completed / total * 100)) if total > 0 else 0
                feature.total_todos = total
                feature.completed_todos = completed
                feature.progress_percentage = percentage
                db.commit()
                feature_progress = percentage

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
        elif element:
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
            asyncio.create_task(
                broadcast_feature_update(
                    str(element.project_id),
                    feature_id,
                    feature_progress
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
    finally:
        db.close()


def get_update_todo_status_tool() -> MCPTool:
    """Get update todo status tool definition."""
    return MCPTool(
        name="mcp_update_todo_status",
        description="Update a todo's status (new → in_progress → tested → done) with optimistic locking to prevent conflicts. Always provide expectedVersion from the previous read to avoid conflicts. Returns updated todo with new version number.",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "status": {
                    "type": "string",
                    "enum": ["new", "in_progress", "tested", "done"],
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
    """Handle update todo status tool call."""
    db = SessionLocal()
    try:
        todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
        if not todo:
            return {"error": "Todo not found"}

        # Optimistic locking check
        if expected_version is not None and todo.version != expected_version:
            return {
                "error": "Conflict",
                "message": "Todo was modified by another user. Please refresh and try again.",
                "current_version": todo.version,
            }

        old_status = todo.status
        todo.status = status
        todo.version += 1

        # Update completed_at
        from datetime import datetime
        if status == "done" and old_status != "done":
            todo.completed_at = datetime.utcnow()
        elif status != "done" and old_status == "done":
            todo.completed_at = None

        db.commit()
        db.refresh(todo)

        # Get element for project_id and user_id for broadcast
        element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
        
        # Update feature progress if linked
        feature_progress = None
        if todo.feature_id:
            feature = db.query(Feature).filter(Feature.id == todo.feature_id).first()
            if feature:
                total = db.query(func.count(Todo.id)).filter(Todo.feature_id == todo.feature_id).scalar()
                completed = (
                    db.query(func.count(Todo.id))
                    .filter(Todo.feature_id == todo.feature_id, Todo.status == "done")
                    .scalar()
                )
                percentage = int((completed / total * 100)) if total > 0 else 0
                feature.total_todos = total
                feature.completed_todos = completed
                feature.progress_percentage = percentage
                db.commit()
                feature_progress = percentage

        # Invalidate cache
        if element:
            cache_service.clear_pattern(f"project:{element.project_id}:*")
        if todo.feature_id:
            cache_service.delete(f"feature:{todo.feature_id}")

        # Broadcast SignalR update (fire and forget)
        if element:
            # Get user_id from todo (created_by or assigned_to)
            user_id = todo.assigned_to or todo.created_by
            if user_id:
                import asyncio
                asyncio.create_task(
                    broadcast_todo_update(
                        str(element.project_id),
                        str(todo.id),
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
                        str(todo.id),
                        system_user_id,
                        {"status": status}
                    )
                )
            
            # Broadcast feature progress update if feature exists
            if todo.feature_id and feature_progress is not None:
                asyncio.create_task(
                    broadcast_feature_update(
                        str(element.project_id),
                        str(todo.feature_id),
                        feature_progress
                    )
                )

        return {
            "id": str(todo.id),
            "status": todo.status,
            "version": todo.version,
        }
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
                    "enum": ["new", "in_progress", "tested", "done"],
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
        query = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
        )

        if status:
            query = query.filter(Todo.status == status)
        if feature_id:
            query = query.filter(Todo.feature_id == UUID(feature_id))

        # If user_id is provided, exclude todos that are in_progress and assigned to other users
        if user_id:
            from sqlalchemy import or_, and_
            query = query.filter(
                or_(
                    Todo.status == "new",  # New todos are always available
                    Todo.status == "tested",  # Tested todos are always available
                    Todo.status == "done",  # Done todos are always available
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
        todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
        if not todo:
            return {"error": "Todo not found"}

        # TODO: Implement load balancing if user_id is None
        # For now, just assign if user_id provided
        if user_id:
            todo.assigned_to = UUID(user_id)
            todo.version += 1
            db.commit()

        # Invalidate cache
        element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
        if element:
            cache_service.clear_pattern(f"project:{element.project_id}:*")

        return {
            "id": str(todo.id),
            "assigned_to": str(todo.assigned_to) if todo.assigned_to else None,
        }
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

        return {
            "id": str(updated_todo.id),
            "feature_id": str(updated_todo.feature_id) if updated_todo.feature_id else None,
            "version": updated_todo.version,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()
