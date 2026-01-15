"""HTTP client utility with timeout and retry logic."""
import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
from httpx import Timeout, Limits

logger = logging.getLogger(__name__)

# Default timeout values (in seconds)
DEFAULT_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_READ_TIMEOUT = 30.0
DEFAULT_WRITE_TIMEOUT = 10.0

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # Initial delay in seconds
DEFAULT_RETRY_BACKOFF = 2.0  # Exponential backoff multiplier

# Retryable HTTP status codes
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Retryable exceptions
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.NetworkError,
)


class HTTPClient:
    """HTTP client with timeout and retry logic.
    
    This client provides:
    - Configurable timeouts (connect, read, write, total)
    - Automatic retry with exponential backoff
    - Retryable status codes and exceptions
    - Connection pooling
    """
    
    def __init__(
        self,
        timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
        limits: Optional[Limits] = None,
    ):
        """Initialize HTTP client.
        
        Args:
            timeout: Total timeout for requests (default: 30s)
            connect_timeout: Connection timeout (default: 10s)
            read_timeout: Read timeout (default: 30s)
            write_timeout: Write timeout (default: 10s)
            max_retries: Maximum number of retries (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1s)
            retry_backoff: Exponential backoff multiplier (default: 2.0)
            limits: Connection pool limits
        """
        self.timeout = Timeout(
            timeout=timeout or DEFAULT_TIMEOUT,
            connect=connect_timeout or DEFAULT_CONNECT_TIMEOUT,
            read=read_timeout or DEFAULT_READ_TIMEOUT,
            write=write_timeout or DEFAULT_WRITE_TIMEOUT,
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.limits = limits or Limits(max_connections=100, max_keepalive_connections=20)
    
    async def request(
        self,
        method: str,
        url: str,
        *,
        retries: Optional[int] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            retries: Override max_retries for this request
            **kwargs: Additional arguments passed to httpx.AsyncClient.request()
        
        Returns:
            httpx.Response object
        
        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        max_retries = retries if retries is not None else self.max_retries
        delay = self.retry_delay
        last_exception = None
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
        ) as client:
            for attempt in range(max_retries + 1):
                try:
                    response = await client.request(method, url, **kwargs)
                    
                    # Check if status code is retryable
                    if response.status_code in RETRYABLE_STATUS_CODES and attempt < max_retries:
                        logger.warning(
                            f"Request to {url} returned retryable status {response.status_code}, "
                            f"attempt {attempt + 1}/{max_retries + 1}"
                        )
                        await asyncio.sleep(delay)
                        delay *= self.retry_backoff
                        continue
                    
                    # Success or non-retryable error
                    return response
                
                except RETRYABLE_EXCEPTIONS as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Request to {url} failed with {type(e).__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}: {e}"
                        )
                        await asyncio.sleep(delay)
                        delay *= self.retry_backoff
                    else:
                        logger.error(
                            f"Request to {url} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise httpx.HTTPError(f"Request to {url} failed after {max_retries + 1} attempts")
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return await self.request("PUT", url, **kwargs)
    
    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Make PATCH request."""
        return await self.request("PATCH", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return await self.request("DELETE", url, **kwargs)


# Global HTTP client instance with default settings
default_http_client = HTTPClient()

# Convenience functions using the default client
async def get(url: str, **kwargs) -> httpx.Response:
    """Make GET request using default HTTP client."""
    return await default_http_client.get(url, **kwargs)


async def post(url: str, **kwargs) -> httpx.Response:
    """Make POST request using default HTTP client."""
    return await default_http_client.post(url, **kwargs)


async def put(url: str, **kwargs) -> httpx.Response:
    """Make PUT request using default HTTP client."""
    return await default_http_client.put(url, **kwargs)


async def patch(url: str, **kwargs) -> httpx.Response:
    """Make PATCH request using default HTTP client."""
    return await default_http_client.patch(url, **kwargs)


async def delete(url: str, **kwargs) -> httpx.Response:
    """Make DELETE request using default HTTP client."""
    return await default_http_client.delete(url, **kwargs)
