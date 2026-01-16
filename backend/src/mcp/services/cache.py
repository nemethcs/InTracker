"""Cache service for MCP Server.

This module re-exports the unified cache service from src.services.cache_service
to maintain backward compatibility with existing MCP tools.

All MCP tools should use this module, which provides the same interface
but uses the unified cache service implementation.
"""
# Re-export from unified cache service
from src.services.cache_service import (
    CacheService,
    CacheTTL,
    cache_service,
    get_redis_client,
)

# Maintain backward compatibility - export CacheService as class
__all__ = ["CacheService", "CacheTTL", "cache_service", "get_redis_client"]
