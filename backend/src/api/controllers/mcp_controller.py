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


def verify_api_key(api_key: Optional[str]) -> None:
    """Verify API key."""
    if not settings.MCP_API_KEY:
        # If no API key is set, allow all requests (development)
        return
    
    if not api_key or api_key != settings.MCP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@router.get("/health")
async def mcp_health_check():
    """MCP server health check endpoint."""
    return JSONResponse(content={"status": "ok", "service": "intracker-mcp-server"})


class MCPSSEASGIApp:
    """ASGI app wrapper for MCP SSE endpoint."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] != "GET":
            from starlette.responses import Response
            response = Response(status_code=405)
            await response(scope, receive, send)
            return
        
        # Verify API key
        api_key = None
        headers = scope.get("headers", [])
        for key, value in headers:
            if key.lower() == b"x-api-key":
                api_key = value.decode()
                break
        
        try:
            verify_api_key(api_key)
        except HTTPException as e:
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
        cm = sse_transport.connect_sse(scope, receive, send)
        async with cm as streams:
            read_stream, write_stream = streams
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )


class MCPMessagesASGIApp:
    """ASGI app wrapper for MCP messages endpoint."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] != "POST":
            from starlette.responses import Response
            response = Response(status_code=405)
            await response(scope, receive, send)
            return
        
        # Verify API key
        api_key = None
        headers = scope.get("headers", [])
        for key, value in headers:
            if key.lower() == b"x-api-key":
                api_key = value.decode()
                break
        
        try:
            verify_api_key(api_key)
        except HTTPException as e:
            response = JSONResponse(
                content={"detail": e.detail},
                status_code=e.status_code
            )
            await response(scope, receive, send)
            return
        
        # Use the SSE transport's handle_post_message ASGI app
        await sse_transport.handle_post_message(scope, receive, send)


@router.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server SSE (Server-Sent Events) endpoint for Cursor integration.
    Supports both local development and Azure deployment.
    """
    app = MCPSSEASGIApp()
    await app(request.scope, request.receive, request._send)


@router.post("/messages/{path:path}")
async def mcp_messages_endpoint(path: str, request: Request):
    """
    MCP Server messages endpoint for POST requests.
    Used by Cursor to send messages to the MCP server.
    """
    app = MCPMessagesASGIApp()
    await app(request.scope, request.receive, request._send)
