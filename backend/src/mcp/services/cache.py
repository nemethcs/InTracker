"""Cache service for MCP Server."""
import json
import redis
from typing import Optional, Any
from src.config import settings

# Redis client (singleton)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global _redis_client

    if _redis_client is None:
        try:
            # Use REDIS_URL if available (contains password and SSL settings)
            if settings.REDIS_URL:
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
            else:
                # Fallback to individual settings (for local development)
                _redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
            # Test connection
            _redis_client.ping()
        except Exception:
            # Graceful degradation - return None if Redis unavailable
            _redis_client = None

    return _redis_client


class CacheService:
    """Service for caching operations."""

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        client = get_redis_client()
        if not client:
            return None

        try:
            value = client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (default 5 minutes)."""
        client = get_redis_client()
        if not client:
            return False

        try:
            serialized = json.dumps(value)
            client.setex(key, ttl, serialized)
            return True
        except Exception:
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache."""
        client = get_redis_client()
        if not client:
            return False

        try:
            client.delete(key)
            return True
        except Exception:
            return False

    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern."""
        client = get_redis_client()
        if not client:
            return 0

        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception:
            return 0


# Global instance
cache_service = CacheService()
