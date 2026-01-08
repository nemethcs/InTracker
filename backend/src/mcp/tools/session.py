"""MCP Tools for session management."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.session_service import SessionService


def get_start_session_tool() -> MCPTool:
    """Get start session tool definition."""
    return MCPTool(
        name="mcp_start_session",
        description="Start a new work session",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "goal": {"type": "string", "description": "Session goal"},
                "featureIds": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional feature IDs to focus on",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_start_session(
    project_id: str,
    goal: Optional[str] = None,
    feature_ids: Optional[List[str]] = None,
    auto_enforce_workflow: bool = True,
) -> dict:
    """Handle start session tool call.
    
    If auto_enforce_workflow is True (default), automatically enforces the workflow
    by calling mcp_enforce_workflow to ensure proper project setup.
    
    The user_id is automatically extracted from the MCP API key if available.
    """
    from src.mcp.middleware.auth import get_current_user_id
    
    db = SessionLocal()
    try:
        # Get user_id from MCP API key (if available)
        user_id = get_current_user_id()
        
        # Use SessionService to create session
        feature_uuid_list = [UUID(fid) for fid in (feature_ids or [])]
        session = SessionService.create_session(
            db=db,
            project_id=UUID(project_id),
            user_id=user_id,  # Pass user_id from MCP API key
            goal=goal,
            feature_ids=feature_uuid_list,
        )

        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        
        # Auto-enforce workflow if requested (default: True)
        workflow_info = None
        if auto_enforce_workflow:
            try:
                from src.mcp.tools.project import handle_enforce_workflow
                workflow_info = await handle_enforce_workflow(None)
            except Exception as e:
                # Don't fail session creation if workflow enforcement fails
                workflow_info = {
                    "error": f"Failed to enforce workflow: {str(e)}",
                    "workflow_enforced": False
                }

        result = {
            "id": str(session.id),
            "project_id": str(session.project_id),
            "goal": session.goal,
            "started_at": session.started_at.isoformat(),
            "workflow_enforced": workflow_info.get("workflow_enforced", False) if workflow_info else False,
        }
        
        # Include workflow info if available
        if workflow_info and workflow_info.get("workflow_enforced"):
            result["workflow"] = {
                "checklist": workflow_info.get("workflow_checklist", []),
                "next_todos": workflow_info.get("next_todos", []),
                "reminder": workflow_info.get("reminder", ""),
            }
        
        return result
    finally:
        db.close()


def get_update_session_tool() -> MCPTool:
    """Get update session tool definition."""
    return MCPTool(
        name="mcp_update_session",
        description="Update session with completed todos, features, and notes",
        inputSchema={
            "type": "object",
            "properties": {
                "sessionId": {"type": "string", "description": "Session UUID"},
                "completedTodos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Completed todo IDs",
                },
                "completedFeatures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Completed feature IDs",
                },
                "notes": {"type": "string", "description": "Session notes"},
            },
            "required": ["sessionId"],
        },
    )


async def handle_update_session(
    session_id: str,
    completed_todos: Optional[List[str]] = None,
    completed_features: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> dict:
    """Handle update session tool call."""
    db = SessionLocal()
    try:
        # Use SessionService to update session
        todo_uuid_list = [UUID(tid) for tid in completed_todos] if completed_todos is not None else None
        feature_uuid_list = [UUID(fid) for fid in completed_features] if completed_features is not None else None
        
        session = SessionService.update_session(
            db=db,
            session_id=UUID(session_id),
            todos_completed=todo_uuid_list,
            features_completed=feature_uuid_list,
            notes=notes,
        )
        
        if not session:
            return {"error": "Session not found"}

        # Invalidate cache
        cache_service.clear_pattern(f"project:{session.project_id}:*")

        return {
            "id": str(session.id),
            "todos_completed": [str(tid) for tid in session.todos_completed],
            "features_completed": [str(fid) for fid in session.features_completed],
            "notes": session.notes,
        }
    finally:
        db.close()


def get_end_session_tool() -> MCPTool:
    """Get end session tool definition."""
    return MCPTool(
        name="mcp_end_session",
        description="End session and generate summary",
        inputSchema={
            "type": "object",
            "properties": {
                "sessionId": {"type": "string", "description": "Session UUID"},
                "summary": {"type": "string", "description": "Optional custom summary"},
            },
            "required": ["sessionId"],
        },
    )


async def handle_end_session(session_id: str, summary: Optional[str] = None) -> dict:
    """Handle end session tool call."""
    db = SessionLocal()
    try:
        # Use SessionService to end session
        session = SessionService.end_session(
            db=db,
            session_id=UUID(session_id),
            summary=summary,
        )
        
        if not session:
            return {"error": "Session not found"}

        # Invalidate cache
        cache_service.clear_pattern(f"project:{session.project_id}:*")
        cache_service.delete(f"project:{session.project_id}:resume")

        return {
            "id": str(session.id),
            "summary": session.summary,
            "ended_at": session.ended_at.isoformat(),
        }
    finally:
        db.close()
