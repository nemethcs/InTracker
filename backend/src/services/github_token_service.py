"""GitHub token management service with automatic refresh."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.database.models import User
from src.services.github_oauth_service import github_oauth_service
from src.database.base import SessionLocal


class GitHubTokenService:
    """Service for managing GitHub OAuth tokens with automatic refresh."""
    
    @staticmethod
    def get_user_token(db: Session, user_id: UUID) -> Optional[str]:
        """Get user's GitHub access token, refreshing if expired.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            Decrypted access token, or None if user has no token or refresh fails
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"⚠️  get_user_token: User {user_id} not found")
            return None
        
        # Check if user has a token
        if not user.github_access_token_encrypted:
            print(f"⚠️  get_user_token: User {user_id} ({user.email}) has no github_access_token_encrypted")
            return None
        
        # Check if token is expired (with 5 minute buffer)
        now = datetime.utcnow()
        buffer = timedelta(minutes=5)
        
        if user.github_token_expires_at and user.github_token_expires_at < (now + buffer):
            # Token is expired or will expire soon, try to refresh
            refreshed = GitHubTokenService.refresh_user_token(db, user_id)
            if refreshed:
                # Reload user to get new token
                db.refresh(user)
                if user.github_access_token_encrypted:
                    return github_oauth_service.decrypt_token(user.github_access_token_encrypted)
            else:
                # Refresh failed, return None
                return None
        
        # Token is still valid, decrypt and return
        return github_oauth_service.decrypt_token(user.github_access_token_encrypted)
    
    @staticmethod
    def refresh_user_token(db: Session, user_id: UUID) -> bool:
        """Refresh user's GitHub access token using refresh token.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            True if refresh was successful, False otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Check if user has a refresh token
        if not user.github_refresh_token_encrypted:
            return False
        
        # Check if refresh token is expired
        if user.github_refresh_token_expires_at and user.github_refresh_token_expires_at < datetime.utcnow():
            # Refresh token is expired, cannot refresh
            # Clear tokens
            user.github_access_token_encrypted = None
            user.github_refresh_token_encrypted = None
            user.github_token_expires_at = None
            user.github_refresh_token_expires_at = None
            db.commit()
            return False
        
        # Decrypt refresh token
        refresh_token = github_oauth_service.decrypt_token(user.github_refresh_token_encrypted)
        if not refresh_token:
            return False
        
        try:
            # Refresh access token
            import asyncio
            token_data = asyncio.run(github_oauth_service.refresh_access_token(refresh_token))
            
            # Encrypt new tokens
            encrypted_access_token = github_oauth_service.encrypt_token(token_data["access_token"])
            encrypted_refresh_token = None
            if token_data.get("refresh_token"):
                encrypted_refresh_token = github_oauth_service.encrypt_token(token_data["refresh_token"])
            else:
                # If no new refresh token, keep the old one
                encrypted_refresh_token = user.github_refresh_token_encrypted
            
            # Update user with new tokens
            user.github_access_token_encrypted = encrypted_access_token
            user.github_refresh_token_encrypted = encrypted_refresh_token
            user.github_token_expires_at = token_data["expires_at"]
            if token_data.get("refresh_expires_at"):
                user.github_refresh_token_expires_at = token_data["refresh_expires_at"]
            
            db.commit()
            db.refresh(user)
            return True
        except Exception as e:
            print(f"⚠️  Failed to refresh GitHub token for user {user_id}: {e}")
            # If refresh fails, clear tokens (they might be invalid)
            user.github_access_token_encrypted = None
            user.github_refresh_token_encrypted = None
            user.github_token_expires_at = None
            user.github_refresh_token_expires_at = None
            db.commit()
            return False
    
    @staticmethod
    def is_token_valid(db: Session, user_id: UUID) -> bool:
        """Check if user has a valid (non-expired) GitHub token.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            True if user has a valid token, False otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not user.github_access_token_encrypted:
            return False
        
        # Check if token is expired
        if user.github_token_expires_at and user.github_token_expires_at < datetime.utcnow():
            return False
        
        return True
    
    @staticmethod
    def disconnect_github(db: Session, user_id: UUID) -> bool:
        """Disconnect GitHub OAuth by clearing all tokens.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            True if disconnection was successful, False otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Clear all GitHub OAuth data
        user.github_access_token_encrypted = None
        user.github_refresh_token_encrypted = None
        user.github_token_expires_at = None
        user.github_refresh_token_expires_at = None
        user.github_connected_at = None
        user.github_username = None
        user.avatar_url = None
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return True


# Global instance
github_token_service = GitHubTokenService()
