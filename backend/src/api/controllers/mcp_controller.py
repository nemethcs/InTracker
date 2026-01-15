"""MCP Server HTTP/SSE transport controller for FastAPI.

Session Management:
- Sessions are stored in Redis with 24-hour TTL
- Backend restarts don't break Cursor connections
- Graceful session rehydration for old sessions
- No manual Cursor toggle required
"""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from starlette.types import Receive, Send, Scope
from mcp.server.sse import SseServerTransport
from src.config import settings
from src.mcp.server import server as mcp_server
from src.services.mcp_session_service import mcp_session_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Create SSE transport
sse_transport = SseServerTransport("/mcp/messages/")

# No global lock needed - removed to prevent deadlocks
# MCP SDK and Redis session handling are already thread-safe
import asyncio


def verify_api_key(api_key: Optional[str]) -> Optional[str]:
    """Verify API key and return user_id if valid.
    
    Checks both:
    1. User-specific MCP API keys from database (preferred)
    2. Legacy settings.MCP_API_KEY (fallback for development)
    
    Returns:
        user_id (as string) if key is valid, None otherwise
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    # First, try to verify as user-specific MCP API key
    from src.database.base import SessionLocal
    from src.services.mcp_key_service import mcp_key_service
    
    db = SessionLocal()
    try:
        user_id = mcp_key_service.verify_and_get_user_id(db=db, key=api_key)
        if user_id:
            # Valid user-specific key found
            return str(user_id)
    except Exception as e:
        # Key not found in database, try legacy key
        pass
    finally:
        db.close()
    
    # Fallback to legacy settings.MCP_API_KEY (for development)
    if settings.MCP_API_KEY and api_key == settings.MCP_API_KEY:
        # Legacy key is valid, but no user_id (returns None)
        return None
    
    # Key is invalid
    raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/health")
async def mcp_health_check():
    """MCP server health check endpoint."""
    return JSONResponse(content={"status": "ok", "service": "intracker-mcp-server"})


class MCPSSEASGIApp:
    """ASGI app wrapper for MCP SSE endpoint with Redis session persistence.
    
    Supports both GET (SSE) and POST (Streamable HTTP) methods.
    Cursor tries POST first (Streamable HTTP), then falls back to GET (SSE).
    Both methods return the same SSE stream.
    """
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        method = scope.get("method", "UNKNOWN")
        logger.info(f"DEBUG: MCPSSEASGIApp called with method: {method}")
        
        # Accept both GET (SSE) and POST (Streamable HTTP) methods
        if scope["type"] != "http" or scope["method"] not in ["GET", "POST"]:
            from starlette.responses import Response
            response = Response(status_code=405)
            await response(scope, receive, send)
            return
        
        # For POST requests (Streamable HTTP), read and discard the body
        # The MCP SDK sends initialization data in POST body, but we don't need it
        # as we handle initialization through SSE events
        if scope["method"] == "POST":
            logger.info(f"DEBUG: Reading POST body...")
            # Read the request body to avoid connection issues
            while True:
                message = await receive()
                if message["type"] == "http.request":
                    # Body received, continue processing
                    if not message.get("more_body", False):
                        logger.info(f"DEBUG: POST body fully read")
                        break
                elif message["type"] == "http.disconnect":
                    logger.info(f"DEBUG: Client disconnected during POST body read")
                    # Client disconnected
                    return
        
        # Extract connection ID from query params or headers (for session rehydration)
        connection_id = None
        query_string = scope.get("query_string", b"").decode()
        if "connection_id=" in query_string:
            # Extract connection_id from query params
            for param in query_string.split("&"):
                if param.startswith("connection_id="):
                    connection_id = param.split("=", 1)[1]
                    break
        
        # If no connection_id provided, generate one
        if not connection_id:
            import uuid
            connection_id = str(uuid.uuid4())
            logger.info(f"🆕 New MCP connection, generated ID: {connection_id[:8]}...")
        else:
            logger.info(f"🔄 Reconnecting MCP session: {connection_id[:8]}...")
        
        # Verify API key and get user_id
        api_key = None
        headers = scope.get("headers", [])
        for key, value in headers:
            if key.lower() == b"x-api-key":
                api_key = value.decode()
                break
        
        try:
            user_id = verify_api_key(api_key)
            # Set the user_id in MCP middleware for this connection
            if user_id:
                from src.mcp.middleware.auth import set_mcp_api_key
                set_mcp_api_key(api_key)  # This will extract and set user_id
        except HTTPException as e:
            # Return error response and stop processing
            # Don't re-raise to avoid global exception handler duplicate response
            response = JSONResponse(
                content={"detail": e.detail},
                status_code=e.status_code
            )
            await response(scope, receive, send)
            return
        
        # Check if this is a session rehydration (reconnect after backend restart)
        existing_session = mcp_session_service.get_session(connection_id)
        if existing_session:
            logger.info(f"✅ Rehydrating MCP session: {connection_id[:8]}... (created: {existing_session.get('created_at')})")
            # Update activity timestamp and extend TTL
            mcp_session_service.update_session_activity(connection_id)
        else:
            # Create new session in Redis
            metadata = {
                "user_id": user_id,
                "api_key_prefix": api_key[:12] if api_key else None,
            }
            mcp_session_service.create_session(connection_id, metadata)
        
        # No global lock needed - MCP SDK and Redis are already thread-safe
        # Global lock was causing deadlocks with multiple concurrent connections
        
        logger.info(f"DEBUG: Calling sse_transport.connect_sse() for connection: {connection_id[:8]}...")
        try:
            cm = sse_transport.connect_sse(scope, receive, send)
            logger.info(f"DEBUG: connect_sse() returned context manager for connection: {connection_id[:8]}...")
            
            async with cm as streams:
                logger.info(f"DEBUG: Context manager entered for connection: {connection_id[:8]}...")
                read_stream, write_stream = streams
                
                logger.info(f"🚀 MCP server running for connection: {connection_id[:8]}...")
                
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
                
        except BaseException as e:
                # Catch all exceptions including ExceptionGroup
                error_msg = str(e)
                
                # Check for response already sent errors (ignore)
                if "Response already sent" in error_msg or "already completed" in error_msg:
                    # Response already sent - ignore
                    pass
                
                # Check for graceful connection close
                elif isinstance(e, (ConnectionError, BrokenPipeError, OSError)):
                    # Connection closed gracefully (client disconnected or server restart)
                    # This is normal - Cursor will automatically reconnect
                    logger.info(f"🔌 MCP SSE connection closed: {connection_id[:8]}... - {e}")
                    # Don't delete session - allow reconnection
                
                # Log all other errors
                else:
                    logger.error(f"❌ MCP SSE connection error: {connection_id[:8]}... - {e}", exc_info=True)
                    # Delete session on error
                    mcp_session_service.delete_session(connection_id)


class MCPMessagesASGIApp:
    """ASGI app wrapper for MCP messages endpoint with session tracking."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] != "POST":
            from starlette.responses import Response
            response = Response(status_code=405)
            await response(scope, receive, send)
            return
        
        # Extract connection ID from query params
        # Cursor sends session_id, we need to extract connection_id from it or use it directly
        connection_id = None
        session_id = None
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode()
        
        # Try to extract session_id first (sent by Cursor/MCP SDK)
        if "session_id=" in query_string:
            for param in query_string.split("&"):
                if param.startswith("session_id="):
                    session_id = param.split("=", 1)[1]
                    # Extract connection_id from session_id (first 8 chars)
                    connection_id = session_id[:8] if session_id else None
                    break
        
        # If no session_id, try connection_id directly
        if not connection_id and "connection_id=" in query_string:
            for param in query_string.split("&"):
                if param.startswith("connection_id="):
                    connection_id = param.split("=", 1)[1]
                    break
        
        # IMPORTANT: Add connection_id to query string if not present
        # The SSE transport needs connection_id in the query string
        if connection_id and "connection_id=" not in query_string:
            if query_string:
                query_string = f"{query_string}&connection_id={connection_id}"
            else:
                query_string = f"connection_id={connection_id}"
            # Update scope with modified query string
            scope["query_string"] = query_string.encode()
        
        # Verify API key and get user_id
        api_key = None
        headers = scope.get("headers", [])
        for key, value in headers:
            if key.lower() == b"x-api-key":
                api_key = value.decode()
                break
        
        try:
            user_id = verify_api_key(api_key)
            # Set the user_id in MCP middleware for this connection
            if user_id:
                from src.mcp.middleware.auth import set_mcp_api_key
                set_mcp_api_key(api_key)  # This will extract and set user_id
        except HTTPException as e:
            # Return error response and stop processing
            # Don't re-raise to avoid global exception handler duplicate response
            response = JSONResponse(
                content={"detail": e.detail},
                status_code=e.status_code
            )
            await response(scope, receive, send)
            return
        
        # Update session activity if connection_id is provided
        if connection_id:
            mcp_session_service.update_session_activity(connection_id)
            logger.debug(f"📨 MCP message received for session: {connection_id[:8]}...")
        
        # Use the SSE transport's handle_post_message ASGI app
        # This will send its own response (202 Accepted), so we don't need to handle it
        try:
            await sse_transport.handle_post_message(scope, receive, send)
        except Exception as e:
            # If handle_post_message fails, don't let global exception handler catch it
            # as it may have already sent a response
            logger.error(f"❌ MCP handle_post_message error: {e}", exc_info=True)
            # Don't re-raise - response may have already been sent


