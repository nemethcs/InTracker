"""WebSocket handler for SignalR hub."""
import json
import asyncio
import logging
from typing import Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from src.database.base import get_db
from src.database.models import User
from src.services.auth_service import auth_service
from .connection_manager import connection_manager
from .message_handler import handle_message

logger = logging.getLogger(__name__)


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
                logger.warning(f"Token verification failed: {e}", exc_info=True)
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
                    logger.debug(f"SignalR handshake completed for connection {connection_id}")
                    
                    # Send a ping message immediately after handshake to prevent timeout
                    # SignalR message type 6 is ping/keepalive
                    ping_msg = json.dumps({"type": 6}) + '\x1E'
                    await websocket.send_text(ping_msg)
                    logger.debug(f"Sent ping message to connection {connection_id}")
                else:
                    # Not a handshake, process as regular message
                    await handle_message(connection_id, user_id, handshake)
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Error parsing handshake: {e}, data: {handshake_data[:100]}")
                # Not valid JSON, might be a regular message, try to process it
                try:
                    # Try to parse as regular message
                    data = json.loads(handshake_data.split('\x1E')[0])  # Take first part if multiple messages
                    await handle_message(connection_id, user_id, data)
                except:
                    pass  # Ignore if can't parse
        except asyncio.TimeoutError:
            # No handshake received within timeout, continue with normal flow
            logger.debug(f"No handshake received for connection {connection_id}, continuing...")
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
                        logger.debug(f"Sent keepalive ping to connection {connection_id}")
                except Exception as e:
                    logger.warning(f"Error sending keepalive ping: {e}")
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
                            logger.debug(f"Received message type {data.get('type')} from connection {connection_id}")
                        await handle_message(connection_id, user_id, data)
                    except json.JSONDecodeError as e:
                        # Not valid JSON, might be handshake or other format
                        logger.debug(f"Error parsing message: {e}, text: {msg_text[:100]}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"Error receiving message: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cancel keepalive task if it exists
        if 'keepalive_task' in locals():
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
        if connection_id:
            await connection_manager.disconnect(connection_id)
