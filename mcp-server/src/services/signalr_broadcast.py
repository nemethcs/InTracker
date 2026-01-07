"""SignalR broadcast service for MCP server."""
import httpx
import os
from typing import Optional
from uuid import UUID
from src.config import settings


# Determine backend URL based on environment
# In Docker, use service name; locally or from host, use localhost
def get_backend_url() -> str:
    """Get backend API URL based on environment."""
    # Check if BACKEND_API_URL is set in config
    if settings.BACKEND_API_URL:
        return settings.BACKEND_API_URL
    
    # Check if we're in Docker (backend service available)
    # Docker containers can reach each other by service name
    if os.path.exists("/.dockerenv"):
        return "http://backend:3000"
    else:
        # Local development - use localhost
        return "http://localhost:3000"


async def broadcast_todo_update(
    project_id: str,
    todo_id: str,
    user_id: UUID,
    changes: dict,
) -> bool:
    """Broadcast todo update via SignalR by calling backend API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            backend_url = get_backend_url()
            response = await client.post(
                f"{backend_url}/signalr/hub/broadcast/todo-update",
                params={
                    "project_id": project_id,
                    "todo_id": todo_id,
                    "user_id": str(user_id),
                    "api_key": settings.MCP_API_KEY or "test",
                },
                json=changes,
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"⚠️  Failed to broadcast todo update: {e}")
        return False


async def broadcast_feature_update(
    project_id: str,
    feature_id: str,
    progress: int,
) -> bool:
    """Broadcast feature progress update via SignalR by calling backend API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            backend_url = get_backend_url()
            response = await client.post(
                f"{backend_url}/signalr/hub/broadcast/feature-update",
                params={
                    "project_id": project_id,
                    "feature_id": feature_id,
                    "progress": progress,
                    "api_key": settings.MCP_API_KEY or "test",
                },
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"⚠️  Failed to broadcast feature update: {e}")
        return False


async def broadcast_project_update(
    project_id: str,
    changes: dict,
) -> bool:
    """Broadcast project update via SignalR by calling backend API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            backend_url = get_backend_url()
            response = await client.post(
                f"{backend_url}/signalr/hub/broadcast/project-update",
                params={
                    "project_id": project_id,
                    "api_key": settings.MCP_API_KEY or "test",
                },
                json=changes,
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"⚠️  Failed to broadcast project update: {e}")
        return False
