"""MCP Server FastAPI integration using fastapi-mcp library."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from src.config import settings
from src.mcp.server import server as mcp_server

router = APIRouter(prefix="/mcp", tags=["mcp"])


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


# Initialize FastApiMCP - this will be called from main.py
def setup_mcp(app):
    """Setup MCP server with FastAPI app using fastapi-mcp library.
    
    This must be called AFTER including the router in the main app.
    """
    # Custom auth middleware for API key verification
    async def auth_middleware(headers: dict):
        """Custom auth middleware for MCP requests."""
        api_key = headers.get("x-api-key")
        try:
            user_id = verify_api_key(api_key)
            
            # Set user_id in MCP context if available
            if user_id:
                from src.mcp.middleware.auth import set_mcp_api_key
                set_mcp_api_key(api_key)
            
            return True
        except HTTPException:
            return False
    
    # Create FastApiMCP instance and mount it
    mcp = FastApiMCP(
        server=mcp_server,
        path="/mcp",
    )
    
    # Mount MCP to the FastAPI app
    mcp.mount(app)
    
    print("✅ MCP server mounted at /mcp with fastapi-mcp", flush=True)
