"""HTTP transport wrapper for MCP Server (for Azure deployment)."""
import json
from typing import Optional
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import Receive, Send, Scope
from mcp.server.sse import SseServerTransport
from src.config import settings
from src.server import server as mcp_server

# Create SSE transport
sse_transport = SseServerTransport("/mcp/messages/")


def verify_api_key(api_key: Optional[str]) -> None:
    """Verify API key."""
    if not settings.MCP_API_KEY:
        # If no API key is set, allow all requests (development)
        return
    
    if not api_key or api_key != settings.MCP_API_KEY:
        raise ValueError("Invalid or missing API key")


async def health_check_endpoint(request: Request):
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok", "service": "intracker-mcp-server"})


class MCPSSEASGIApp:
    """ASGI app wrapper for MCP SSE endpoint."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] != "GET":
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
        except ValueError:
            response = JSONResponse(
                content={"detail": "Invalid or missing API key"},
                status_code=401
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
        except ValueError:
            response = JSONResponse(
                content={"detail": "Invalid or missing API key"},
                status_code=401
            )
            await response(scope, receive, send)
            return
        
        # Use the SSE transport's handle_post_message ASGI app
        await sse_transport.handle_post_message(scope, receive, send)


# Create Starlette app with routes
app = Starlette(
    routes=[
        Route("/health", health_check_endpoint),
        Route("/mcp/sse", MCPSSEASGIApp()),
        Route("/mcp/messages/{path:path}", MCPMessagesASGIApp(), methods=["POST"]),
    ]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(settings.MCP_HTTP_PORT) if hasattr(settings, 'MCP_HTTP_PORT') else 3001,
    )
