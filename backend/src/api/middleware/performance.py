"""Performance monitoring middleware for FastAPI."""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
from src.utils.error_logger import log_performance_issue
from src.config import settings

logger = logging.getLogger(__name__)

# Performance thresholds (in seconds)
SLOW_REQUEST_THRESHOLD = 1.0  # Log requests taking longer than 1 second
VERY_SLOW_REQUEST_THRESHOLD = 3.0  # Log as error requests taking longer than 3 seconds


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor and log request performance.
    
    Tracks:
    - Request duration
    - Slow requests (>1s)
    - Very slow requests (>3s)
    - Request path and method
    
    Logs performance issues using the centralized error logger.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Measure request duration and log slow requests."""
        # Skip performance monitoring for certain paths
        skip_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/health/ready",
            "/health/live",
            "/health/metrics",
        }
        
        if request.url.path in skip_paths or request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log slow requests
            if duration >= VERY_SLOW_REQUEST_THRESHOLD:
                # Very slow - log as error
                log_performance_issue(
                    operation=f"{request.method} {request.url.path}",
                    duration_seconds=duration,
                    threshold_seconds=VERY_SLOW_REQUEST_THRESHOLD,
                    context={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "query_params": str(request.query_params) if request.query_params else None,
                    },
                )
                logger.error(
                    f"Very slow request: {request.method} {request.url.path} took {duration:.3f}s "
                    f"(status: {response.status_code})"
                )
            elif duration >= SLOW_REQUEST_THRESHOLD:
                # Slow - log as warning
                log_performance_issue(
                    operation=f"{request.method} {request.url.path}",
                    duration_seconds=duration,
                    threshold_seconds=SLOW_REQUEST_THRESHOLD,
                    context={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "query_params": str(request.query_params) if request.query_params else None,
                    },
                )
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {duration:.3f}s "
                    f"(status: {response.status_code})"
                )
            
            # Add performance header (optional, for debugging)
            if settings.NODE_ENV == "development":
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # If an exception occurs, still measure duration
            duration = time.time() - start_time
            
            # Log performance even for failed requests
            if duration >= SLOW_REQUEST_THRESHOLD:
                log_performance_issue(
                    operation=f"{request.method} {request.url.path} (failed)",
                    duration_seconds=duration,
                    threshold_seconds=SLOW_REQUEST_THRESHOLD,
                    context={
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                    },
                )
            
            # Re-raise the exception
            raise
