"""MCP Tools for project context."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.services.cache import cache_service
from src.models import Project, ProjectElement, Feature, Todo, Session as SessionModel
from sqlalchemy import func
import json


def get_project_context_tool() -> MCPTool:
    """Get project context tool definition."""
    return MCPTool(
        name="mcp_get_project_context",
        description="Get full project context including structure, features, todos, and resume context",
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

        # Get active todos
        todos = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
            Todo.status.in_(["todo", "in_progress", "blocked"]),
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
        description="Get resume context package (Last, Now, Blockers, Constraints) for a project",
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


async def handle_get_resume_context(project_id: str) -> dict:
    """Handle get resume context tool call."""
    cache_key = f"project:{project_id}:resume"
    
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

        # If resume context exists, return it
        if resume_context:
            cache_service.set(cache_key, resume_context, ttl=60)  # 1 min TTL
            return resume_context

        # Otherwise, generate basic resume context
        # Get last session
        last_session = db.query(SessionModel).filter(
            SessionModel.project_id == UUID(project_id),
            SessionModel.ended_at.isnot(None),
        ).order_by(SessionModel.ended_at.desc()).first()

        # Get next todos
        next_todos = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
            Todo.status == "todo",
        ).order_by(Todo.position, Todo.created_at).limit(3).all()

        # Get blocked todos
        blocked_todos = db.query(Todo).join(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
            Todo.status == "blocked",
        ).all()

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
                "blocked_todos": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "blocker_reason": t.blocker_reason,
                    }
                    for t in blocked_todos
                ],
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
        description="Get hierarchical element tree for a project",
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
        description="Get active todos for a project with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "blocked", "done"],
                    "description": "Filter by status",
                },
                "featureId": {
                    "type": "string",
                    "description": "Filter by feature ID",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_get_active_todos(
    project_id: str,
    status: Optional[str] = None,
    feature_id: Optional[str] = None,
) -> dict:
    """Handle get active todos tool call."""
    cache_key = f"project:{project_id}:todos:active"
    if status:
        cache_key += f":status:{status}"
    if feature_id:
        cache_key += f":feature:{feature_id}"
    
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
            query = query.filter(Todo.status.in_(["todo", "in_progress", "blocked"]))

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
