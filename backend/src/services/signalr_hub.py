"""SignalR-compatible WebSocket hub for real-time updates - refactored into smaller modules.

This module re-exports functions and classes for backward compatibility.
The actual implementation is in the signalr/ subdirectory.
"""

# Re-export everything from signalr module
from .signalr import (
    ConnectionManager,
    connection_manager,
    handle_websocket,
    handle_message,
    broadcast_todo_update,
    broadcast_feature_update,
    broadcast_project_update,
    broadcast_session_start,
    broadcast_session_end,
    broadcast_idea_update,
)

__all__ = [
    "ConnectionManager",
    "connection_manager",
    "handle_websocket",
    "handle_message",
    "broadcast_todo_update",
    "broadcast_feature_update",
    "broadcast_project_update",
    "broadcast_session_start",
    "broadcast_session_end",
    "broadcast_idea_update",
]
