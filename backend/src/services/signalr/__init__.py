"""SignalR-compatible WebSocket hub for real-time updates - refactored into smaller modules.

This module re-exports functions and classes from:
- connection_manager: ConnectionManager class and instance
- websocket_handler: handle_websocket function
- message_handler: handle_message function
- broadcast_handlers: All broadcast functions
"""

# Re-export from connection_manager
from .connection_manager import ConnectionManager, connection_manager

# Re-export from websocket_handler
from .websocket_handler import handle_websocket

# Re-export from message_handler
from .message_handler import handle_message

# Re-export from broadcast_handlers
from .broadcast_handlers import (
    broadcast_todo_update,
    broadcast_feature_update,
    broadcast_project_update,
    broadcast_session_start,
    broadcast_session_end,
    broadcast_idea_update,
    broadcast_mcp_verified,
)

__all__ = [
    # Connection manager
    "ConnectionManager",
    "connection_manager",
    # WebSocket handler
    "handle_websocket",
    # Message handler
    "handle_message",
    # Broadcast handlers
    "broadcast_todo_update",
    "broadcast_feature_update",
    "broadcast_project_update",
    "broadcast_session_start",
    "broadcast_session_end",
    "broadcast_idea_update",
    "broadcast_mcp_verified",
]
