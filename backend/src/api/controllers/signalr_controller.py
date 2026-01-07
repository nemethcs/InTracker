"""SignalR WebSocket hub controller."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from typing import Optional
from uuid import UUID
from src.services.signalr_hub import handle_websocket, connection_manager
from src.api.middleware.auth import get_current_user
from src.database.base import get_db
from sqlalchemy.orm import Session
from src.database.models import User

router = APIRouter(prefix="/signalr", tags=["signalr"])


@router.websocket("/hub")
async def websocket_hub(
    websocket: WebSocket,
    token: Optional[str] = Query(None, alias="access_token"),
):
    """
    SignalR-compatible WebSocket hub endpoint.
    
    Supports:
    - Connection with JWT token authentication
    - Project groups (join/leave)
    - Real-time event broadcasting
    - User activity tracking
    """
    await handle_websocket(websocket, token)


@router.get("/hub/negotiate")
async def negotiate():
    """
    SignalR negotiation endpoint (for compatibility).
    Returns connection info for SignalR client.
    """
    return {
        "url": "/signalr/hub",  # Updated to match router prefix
        "accessToken": None,  # Token should be passed in query string
        "connectionToken": None,
        "availableTransports": [
            {
                "transport": "WebSockets",
                "transferFormats": ["Text", "Binary"]
            }
        ]
    }


@router.get("/hub/projects/{project_id}/active-users")
async def get_active_users(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of active users for a project.
    Returns user information for all users currently connected to the project.
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    # Get active user IDs from connection manager
    active_user_ids = connection_manager.get_active_users_for_project(project_id)
    
    # Fetch user details from database
    users = db.query(User).filter(User.id.in_(active_user_ids)).all()
    
    return {
        "projectId": project_id,
        "activeUsers": [
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatarUrl": user.avatar_url
            }
            for user in users
        ],
        "count": len(users)
    }


