# Refactoring Plan: signalr_hub.py (615 lines)

## Current Structure Analysis

The `signalr_hub.py` file contains:

### 1. ConnectionManager Class (Lines ~12-178, ~180 lines)
- Connection management
- Project group management
- Broadcast methods (to_project, to_team, to_all)

### 2. handle_websocket Function (Lines ~184-329, ~150 lines)
- WebSocket connection handling
- Authentication
- SignalR handshake
- Keepalive pings
- Message receiving loop

### 3. handle_message Function (Lines ~331-514, ~185 lines)
- Message parsing and routing
- JoinProject, LeaveProject, SendUserActivity handlers

### 4. Broadcast Functions (Lines ~517-615, ~100 lines)
- broadcast_todo_update
- broadcast_feature_update
- broadcast_project_update
- broadcast_session_start
- broadcast_session_end
- broadcast_idea_update

## Refactoring Strategy

Split into 4 separate modules:

### 1. `connection_manager.py` (~180 lines)
- ConnectionManager class
- Global connection_manager instance

### 2. `websocket_handler.py` (~150 lines)
- handle_websocket function

### 3. `message_handler.py` (~185 lines)
- handle_message function

### 4. `broadcast_handlers.py` (~100 lines)
- All broadcast functions

### 5. `signalr_hub.py` (refactored, ~50 lines)
- Re-exports all functions and classes
- Maintains backward compatibility

## Implementation Steps

1. Create new module files
2. Move code to appropriate modules
3. Update imports in `signalr_hub.py`
4. Update imports in files that use signalr_hub
5. Test all functionality

## Dependencies

All modules will share:
- `connection_manager` from `connection_manager.py`
- `WebSocket`, `WebSocketDisconnect` from `fastapi`
- `get_db` from `src.database.base`
- `User` from `src.database.models`
- `auth_service` from `src.services.auth_service`
