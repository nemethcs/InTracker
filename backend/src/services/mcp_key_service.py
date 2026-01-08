"""MCP API Key Service for user-specific MCP authentication."""
import secrets
import hashlib
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.models import McpApiKey, User


class McpKeyService:
    """Service for managing MCP API keys."""

    @staticmethod
    def generate_key() -> str:
        """Generate a secure random API key.
        
        Returns a URL-safe base64-encoded key (32 bytes = 44 characters).
        Format: intracker_mcp_<random_token>
        """
        # Generate 32 random bytes and encode as URL-safe base64
        random_bytes = secrets.token_bytes(32)
        token = secrets.token_urlsafe(32)  # 32 bytes = 44 characters
        return f"intracker_mcp_{token}"

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for secure storage.
        
        Uses SHA-256 hashing.
        """
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_key(key: str, key_hash: str) -> bool:
        """Verify an API key against its hash."""
        return McpKeyService.hash_key(key) == key_hash

    @staticmethod
    def create_key(
        db: Session,
        user_id: UUID,
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple[McpApiKey, str]:
        """Create a new MCP API key for a user.
        
        Returns:
            Tuple of (McpApiKey model, plain_text_key)
            The plain_text_key should be shown to the user once and never stored.
        """
        # Generate new key
        plain_text_key = McpKeyService.generate_key()
        key_hash = McpKeyService.hash_key(plain_text_key)

        # Calculate expiration date if provided
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create key record
        api_key = McpApiKey(
            user_id=user_id,
            key_hash=key_hash,
            name=name,
            expires_at=expires_at,
            is_active=True,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return api_key, plain_text_key

    @staticmethod
    def verify_and_get_user_id(db: Session, key: str) -> Optional[UUID]:
        """Verify an API key and return the associated user_id.
        
        Returns:
            user_id if key is valid and active, None otherwise
        """
        key_hash = McpKeyService.hash_key(key)

        # Find the key
        api_key = (
            db.query(McpApiKey)
            .filter(
                McpApiKey.key_hash == key_hash,
                McpApiKey.is_active == True,
            )
            .first()
        )

        if not api_key:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # Update last_used_at
        api_key.last_used_at = datetime.utcnow()
        db.commit()

        return api_key.user_id

    @staticmethod
    def get_keys_by_user(db: Session, user_id: UUID, include_inactive: bool = False) -> list[McpApiKey]:
        """Get all MCP API keys for a user."""
        query = db.query(McpApiKey).filter(McpApiKey.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(McpApiKey.is_active == True)
        
        return query.order_by(McpApiKey.created_at.desc()).all()

    @staticmethod
    def revoke_key(db: Session, key_id: UUID, user_id: UUID) -> bool:
        """Revoke (deactivate) an MCP API key.
        
        Only the key owner can revoke their own keys.
        Returns True if key was revoked, False if not found or not authorized.
        """
        api_key = db.query(McpApiKey).filter(
            McpApiKey.id == key_id,
            McpApiKey.user_id == user_id,
        ).first()

        if not api_key:
            return False

        api_key.is_active = False
        db.commit()
        return True

    @staticmethod
    def delete_key(db: Session, key_id: UUID, user_id: UUID) -> bool:
        """Delete an MCP API key permanently.
        
        Only the key owner can delete their own keys.
        Returns True if key was deleted, False if not found or not authorized.
        """
        api_key = db.query(McpApiKey).filter(
            McpApiKey.id == key_id,
            McpApiKey.user_id == user_id,
        ).first()

        if not api_key:
            return False

        db.delete(api_key)
        db.commit()
        return True

    @staticmethod
    def get_key_by_id(db: Session, key_id: UUID, user_id: UUID) -> Optional[McpApiKey]:
        """Get a specific MCP API key by ID.
        
        Only returns the key if it belongs to the user.
        """
        return (
            db.query(McpApiKey)
            .filter(
                McpApiKey.id == key_id,
                McpApiKey.user_id == user_id,
            )
            .first()
        )


# Global instance
mcp_key_service = McpKeyService()
