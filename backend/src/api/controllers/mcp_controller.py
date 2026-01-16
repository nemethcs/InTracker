"""MCP Server HTTP/SSE transport controller for FastAPI."""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from starlette.types import Receive, Send, Scope
from mcp.server.sse import SseServerTransport
from src.config import settings
from src.mcp.server import server as mcp_server

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Create SSE transport
sse_transport = SseServerTransport("/mcp/messages/")


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
    """ASGI app wrapper for MCP SSE endpoint."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        print(f"🔌 MCPSSEASGIApp called: {scope['method']} {scope['path']}", flush=True)
        if scope["type"] != "http" or scope["method"] != "GET":
            from starlette.responses import Response
            response = Response(status_code=405)
            await response(scope, receive, send)
            return
        
        # Verify API key and get user_id
        api_key = None
        headers = scope.get("headers", [])
        for key, value in headers:
            if key.lower() == b"x-api-key":
                api_key = value.decode()
                break
        
        print(f"🔑 API key present: {bool(api_key)}", flush=True)
        try:
            user_id = verify_api_key(api_key)
            print(f"✅ API key verified, user_id: {user_id}", flush=True)
            # Set the user_id in MCP middleware for this connection
            if user_id:
                from src.mcp.middleware.auth import set_mcp_api_key
                set_mcp_api_key(api_key)  # This will extract and set user_id
        except HTTPException as e:
            print(f"❌ API key verification failed: {e.detail}", flush=True)
            # Return error response and stop processing
            # Don't re-raise to avoid global exception handler duplicate response
            response = JSONResponse(
                content={"detail": e.detail},
                status_code=e.status_code
            )
            await response(scope, receive, send)
            return
        
        # Based on MCP SDK source code inspection:
        # connect_sse returns an async context manager
        # When entered, it returns (read_stream, write_stream)
        # We need to run the MCP server with these streams
        try:
            print("🔄 Establishing MCP SSE connection...", flush=True)
            cm = sse_transport.connect_sse(scope, receive, send)
            async with cm as streams:
                read_stream, write_stream = streams
                print("✅ MCP SSE streams established, starting server...", flush=True)
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
        except Exception as e:
            # If MCP server fails, don't let global exception handler catch it
            # as it may have already sent a response
            print(f"❌ MCP SSE connection error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            # Don't re-raise - response may have already been sent


class MCPMessagesASGIApp:
    """ASGI app wrapper for MCP messages endpoint."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        print(f"📨 MCPMessagesASGIApp called: {scope['method']} {scope['path']}", flush=True)
        if scope["type"] != "http" or scope["method"] != "POST":
            from starlette.responses import Response
            response = Response(status_code=405)
            await response(scope, receive, send)
            return
        
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
        
        # Use the SSE transport's handle_post_message ASGI app
        # This will send its own response (202 Accepted), so we don't need to handle it
        try:
            await sse_transport.handle_post_message(scope, receive, send)
        except Exception as e:
            # If handle_post_message fails, don't let global exception handler catch it
            # as it may have already sent a response
            print(f"❌ MCP handle_post_message error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            # Don't re-raise - response may have already been sent


@router.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server SSE (Server-Sent Events) endpoint for Cursor integration.
    Supports both local development and Azure deployment.
    
    NOTE: This endpoint uses a custom ASGI app that handles its own responses.
    We don't return anything to avoid FastAPI trying to send a response.
    """
    app = MCPSSEASGIApp()
    try:
        await app(request.scope, request.receive, request._send)
    except Exception as e:
        # Log but don't raise - ASGI app may have already sent response
        print(f"❌ MCP SSE endpoint error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    # Don't return anything - ASGI app already handled the response


@router.post("/messages")
async def mcp_messages_endpoint_no_path(request: Request):
    """
    MCP Server messages endpoint for POST requests without path.
    Used by streamableHttp transport.
    
    NOTE: This endpoint uses a custom ASGI app that handles its own responses.
    We don't return anything to avoid FastAPI trying to send a response.
    """
    app = MCPMessagesASGIApp()
    try:
        await app(request.scope, request.receive, request._send)
    except Exception as e:
        # Log but don't raise - ASGI app may have already sent response
        import logging
        logging.error(f"MCP messages endpoint error: {e}", exc_info=True)
    # Don't return anything - ASGI app already handled the response


@router.post("/messages/{path:path}")
async def mcp_messages_endpoint(path: str, request: Request):
    """
    MCP Server messages endpoint for POST requests with path.
    Used by Cursor to send messages to the MCP server.
    
    NOTE: This endpoint uses a custom ASGI app that handles its own responses.
    We don't return anything to avoid FastAPI trying to send a response.
    """
    app = MCPMessagesASGIApp()
    try:
        await app(request.scope, request.receive, request._send)
    except Exception as e:
        # Log but don't raise - ASGI app may have already sent response
        import logging
        logging.error(f"MCP messages endpoint error: {e}", exc_info=True)
    # Don't return anything - ASGI app already handled the response
