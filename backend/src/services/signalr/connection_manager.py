"""Connection manager for SignalR WebSocket connections."""
import json
import asyncio
from typing import Dict, Set, Optional
from uuid import UUID, uuid4
from fastapi import WebSocket


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
                # SignalR message format
                message = {
                    "type": 1,  # SignalR invocation
                    "target": "userLeft",
                    "arguments": [{
                        "userId": str(user_id),
                        "projectId": project_id
                    }]
                }
                asyncio.create_task(self.broadcast_to_project(project_id, message))
    
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
            # SignalR message format
            message = {
                "type": 1,  # SignalR invocation
                "target": "userLeft",
                "arguments": [{
                    "userId": str(user_id),
                    "projectId": project_id
                }]
            }
            await self.broadcast_to_project(project_id, message)
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                # SignalR protocol requires record separator (0x1E) after each message
                message_json = json.dumps(message)
                await websocket.send_text(message_json + '\x1E')
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
    
    async def broadcast_to_team(self, team_id: str, message: dict, exclude_connection: Optional[str] = None):
        """Broadcast message to all connections in projects that belong to a team.
        
        Since ideas are team-level, we need to broadcast to all users who have
        access to projects in that team. We'll broadcast to all connections and
        let the frontend filter by team_id.
        """
        # For now, broadcast to all (frontend will filter by team_id)
        # TODO: Implement team_groups for more efficient broadcasting
        await self.broadcast_to_all(message, exclude_connection)
    
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
