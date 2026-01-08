"""Message handler for SignalR WebSocket messages."""
from uuid import UUID
from .connection_manager import connection_manager


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
