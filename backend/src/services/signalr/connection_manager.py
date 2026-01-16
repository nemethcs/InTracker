"""Connection manager for SignalR WebSocket connections."""
import json
import asyncio
import logging
import time
from typing import Dict, Set, Optional
from uuid import UUID, uuid4
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and project groups.
    
    Optimizations:
    - Automatic dead connection cleanup
    - Parallel broadcast operations
    - Connection health monitoring
    - Efficient team-level broadcasting
    """
    
    def __init__(self):
        # Map: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map: connection_id -> user_id
        self.connection_users: Dict[str, UUID] = {}
        # Map: project_id -> Set[connection_id]
        self.project_groups: Dict[str, Set[str]] = {}
        # Map: connection_id -> Set[project_id]
        self.connection_projects: Dict[str, Set[str]] = {}
        # Map: connection_id -> last_activity_timestamp
        self.connection_activity: Dict[str, float] = {}
        # Map: team_id -> Set[project_id]
        self.team_projects: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: UUID) -> str:
        """Accept WebSocket connection and register user."""
        await websocket.accept()
        connection_id = str(uuid4())
        async with self._lock:
            self.active_connections[connection_id] = websocket
            self.connection_users[connection_id] = user_id
            self.connection_projects[connection_id] = set()
            self.connection_activity[connection_id] = time.time()
        logger.info(f"Connection established: {connection_id} for user {user_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove connection and clean up groups.
        
        Optimized to:
        - Use async lock for thread safety
        - Batch broadcast operations
        - Clean up all related data structures
        """
        async with self._lock:
            # Get user_id and projects before cleanup
            user_id = self.connection_users.get(connection_id)
            project_ids = list(self.connection_projects.get(connection_id, []))
            
            # Clean up all connection data
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
            if connection_id in self.connection_activity:
                del self.connection_activity[connection_id]
        
        logger.info(f"Connection disconnected: {connection_id} for user {user_id}")
        
        # Broadcast user left events for all projects they were in
        # Use asyncio.gather for parallel broadcasting
        if user_id and project_ids:
            message = {
                "type": 1,  # SignalR invocation
                "target": "userLeft",
                "arguments": [{
                    "userId": str(user_id),
                    "projectId": None  # Will be set per project
                }]
            }
            # Broadcast to all projects in parallel
            tasks = []
            for project_id in project_ids:
                project_message = message.copy()
                project_message["arguments"][0]["projectId"] = project_id
                tasks.append(self.broadcast_to_project(project_id, project_message))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
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
        async with self._lock:
            if connection_id not in self.active_connections:
                return
            
            if project_id not in self.project_groups:
                self.project_groups[project_id] = set()
            
            was_new_join = connection_id not in self.project_groups[project_id]
            self.project_groups[project_id].add(connection_id)
            self.connection_projects[connection_id].add(project_id)
            # Update activity timestamp
            if connection_id in self.connection_activity:
                self.connection_activity[connection_id] = time.time()
        
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
        async with self._lock:
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
        """Send message to specific connection.
        
        Updates connection activity timestamp on successful send.
        """
        if connection_id not in self.active_connections:
            return
        
        try:
            websocket = self.active_connections[connection_id]
            # SignalR protocol requires record separator (0x1E) after each message
            message_json = json.dumps(message)
            await websocket.send_text(message_json + '\x1E')
            # Update activity timestamp on successful send
            async with self._lock:
                if connection_id in self.connection_activity:
                    self.connection_activity[connection_id] = time.time()
        except Exception as e:
            logger.warning(f"Error sending to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def broadcast_to_project(self, project_id: str, message: dict, exclude_connection: Optional[str] = None):
        """Broadcast message to all connections in a project group.
        
        Optimized to send messages in parallel for better performance.
        """
        if project_id not in self.project_groups:
            return
        
        # Get connection IDs to broadcast to (with lock for thread safety)
        async with self._lock:
            connection_ids = [
                conn_id for conn_id in self.project_groups[project_id]
                if conn_id != exclude_connection
            ]
        
        if not connection_ids:
            return
        
        # Send messages in parallel
        tasks = [self.send_to_connection(conn_id, message) for conn_id in connection_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up failed connections
        connections_to_remove = [
            conn_id for conn_id, result in zip(connection_ids, results)
            if isinstance(result, Exception)
        ]
        
        if connections_to_remove:
            logger.warning(f"Removing {len(connections_to_remove)} failed connections from project {project_id}")
            for connection_id in connections_to_remove:
                await self.disconnect(connection_id)
    
    async def broadcast_to_team(self, team_id: str, message: dict, exclude_connection: Optional[str] = None):
        """Broadcast message to all connections in projects that belong to a team.
        
        Optimized to use team_projects mapping for efficient broadcasting.
        """
        # Get all project IDs for this team
        async with self._lock:
            project_ids = list(self.team_projects.get(team_id, set()))
        
        if not project_ids:
            # Fallback to broadcast all if team has no projects registered
            await self.broadcast_to_all(message, exclude_connection)
            return
        
        # Broadcast to all projects in parallel
        tasks = [
            self.broadcast_to_project(project_id, message, exclude_connection)
            for project_id in project_ids
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def register_team_project(self, team_id: str, project_id: str):
        """Register a project as belonging to a team for efficient team-level broadcasting."""
        if team_id not in self.team_projects:
            self.team_projects[team_id] = set()
        self.team_projects[team_id].add(project_id)
    
    def unregister_team_project(self, team_id: str, project_id: str):
        """Unregister a project from a team."""
        if team_id in self.team_projects:
            self.team_projects[team_id].discard(project_id)
            if not self.team_projects[team_id]:
                del self.team_projects[team_id]
    
    async def broadcast_to_all(self, message: dict, exclude_connection: Optional[str] = None):
        """Broadcast message to all connected clients.
        
        Optimized to send messages in parallel for better performance.
        """
        # Get all connection IDs (with lock for thread safety)
        async with self._lock:
            connection_ids = [
                conn_id for conn_id in self.active_connections.keys()
                if conn_id != exclude_connection
            ]
        
        if not connection_ids:
            return
        
        # Send messages in parallel
        tasks = [self.send_to_connection(conn_id, message) for conn_id in connection_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up failed connections
        connections_to_remove = [
            conn_id for conn_id, result in zip(connection_ids, results)
            if isinstance(result, Exception)
        ]
        
        if connections_to_remove:
            logger.warning(f"Removing {len(connections_to_remove)} failed connections")
            for connection_id in connections_to_remove:
                await self.disconnect(connection_id)
    
    async def cleanup_dead_connections(self, timeout_seconds: float = 60.0):
        """Remove connections that haven't been active for the specified timeout.
        
        This should be called periodically to clean up dead connections.
        """
        current_time = time.time()
        async with self._lock:
            dead_connections = [
                conn_id for conn_id, last_activity in self.connection_activity.items()
                if current_time - last_activity > timeout_seconds
            ]
        
        if dead_connections:
            logger.info(f"Cleaning up {len(dead_connections)} dead connections")
            for connection_id in dead_connections:
                await self.disconnect(connection_id)
    
    async def get_connection_stats(self) -> dict:
        """Get statistics about current connections."""
        async with self._lock:
            return {
                "total_connections": len(self.active_connections),
                "total_projects": len(self.project_groups),
                "total_teams": len(self.team_projects),
                "connections_by_project": {
                    project_id: len(conn_ids)
                    for project_id, conn_ids in self.project_groups.items()
                },
            }


# Global connection manager instance
connection_manager = ConnectionManager()
