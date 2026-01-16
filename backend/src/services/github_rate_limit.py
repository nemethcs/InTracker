"""GitHub API rate limit handler with retry logic and caching."""
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from github import Github
from github.GithubException import GithubException
from src.services.cache_service import CacheService
from src.services.cache_service import CacheTTL

logger = logging.getLogger(__name__)

# Rate limit cache keys
RATE_LIMIT_CACHE_PREFIX = "github_rate_limit:"
RATE_LIMIT_RESET_CACHE_PREFIX = "github_rate_limit_reset:"


class GitHubRateLimitHandler:
    """Handler for GitHub API rate limiting with retry logic.
    
    Features:
    - Automatic rate limit detection
    - Retry with exponential backoff
    - Rate limit information caching
    - Respects X-RateLimit-Reset header
    - Prevents unnecessary API calls when rate limited
    """
    
    @staticmethod
    def is_rate_limit_error(exception: Exception) -> bool:
        """Check if exception is a rate limit error.
        
        GitHub API returns:
        - 403 Forbidden with "API rate limit exceeded" message
        - 429 Too Many Requests (for secondary rate limits)
        """
        if isinstance(exception, GithubException):
            # Check status code
            if exception.status == 403:
                # Check if it's a rate limit error
                error_data = exception.data if hasattr(exception, 'data') else {}
                error_message = str(error_data).lower() if error_data else ""
                if "rate limit" in error_message or "api rate limit exceeded" in error_message:
                    return True
            elif exception.status == 429:
                return True
        return False
    
    @staticmethod
    def get_rate_limit_info(client: Github) -> Optional[Dict[str, Any]]:
        """Get current rate limit information from GitHub API.
        
        Returns:
            Dict with 'limit', 'remaining', 'reset' keys, or None if unavailable
        """
        try:
            rate_limit = client.get_rate_limit()
            return {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": rate_limit.core.reset.timestamp() if rate_limit.core.reset else None,
            }
        except Exception as e:
            logger.warning(f"Failed to get rate limit info: {e}")
            return None
    
    @staticmethod
    def get_cached_rate_limit_info(token_key: str) -> Optional[Dict[str, Any]]:
        """Get cached rate limit information.
        
        Args:
            token_key: Cache key for the token (e.g., user_id or 'global')
            
        Returns:
            Cached rate limit info or None
        """
        cache_key = f"{RATE_LIMIT_CACHE_PREFIX}{token_key}"
        cached = CacheService.get_cache(cache_key)
        if cached:
            # Check if still valid (cache for 1 minute)
            reset_time = cached.get("reset")
            if reset_time and time.time() < reset_time:
                return cached
        return None
    
    @staticmethod
    def cache_rate_limit_info(token_key: str, info: Dict[str, Any]) -> None:
        """Cache rate limit information.
        
        Args:
            token_key: Cache key for the token
            info: Rate limit info dict
        """
        cache_key = f"{RATE_LIMIT_CACHE_PREFIX}{token_key}"
        # Cache until reset time, or 1 minute minimum
        reset_time = info.get("reset")
        if reset_time:
            ttl = max(int(reset_time - time.time()), 60)  # At least 1 minute
        else:
            ttl = CacheTTL.SHORT  # 1 minute default
        
        CacheService.set_cache(cache_key, info, ttl=ttl)
    
    @staticmethod
    def should_wait_for_rate_limit(token_key: str, client: Optional[Github] = None) -> Optional[float]:
        """Check if we should wait for rate limit reset.
        
        Args:
            token_key: Cache key for the token
            client: Optional GitHub client to check current rate limit
            
        Returns:
            Seconds to wait until rate limit resets, or None if no wait needed
        """
        # Check cache first
        cached_info = GitHubRateLimitHandler.get_cached_rate_limit_info(token_key)
        if cached_info:
            remaining = cached_info.get("remaining", 0)
            if remaining == 0:
                reset_time = cached_info.get("reset")
                if reset_time:
                    wait_time = reset_time - time.time()
                    if wait_time > 0:
                        return wait_time
        
        # If client provided, check current rate limit
        if client:
            try:
                info = GitHubRateLimitHandler.get_rate_limit_info(client)
                if info:
                    GitHubRateLimitHandler.cache_rate_limit_info(token_key, info)
                    remaining = info.get("remaining", 0)
                    if remaining == 0:
                        reset_time = info.get("reset")
                        if reset_time:
                            wait_time = reset_time - time.time()
                            if wait_time > 0:
                                return wait_time
            except Exception as e:
                logger.warning(f"Failed to check rate limit: {e}")
        
        return None
    
    @staticmethod
    async def handle_rate_limit_error(
        exception: GithubException,
        token_key: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> bool:
        """Handle rate limit error with retry logic.
        
        Args:
            exception: The GithubException that occurred
            token_key: Cache key for the token
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds for exponential backoff
            
        Returns:
            True if should retry, False otherwise
        """
        if not GitHubRateLimitHandler.is_rate_limit_error(exception):
            return False
        
        # Extract reset time from exception if available
        reset_time = None
        if hasattr(exception, 'data') and exception.data:
            # Try to extract reset time from error message
            error_str = str(exception.data).lower()
            if "reset" in error_str:
                # Try to parse reset time (format varies)
                # GitHub usually includes reset time in error message
                try:
                    # Look for timestamp in error message
                    import re
                    timestamp_match = re.search(r'(\d{10})', str(exception.data))
                    if timestamp_match:
                        reset_time = float(timestamp_match.group(1))
                except:
                    pass
        
        # If no reset time found, use default (1 hour from now)
        if not reset_time:
            reset_time = time.time() + 3600  # 1 hour default
        
        # Cache the rate limit info
        GitHubRateLimitHandler.cache_rate_limit_info(token_key, {
            "limit": 5000,  # Default GitHub limit
            "remaining": 0,
            "reset": reset_time,
        })
        
        wait_time = reset_time - time.time()
        if wait_time > 0:
            logger.warning(
                f"GitHub API rate limit exceeded. Waiting {wait_time:.0f} seconds until reset "
                f"(reset at {datetime.fromtimestamp(reset_time).isoformat()})"
            )
            # Wait for rate limit reset
            time.sleep(min(wait_time, 3600))  # Max 1 hour wait
            return True
        
        return False
    
    @staticmethod
    def update_rate_limit_after_request(token_key: str, client: Github) -> None:
        """Update cached rate limit info after a successful request.
        
        Args:
            token_key: Cache key for the token
            client: GitHub client to check rate limit
        """
        try:
            info = GitHubRateLimitHandler.get_rate_limit_info(client)
            if info:
                GitHubRateLimitHandler.cache_rate_limit_info(token_key, info)
        except Exception as e:
            logger.debug(f"Failed to update rate limit info: {e}")
