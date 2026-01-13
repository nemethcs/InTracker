"""MCP Tools for user onboarding."""
from datetime import datetime
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.database.models import User
from src.mcp.middleware.auth import get_current_user_id
from src.services.signalr.broadcast_handlers import broadcast_mcp_verified


def get_verify_connection_tool() -> MCPTool:
    """Get verify connection tool definition."""
    return MCPTool(
        name="mcp_verify_connection",
        description="Verify that Cursor is connected and can communicate with the MCP server. This tool is used during onboarding to confirm MCP setup is complete.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


async def handle_verify_connection() -> dict:
    """Handle verify connection tool call.
    
    This tool verifies that Cursor is connected and can communicate with the MCP server.
    It saves the verification timestamp to the user's profile and broadcasts a SignalR event.
    
    Returns:
        dict: Verification result with verified status and message
    """
    user_id = get_current_user_id()
    if not user_id:
        return {
            "verified": False,
            "message": "Not authenticated. Please ensure you are using a valid MCP API key."
        }
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "verified": False,
                "message": "User not found."
            }
        
        # Save verification timestamp
        user.mcp_verified_at = datetime.utcnow()
        # Update onboarding step to 3 (mcp_verified)
        if user.onboarding_step < 3:
            user.onboarding_step = 3
        db.commit()
        db.refresh(user)
        
        # Broadcast SignalR event for real-time frontend update
        await broadcast_mcp_verified(
            str(user_id),
            user.mcp_verified_at.isoformat() if user.mcp_verified_at else None
        )
        
        return {
            "verified": True,
            "message": "MCP connection verified successfully",
            "verified_at": user.mcp_verified_at.isoformat() if user.mcp_verified_at else None
        }
    except Exception as e:
        db.rollback()
        return {
            "verified": False,
            "message": f"Failed to verify connection: {str(e)}"
        }
    finally:
        db.close()
