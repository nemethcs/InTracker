"""Cache service using Redis.

This service provides a unified caching interface for the entire application.
It includes:
- Standardized TTL constants for different cache types
- Cache key naming conventions
- Automatic cache invalidation helpers
- Graceful degradation when Redis is unavailable
"""
import json
import redis
from typing import Optional, Any
from src.config import settings
import logging

logger = logging.getLogger(__name__)

# Redis client (singleton)
_redis_client: Optional[redis.Redis] = None

# Standardized TTL constants (in seconds)
class CacheTTL:
    """Standard TTL values for different cache types."""
    # Short-lived caches (frequently changing data)
    SHORT = 60  # 1 minute - for resume context, active todos
    
    # Medium-lived caches (moderately changing data)
    MEDIUM = 120  # 2 minutes - for features, todos, project lists
    
    # Long-lived caches (rarely changing data)
    LONG = 300  # 5 minutes - for project context, documents
    
    # Very long-lived caches (static or rarely changing data)
    VERY_LONG = 600  # 10 minutes - for OAuth tokens, static data
    
    # Session caches
    SESSION = 86400  # 24 hours - for MCP sessions


def get_redis_client() -> redis.Redis:
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
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            # Return a mock client that does nothing (graceful degradation)
            _redis_client = None

    return _redis_client


class CacheService:
    """Service for caching operations with standardized TTL and key naming."""

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache. Alias for get_cache for backward compatibility."""
        return CacheService.get_cache(key)

    @staticmethod
    def get_cache(key: str) -> Optional[Any]:
        """Get value from cache."""
        client = get_redis_client()
        if not client:
            return None

        try:
            value = client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = CacheTTL.LONG) -> bool:
        """Set value in cache. Alias for set_cache for backward compatibility."""
        return CacheService.set_cache(key, value, ttl)

    @staticmethod
    def set_cache(key: str, value: Any, ttl: int = CacheTTL.LONG) -> bool:
        """Set value in cache with TTL (default: LONG = 5 minutes).
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (use CacheTTL constants)
        """
        client = get_redis_client()
        if not client:
            return False

        try:
            serialized = json.dumps(value)
            client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache. Alias for delete_cache for backward compatibility."""
        return CacheService.delete_cache(key)

    @staticmethod
    def delete_cache(key: str) -> bool:
        """Delete key from cache."""
        client = get_redis_client()
        if not client:
            return False

        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern. Alias for clear_cache_by_pattern."""
        return CacheService.clear_cache_by_pattern(pattern)

    @staticmethod
    def clear_cache_by_pattern(pattern: str) -> int:
        """Clear all keys matching pattern.
        
        Note: This uses Redis KEYS command which can be slow on large datasets.
        Consider using SCAN for production environments with many keys.
        """
        client = get_redis_client()
        if not client:
            return 0

        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0

    @staticmethod
    def invalidate_project_cache(project_id: str) -> None:
        """Invalidate all project-related caches."""
        patterns = [
            f"project:{project_id}:*",
            f"feature:*:project:{project_id}",
            f"user:*:project:{project_id}",
        ]
        for pattern in patterns:
            CacheService.clear_cache_by_pattern(pattern)

    @staticmethod
    def invalidate_feature_cache(feature_id: str) -> None:
        """Invalidate feature cache."""
        CacheService.delete_cache(f"feature:{feature_id}")

    @staticmethod
    def invalidate_user_cache(user_id: str, project_id: Optional[str] = None) -> None:
        """Invalidate user cache."""
        if project_id:
            CacheService.delete_cache(f"user:{user_id}:project:{project_id}")
        else:
            CacheService.clear_cache_by_pattern(f"user:{user_id}:*")

    @staticmethod
    def invalidate_document_cache(document_id: str) -> None:
        """Invalidate document cache."""
        CacheService.delete_cache(f"document:{document_id}")

    @staticmethod
    def invalidate_todo_cache(todo_id: str, project_id: Optional[str] = None) -> None:
        """Invalidate todo-related caches."""
        CacheService.delete_cache(f"todo:{todo_id}")
        if project_id:
            CacheService.clear_cache_by_pattern(f"project:{project_id}:*")


# Global instance (for backward compatibility)
cache_service = CacheService()
