"""Service for onboarding and setup completion logic."""
from sqlalchemy.orm import Session
from uuid import UUID
from src.database.models import User, McpApiKey


def update_setup_completed(db: Session, user_id: UUID) -> bool:
    """Update user's setup_completed status based on MCP key and GitHub connection.
    
    Returns True if setup is now complete, False otherwise.
    Also updates onboarding_step to 5 (complete) if setup is complete.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Check if user has active MCP key
    has_mcp_key = (
        db.query(McpApiKey)
        .filter(
            McpApiKey.user_id == user_id,
            McpApiKey.is_active == True,
        )
        .first() is not None
    )
    
    # Check if user has GitHub connected
    has_github = user.github_access_token_encrypted is not None
    
    # Update setup_completed
    new_setup_completed = has_mcp_key and has_github
    
    if user.setup_completed != new_setup_completed:
        user.setup_completed = new_setup_completed
        
        # If setup is complete, update onboarding_step to 5 (complete)
        if new_setup_completed and user.onboarding_step < 5:
            user.onboarding_step = 5
        
        db.commit()
        db.refresh(user)
    
    return new_setup_completed
