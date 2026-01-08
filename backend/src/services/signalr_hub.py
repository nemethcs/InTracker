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
                payload = auth_service.verify_token(token, is_refresh=False)
                user_email = payload.get("email")
                if user_email:
                    db = next(get_db())
                    try:
                        user = db.query(User).filter(User.email == user_email).first()
                        if user:
                            user_id = user.id
                    finally:
                        db.close()
            except Exception as e:
                print(f"Token verification failed: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await websocket.close(code=1008, reason="Unauthorized")
                except:
                    pass
                return
        
        if not user_id:
            try:
                await websocket.close(code=1008, reason="Unauthorized")
            except:
                pass
            return
        
        # Accept connection
        connection_id = await connection_manager.connect(websocket, user_id)
        
        # Handle SignalR handshake
        # SignalR client sends handshake: {"protocol":"json","version":1}
        # We need to respond with: {} (empty object)
        try:
            # Wait for handshake message (with timeout)
            handshake_data = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
            # SignalR handshake might be followed by a record separator (0x1E)
            # Remove record separator if present
            if handshake_data.endswith('\x1E'):
                handshake_data = handshake_data[:-1]
            
            try:
                handshake = json.loads(handshake_data)
                # If it's a handshake message, respond with empty object
                if isinstance(handshake, dict) and ("protocol" in handshake or "version" in handshake):
                    # Send SignalR handshake response: {} followed by record separator
                    await websocket.send_text("{}\x1E")  # SignalR handshake response with record separator
                    print(f"SignalR handshake completed for connection {connection_id}")
                    
                    # Send a ping message immediately after handshake to prevent timeout
                    # SignalR message type 6 is ping/keepalive
                    ping_msg = json.dumps({"type": 6}) + '\x1E'
                    await websocket.send_text(ping_msg)
                    print(f"Sent ping message to connection {connection_id}")
                else:
                    # Not a handshake, process as regular message
                    await handle_message(connection_id, user_id, handshake)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing handshake: {e}, data: {handshake_data[:100]}")
                # Not valid JSON, might be a regular message, try to process it
                try:
                    # Try to parse as regular message
                    data = json.loads(handshake_data.split('\x1E')[0])  # Take first part if multiple messages
                    await handle_message(connection_id, user_id, data)
                except:
                    pass  # Ignore if can't parse
        except asyncio.TimeoutError:
            # No handshake received within timeout, continue with normal flow
            print(f"No handshake received for connection {connection_id}, continuing...")
        except WebSocketDisconnect:
            # Client disconnected during handshake
            return
        
        # Note: Ping message is now sent immediately after handshake response
        # This prevents the SignalR client from timing out
        
        # Start a background task to send periodic keepalive pings
        async def send_keepalive():
            """Send periodic keepalive pings to prevent timeout."""
            while connection_id in connection_manager.active_connections:
                try:
                    await asyncio.sleep(15)  # Send ping every 15 seconds (SignalR default timeout is 30 seconds)
                    if connection_id in connection_manager.active_connections:
                        ping_msg = {"type": 6}
                        await connection_manager.send_to_connection(connection_id, ping_msg)
                        print(f"Sent keepalive ping to connection {connection_id}")
                except Exception as e:
                    print(f"Error sending keepalive ping: {e}")
                    break
        
        # Start keepalive task
        keepalive_task = asyncio.create_task(send_keepalive())
        
        # Handle incoming messages
        while True:
            try:
                # Receive as text (SignalR protocol uses text with record separators)
                text_data = await websocket.receive_text()
                
                # SignalR messages are separated by record separator (0x1E)
                # Split by record separator and process each message
                messages = text_data.split('\x1E')
                for msg_text in messages:
                    if not msg_text.strip():
                        continue
                    
                    try:
                        data = json.loads(msg_text)
                        # Log message type for debugging
                        if isinstance(data, dict) and "type" in data:
                            print(f"Received message type {data.get('type')} from connection {connection_id}")
                        await handle_message(connection_id, user_id, data)
                    except json.JSONDecodeError as e:
                        # Not valid JSON, might be handshake or other format
                        print(f"Error parsing message: {e}, text: {msg_text[:100]}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Cancel keepalive task if it exists
        if 'keepalive_task' in locals():
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
        if connection_id:
            connection_manager.disconnect(connection_id)


async def handle_message(connection_id: str, user_id: UUID, data: dict):
    """Handle incoming WebSocket message."""
    # Support both SignalR protocol and simple JSON messages
    if isinstance(data, dict):
        # Handle SignalR ping/keepalive messages (type: 6)
        # The client sends ping messages, and we need to respond with ping
        message_type = data.get("type")
        if message_type == 6:
            # Respond with ping to keep connection alive
            ping_response = {"type": 6}
            await connection_manager.send_to_connection(connection_id, ping_response)
            return  # Don't log every ping to reduce noise
        
        # Log other message types for debugging
        if message_type != 6:
            print(f"Received message from connection {connection_id}: {data}")
        
        # Check for SignalR invoke method (type: 1 with invocation)
        if message_type == 1 and "target" in data:
            # SignalR invocation message format: {"type": 1, "target": "methodName", "arguments": [...]}
            method = data.get("target")
            arguments = data.get("arguments", [])
            
            if method == "JoinProject":
                project_id = arguments[0] if arguments and len(arguments) > 0 else arguments[0] if isinstance(arguments[0], str) else None
                if not project_id and isinstance(arguments[0], dict):
                    project_id = arguments[0].get("projectId")
                if project_id:
                    await connection_manager.join_project(connection_id, str(project_id))
                    print(f"Connection {connection_id} joined project {project_id}")
                    # Send confirmation with SignalR format
                    confirmation = {
                        "type": 1,  # SignalR invocation
                        "target": "joinedProject",
                        "arguments": [{
                            "projectId": str(project_id)
                        }]
                    }
                    await connection_manager.send_to_connection(connection_id, confirmation)
                return
            
            elif method == "LeaveProject":
                project_id = arguments[0] if arguments and len(arguments) > 0 else None
                if not project_id and isinstance(arguments[0], dict):
                    project_id = arguments[0].get("projectId")
                if project_id:
                    await connection_manager.leave_project(connection_id, str(project_id))
                    print(f"Connection {connection_id} left project {project_id}")
                    # Send confirmation with SignalR format
                    confirmation = {
                        "type": 1,  # SignalR invocation
                        "target": "leftProject",
                        "arguments": [{
                            "projectId": str(project_id)
                        }]
                    }
                    await connection_manager.send_to_connection(connection_id, confirmation)
                return
            
            elif method == "SendUserActivity":
                project_id = arguments[0] if len(arguments) > 0 else None
                action = arguments[1] if len(arguments) > 1 else None
                feature_id = arguments[2] if len(arguments) > 2 else None
                
                if project_id:
                    # SignalR message format
                    message = {
                        "type": 1,  # SignalR invocation
                        "target": "userActivity",
                        "arguments": [{
                            "userId": str(user_id),
                            "projectId": str(project_id),
                            "action": action,
                            "featureId": str(feature_id) if feature_id else None
                        }]
                    }
                    await connection_manager.broadcast_to_project(str(project_id), message, exclude_connection=connection_id)
                return
        
        # Check for SignalR invoke method (legacy format with "method" key)
        if "method" in data:
            method = data.get("method")
            arguments = data.get("arguments", [])
            
            if method == "JoinProject":
                project_id = arguments[0] if arguments else data.get("projectId")
                if project_id:
                    await connection_manager.join_project(connection_id, str(project_id))
                    # Send confirmation with SignalR format
                    confirmation = {
                        "type": 1,  # SignalR invocation
                        "target": "joinedProject",
                        "arguments": [{
                            "projectId": str(project_id)
                        }]
                    }
                    await connection_manager.send_to_connection(connection_id, confirmation)
            
            elif method == "LeaveProject":
                project_id = arguments[0] if arguments else data.get("projectId")
                if project_id:
                    await connection_manager.leave_project(connection_id, str(project_id))
                    # Send confirmation with SignalR format
                    confirmation = {
                        "type": 1,  # SignalR invocation
                        "target": "leftProject",
                        "arguments": [{
                            "projectId": str(project_id)
                        }]
                    }
                    await connection_manager.send_to_connection(connection_id, confirmation)
            
            elif method == "SendUserActivity":
                project_id = arguments[0] if len(arguments) > 0 else data.get("projectId")
                action = arguments[1] if len(arguments) > 1 else data.get("action")
                feature_id = arguments[2] if len(arguments) > 2 else data.get("featureId")
                
                if project_id:
                    # SignalR message format
                    message = {
                        "type": 1,  # SignalR invocation
                        "target": "userActivity",
                        "arguments": [{
                            "userId": str(user_id),
                            "projectId": str(project_id),
                            "action": action,
                            "featureId": str(feature_id) if feature_id else None
                        }]
                    }
                    await connection_manager.broadcast_to_project(str(project_id), message, exclude_connection=connection_id)
        
        # Support simple JSON messages for compatibility
        elif "type" in data:
            message_type = data.get("type")
            
            if message_type == "joinProject":
                project_id = data.get("projectId")
                if project_id:
                    await connection_manager.join_project(connection_id, str(project_id))
                    # Send confirmation with SignalR format
                    confirmation = {
                        "type": 1,  # SignalR invocation
                        "target": "joinedProject",
                        "arguments": [{
                            "projectId": str(project_id)
                        }]
                    }
                    await connection_manager.send_to_connection(connection_id, confirmation)
            
            elif message_type == "leaveProject":
                project_id = data.get("projectId")
                if project_id:
                    await connection_manager.leave_project(connection_id, str(project_id))
                    # Send confirmation with SignalR format
                    confirmation = {
                        "type": 1,  # SignalR invocation
                        "target": "leftProject",
                        "arguments": [{
                            "projectId": str(project_id)
                        }]
                    }
                    await connection_manager.send_to_connection(connection_id, confirmation)
            
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


async def broadcast_feature_update(project_id: str, feature_id: str, progress: int):
    """Broadcast feature progress update to project group."""
    # SignalR message format
    message = {
        "type": 1,  # SignalR invocation
        "target": "featureUpdated",
        "arguments": [{
            "featureId": feature_id,
            "projectId": project_id,
            "progress": progress
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
