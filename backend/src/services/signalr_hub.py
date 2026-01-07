"""SignalR-compatible WebSocket hub for real-time updates."""
import json
import asyncio
from typing import Dict, Set, Optional
from uuid import UUID, uuid4
from fastapi import WebSocket, WebSocketDisconnect
from src.database.base import get_db
from src.database.models import User
from src.services.auth_service import auth_service


class ConnectionManager:
    """Manages WebSocket connections and project groups."""
    
    def __init__(self):
        # Map: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map: connection_id -> user_id
        self.connection_users: Dict[str, UUID] = {}
        # Map: project_id -> Set[connection_id]
        self.project_groups: Dict[str, Set[str]] = {}
        # Map: connection_id -> Set[project_id]
        self.connection_projects: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: UUID) -> str:
        """Accept WebSocket connection and register user."""
        await websocket.accept()
        connection_id = str(uuid4())
        self.active_connections[connection_id] = websocket
        self.connection_users[connection_id] = user_id
        self.connection_projects[connection_id] = set()
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove connection and clean up groups."""
        # Get user_id and projects before cleanup
        user_id = self.connection_users.get(connection_id)
        project_ids = list(self.connection_projects.get(connection_id, []))
        
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_users:
            del self.connection_users[connection_id]
        if connection_id in self.connection_projects:
            # Remove from all project groups
            for project_id in project_ids:
                if project_id in self.project_groups:
                    self.project_groups[project_id].discard(connection_id)
            del self.connection_projects[connection_id]
        
        # Broadcast user left events for all projects they were in
        if user_id:
            for project_id in project_ids:
                asyncio.create_task(self.broadcast_to_project(project_id, {
                    "type": "userLeft",
                    "userId": str(user_id),
                    "projectId": project_id
                }))
    
    def get_active_users_for_project(self, project_id: str) -> Set[UUID]:
        """Get set of active user IDs for a project."""
        if project_id not in self.project_groups:
            return set()
        
        user_ids = set()
        for connection_id in self.project_groups[project_id]:
            if connection_id in self.connection_users:
                user_ids.add(self.connection_users[connection_id])
        
        return user_ids
    
    async def join_project(self, connection_id: str, project_id: str):
        """Add connection to project group."""
        if connection_id not in self.active_connections:
            return
        
        if project_id not in self.project_groups:
            self.project_groups[project_id] = set()
        
        was_new_join = connection_id not in self.project_groups[project_id]
        self.project_groups[project_id].add(connection_id)
        self.connection_projects[connection_id].add(project_id)
        
        # Broadcast user joined event if this is a new join
        if was_new_join and connection_id in self.connection_users:
            user_id = self.connection_users[connection_id]
            await self.broadcast_to_project(project_id, {
                "type": "userJoined",
                "userId": str(user_id),
                "projectId": project_id
            }, exclude_connection=connection_id)
    
    async def leave_project(self, connection_id: str, project_id: str):
        """Remove connection from project group."""
        was_member = project_id in self.project_groups and connection_id in self.project_groups[project_id]
        
        if project_id in self.project_groups:
            self.project_groups[project_id].discard(connection_id)
        if connection_id in self.connection_projects:
            self.connection_projects[connection_id].discard(project_id)
        
        # Broadcast user left event if they were a member
        if was_member and connection_id in self.connection_users:
            user_id = self.connection_users[connection_id]
            await self.broadcast_to_project(project_id, {
                "type": "userLeft",
                "userId": str(user_id),
                "projectId": project_id
            })
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to connection {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_project(self, project_id: str, message: dict, exclude_connection: Optional[str] = None):
        """Broadcast message to all connections in a project group."""
        if project_id not in self.project_groups:
            return
        
        connections_to_remove = []
        for connection_id in self.project_groups[project_id]:
            if connection_id == exclude_connection:
                continue
            try:
                await self.send_to_connection(connection_id, message)
            except Exception as e:
                print(f"Error broadcasting to connection {connection_id}: {e}")
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            self.disconnect(connection_id)
    
    async def broadcast_to_all(self, message: dict, exclude_connection: Optional[str] = None):
        """Broadcast message to all connected clients."""
        connections_to_remove = []
        for connection_id in list(self.active_connections.keys()):
            if connection_id == exclude_connection:
                continue
            try:
                await self.send_to_connection(connection_id, message)
            except Exception as e:
                print(f"Error broadcasting to connection {connection_id}: {e}")
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            self.disconnect(connection_id)


# Global connection manager instance
connection_manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, token: Optional[str] = None):
    """Handle WebSocket connection for SignalR hub."""
    connection_id = None
    
    try:
        # Authenticate user from token
        user_id = None
        if token:
            try:
                # Verify token and get user
                db = next(get_db())
                try:
                    payload = auth_service.decode_token(token)
                    user_email = payload.get("email")
                    if user_email:
                        user = db.query(User).filter(User.email == user_email).first()
                        if user:
                            user_id = user.id
                finally:
                    db.close()
            except Exception as e:
                print(f"Token verification failed: {e}")
                await websocket.close(code=1008, reason="Unauthorized")
                return
        
        if not user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Accept connection
        connection_id = await connection_manager.connect(websocket, user_id)
        
        # Send connection confirmation (SignalR-compatible format)
        await websocket.send_json({
            "type": 1,  # SignalR message type: invocation
            "target": "connection",
            "arguments": [{
                "connectionId": connection_id,
                "message": "Connected"
            }]
        })
        # Also send simple JSON for compatibility
        await websocket.send_json({
            "type": "connection",
            "connectionId": connection_id,
            "message": "Connected"
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_message(connection_id, user_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error handling message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if connection_id:
            connection_manager.disconnect(connection_id)


async def handle_message(connection_id: str, user_id: UUID, data: dict):
    """Handle incoming WebSocket message."""
    # Support both SignalR protocol and simple JSON messages
    if isinstance(data, dict):
        # Check for SignalR invoke method
        if "method" in data:
            method = data.get("method")
            arguments = data.get("arguments", [])
            
            if method == "JoinProject":
                project_id = arguments[0] if arguments else data.get("projectId")
                if project_id:
                    await connection_manager.join_project(connection_id, str(project_id))
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "joinedProject",
                        "projectId": str(project_id)
                    })
            
            elif method == "LeaveProject":
                project_id = arguments[0] if arguments else data.get("projectId")
                if project_id:
                    await connection_manager.leave_project(connection_id, str(project_id))
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "leftProject",
                        "projectId": str(project_id)
                    })
            
            elif method == "SendUserActivity":
                project_id = arguments[0] if len(arguments) > 0 else data.get("projectId")
                action = arguments[1] if len(arguments) > 1 else data.get("action")
                feature_id = arguments[2] if len(arguments) > 2 else data.get("featureId")
                
                if project_id:
                    await connection_manager.broadcast_to_project(str(project_id), {
                        "type": "userActivity",
                        "userId": str(user_id),
                        "projectId": str(project_id),
                        "action": action,
                        "featureId": str(feature_id) if feature_id else None
                    }, exclude_connection=connection_id)
        
        # Support simple JSON messages for compatibility
        elif "type" in data:
            message_type = data.get("type")
            
            if message_type == "joinProject":
                project_id = data.get("projectId")
                if project_id:
                    await connection_manager.join_project(connection_id, str(project_id))
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "joinedProject",
                        "projectId": str(project_id)
                    })
            
            elif message_type == "leaveProject":
                project_id = data.get("projectId")
                if project_id:
                    await connection_manager.leave_project(connection_id, str(project_id))
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "leftProject",
                        "projectId": str(project_id)
                    })
            
            elif message_type == "userActivity":
                project_id = data.get("projectId")
                action = data.get("action")
                feature_id = data.get("featureId")
                
                if project_id:
                    await connection_manager.broadcast_to_project(str(project_id), {
                        "type": "userActivity",
                        "userId": str(user_id),
                        "projectId": str(project_id),
                        "action": action,
                        "featureId": str(feature_id) if feature_id else None
                    }, exclude_connection=connection_id)
        
        else:
            # Unknown message format
            await connection_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": "Unknown message format"
            })


# Event broadcasting functions
async def broadcast_todo_update(project_id: str, todo_id: str, user_id: UUID, changes: dict):
    """Broadcast todo update to project group."""
    await connection_manager.broadcast_to_project(project_id, {
        "type": "todoUpdated",
        "todoId": todo_id,
        "projectId": project_id,
        "userId": str(user_id),
        "changes": changes
    })


async def broadcast_feature_update(project_id: str, feature_id: str, progress: int):
    """Broadcast feature progress update to project group."""
    await connection_manager.broadcast_to_project(project_id, {
        "type": "featureUpdated",
        "featureId": feature_id,
        "projectId": project_id,
        "progress": progress
    })


async def broadcast_project_update(project_id: str, changes: dict):
    """Broadcast project update to project group."""
    await connection_manager.broadcast_to_project(project_id, {
        "type": "projectUpdated",
        "projectId": project_id,
        "changes": changes
    })
