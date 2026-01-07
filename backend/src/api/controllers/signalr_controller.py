"""SignalR WebSocket hub controller."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from src.services.signalr_hub import handle_websocket

router = APIRouter(tags=["signalr"])


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
        "url": "/hub",
        "accessToken": None,  # Token should be passed in query string
        "connectionToken": None,
        "availableTransports": [
            {
                "transport": "WebSockets",
                "transferFormats": ["Text", "Binary"]
            }
        ]
    }
