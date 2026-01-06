"""MCP Tools for todo management."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.services.cache import cache_service
from src.models import Todo, ProjectElement, Feature
from sqlalchemy import func


def get_create_todo_tool() -> MCPTool:
    """Get create todo tool definition."""
    return MCPTool(
        name="mcp_create_todo",
        description="Create a new todo and optionally link to feature",
        inputSchema={
            "type": "object",
            "properties": {
                "elementId": {"type": "string", "description": "Element UUID"},
                "title": {"type": "string", "description": "Todo title"},
                "description": {"type": "string", "description": "Todo description"},
                "featureId": {"type": "string", "description": "Optional feature UUID"},
                "estimatedEffort": {"type": "integer", "description": "Estimated effort in hours"},
            },
            "required": ["elementId", "title"],
        },
    )


async def handle_create_todo(
    element_id: str,
    title: str,
    description: Optional[str] = None,
    feature_id: Optional[str] = None,
    estimated_effort: Optional[int] = None,
) -> dict:
    """Handle create todo tool call."""
    db = get_db_session()
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
            status="todo",
            estimated_effort=estimated_effort,
            version=1,
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)

        # Update feature progress if linked
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

        # Invalidate cache
        cache_service.clear_pattern(f"project:{element.project_id}:*")
        if feature_id:
            cache_service.delete(f"feature:{feature_id}")

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
        description="Update todo status with optimistic locking",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "blocked", "done"],
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
    db = get_db_session()
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

        # Update feature progress if linked
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

        # Invalidate cache
        element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
        if element:
            cache_service.clear_pattern(f"project:{element.project_id}:*")
        if todo.feature_id:
            cache_service.delete(f"feature:{todo.feature_id}")

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
        description="List todos for a project with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "blocked", "done"],
                    "description": "Filter by status",
                },
                "featureId": {"type": "string", "description": "Filter by feature ID"},
            },
            "required": ["projectId"],
        },
    )


async def handle_list_todos(
    project_id: str,
    status: Optional[str] = None,
    feature_id: Optional[str] = None,
) -> dict:
    """Handle list todos tool call."""
    cache_key = f"project:{project_id}:todos"
    if status:
        cache_key += f":status:{status}"
    if feature_id:
        cache_key += f":feature:{feature_id}"
    
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
        if feature_id:
            query = query.filter(Todo.feature_id == UUID(feature_id))

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
        description="Assign todo to a user (auto-assign if userId is null)",
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
    db = get_db_session()
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
