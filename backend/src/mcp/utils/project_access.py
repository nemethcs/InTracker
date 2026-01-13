"""Utility functions for project access validation in MCP tools."""
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.services.github_access_service import github_access_service
from src.mcp.middleware.auth import get_current_user_id


def validate_project_access(
    db: Session,
    project_id: str,
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """Validate that the current user has access to a project via GitHub OAuth token.
    
    Args:
        db: Database session
        project_id: Project UUID as string
        
    Returns:
        Tuple of (has_access, error_dict)
        - has_access: True if user has access, False otherwise
        - error_dict: Error dictionary with "error" key if access denied, None if access granted
    """
    user_id = get_current_user_id()
    if not user_id:
        return False, {"error": "User not authenticated"}
    
    try:
        access_validation = github_access_service.validate_single_project_access(
            db=db,
            user_id=user_id,
            project_id=UUID(project_id),
        )
        
        if not access_validation["has_access"]:
            error_msg = access_validation.get("error", "User does not have access to this project")
            return False, {"error": f"Cannot access project: {error_msg}"}
        
        return True, None
    except Exception as e:
        return False, {"error": f"Error validating project access: {str(e)}"}
