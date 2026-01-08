"""MCP Server authentication middleware."""
import os
from typing import Optional
from uuid import UUID
from src.database.base import SessionLocal
from src.services.mcp_key_service import mcp_key_service


# Global variable to store the current MCP API key (set during initialization)
_current_mcp_api_key: Optional[str] = None
_current_user_id: Optional[UUID] = None


def set_mcp_api_key(api_key: Optional[str]) -> None:
    """Set the MCP API key for the current session.
    
    This should be called during MCP server initialization.
    The API key can come from:
    - Environment variable: MCP_API_KEY
    - MCP initialization parameters
    - Command line arguments
    """
    global _current_mcp_api_key, _current_user_id
    
    _current_mcp_api_key = api_key
    
    # If API key is provided, verify it and extract user_id
    if api_key:
        db = SessionLocal()
        try:
            user_id = mcp_key_service.verify_and_get_user_id(db=db, key=api_key)
            _current_user_id = user_id
        except Exception as e:
            print(f"Error verifying MCP API key: {e}")
            _current_user_id = None
        finally:
            db.close()
    else:
        _current_user_id = None


def get_current_user_id() -> Optional[UUID]:
    """Get the current user ID from the MCP API key.
    
    Returns None if no valid API key is set or if verification fails.
    """
    return _current_user_id


def initialize_mcp_auth() -> None:
    """Initialize MCP authentication from environment variable.
    
    This should be called when the MCP server starts.
    """
    api_key = os.getenv("MCP_API_KEY")
    if api_key:
        set_mcp_api_key(api_key)
        print(f"MCP API key loaded from environment variable")
    else:
        print("No MCP_API_KEY environment variable set - MCP server running without user context")


# Initialize on module import
initialize_mcp_auth()
