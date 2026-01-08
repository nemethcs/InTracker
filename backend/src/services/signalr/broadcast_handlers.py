"""Broadcast handlers for SignalR real-time updates."""
from typing import Optional
from uuid import UUID
from .connection_manager import connection_manager


async def broadcast_todo_update(project_id: str, todo_id: str, user_id: UUID, changes: dict):
    """Broadcast todo update to project group."""
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "todoUpdated",
        "arguments": [{
            "todoId": todo_id,
            "projectId": project_id,
            "userId": str(user_id),
            "changes": changes
        }]
    }
    await connection_manager.broadcast_to_project(project_id, message)


async def broadcast_feature_update(project_id: str, feature_id: str, progress: int, status: Optional[str] = None):
    """Broadcast feature progress and status update to project group."""
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "featureUpdated",
        "arguments": [{
            "featureId": feature_id,
            "projectId": project_id,
            "progress": progress,
            "status": status
        }]
    }
    await connection_manager.broadcast_to_project(project_id, message)


async def broadcast_project_update(project_id: str, changes: dict):
    """Broadcast project update to project group."""
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "projectUpdated",
        "arguments": [{
            "projectId": project_id,
            "changes": changes
        }]
    }
    await connection_manager.broadcast_to_project(project_id, message)


async def broadcast_session_start(project_id: str, user_id: str):
    """Broadcast session start event to project group.
    
    This notifies all clients that a user has started working on the project
    (opened an MCP session), so they can update the active users list.
    """
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "sessionStarted",
        "arguments": [{
            "userId": user_id,
            "projectId": project_id
        }]
    }
    await connection_manager.broadcast_to_project(project_id, message)


async def broadcast_session_end(project_id: str, user_id: str):
    """Broadcast session end event to project group.
    
    This notifies all clients that a user has stopped working on the project
    (ended an MCP session), so they can update the active users list.
    """
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "sessionEnded",
        "arguments": [{
            "userId": user_id,
            "projectId": project_id
        }]
    }
    await connection_manager.broadcast_to_project(project_id, message)


async def broadcast_idea_update(team_id: str, idea_id: str, changes: dict):
    """Broadcast idea update to team members.
    
    Ideas are team-level, so we broadcast to all connections and let the
    frontend filter by team_id.
    """
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "ideaUpdated",
        "arguments": [{
            "ideaId": idea_id,
            "teamId": team_id,
            "changes": changes
        }]
    }
    await connection_manager.broadcast_to_team(team_id, message)
