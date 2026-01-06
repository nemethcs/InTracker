"""Cache service using Redis."""
import json
import redis
from typing import Optional, Any
from src.config import settings

# Redis client (singleton)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client

    if _redis_client is None:
        try:
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
            print(f"⚠️  Redis connection failed: {e}")
            # Return a mock client that does nothing (graceful degradation)
            _redis_client = None

    return _redis_client


class CacheService:
    """Service for caching operations."""

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
            print(f"⚠️  Cache get error: {e}")
            return None

    @staticmethod
    def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (default 5 minutes)."""
        client = get_redis_client()
        if not client:
            return False

        try:
            serialized = json.dumps(value)
            client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"⚠️  Cache set error: {e}")
            return False

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
            print(f"⚠️  Cache delete error: {e}")
            return False

    @staticmethod
    def clear_cache_by_pattern(pattern: str) -> int:
        """Clear all keys matching pattern."""
        client = get_redis_client()
        if not client:
            return 0

        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            print(f"⚠️  Cache clear error: {e}")
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


# Global instance
cache_service = CacheService()