@router.get("/sse")
@router.post("/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server SSE (Server-Sent Events) endpoint for Cursor integration.
    Supports both local development and Azure deployment.
    
    NOTE: This endpoint uses a custom ASGI app that handles its own responses.
    We don't return anything to avoid FastAPI trying to send a response.
    """
    logger.info(f"🔥 DEBUG: mcp_sse_endpoint called! Method: {request.method}, URL: {request.url}")
    logger.info(f"🔥 DEBUG: Headers: {dict(request.headers)}")
    
    app = MCPSSEASGIApp()
    try:
        logger.info(f"🔥 DEBUG: About to call MCPSSEASGIApp...")
        await app(request.scope, request.receive, request._send)
        logger.info(f"🔥 DEBUG: MCPSSEASGIApp returned")
    except (ConnectionError, BrokenPipeError, OSError) as e:
        # Connection closed gracefully - don't log as error
        import logging
        logging.info(f"MCP SSE connection closed gracefully: {e}")
    except RuntimeError as e:
        # "Response already sent" errors are expected - ignore them
        if "Response already sent" in str(e) or "already completed" in str(e):
            pass  # Ignore - this is expected when client disconnects
        else:
            import logging
            logging.error(f"MCP SSE endpoint error: {e}", exc_info=True)
    except Exception as e:
        # Log but don't raise - ASGI app may have already sent response
        import logging
        logging.error(f"MCP SSE endpoint error: {e}", exc_info=True)
    # Don't return anything - ASGI app already handled the response


@router.post("/messages/{path:path}")
async def mcp_messages_endpoint(path: str, request: Request):
    """
    MCP Server messages endpoint for POST requests.
    Used by Cursor to send messages to the MCP server.
    
    NOTE: This endpoint uses a custom ASGI app that handles its own responses.
    We don't return anything to avoid FastAPI trying to send a response.
    """
    app = MCPMessagesASGIApp()
    try:
        await app(request.scope, request.receive, request._send)
    except (ConnectionError, BrokenPipeError, OSError) as e:
        # Connection closed gracefully - don't log as error
        import logging
        logging.info(f"MCP messages connection closed gracefully: {e}")
    except RuntimeError as e:
        # "Response already sent" errors are expected - ignore them
        if "Response already sent" in str(e) or "already completed" in str(e):
            pass  # Ignore - this is expected when client disconnects
        else:
            import logging
            logging.error(f"MCP messages endpoint error: {e}", exc_info=True)
    except Exception as e:
        # Log but don't raise - ASGI app may have already sent response
        import logging
        logging.error(f"MCP messages endpoint error: {e}", exc_info=True)
    # Don't return anything - ASGI app already handled the response
