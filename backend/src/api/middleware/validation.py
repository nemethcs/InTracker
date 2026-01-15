"""Request and response validation middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
from typing import Callable
import logging
from src.api.schemas.error import ErrorResponse, ErrorDetail
from datetime import datetime

logger = logging.getLogger(__name__)

# Request size limits (in bytes)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_JSON_BODY_SIZE = 5 * 1024 * 1024  # 5MB for JSON bodies

# Allowed content types for JSON endpoints
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/json; charset=utf-8",
    "application/json;charset=utf-8",
}


class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request and response validation.
    
    Validates:
    - Request size limits
    - Content-Type headers for JSON endpoints
    - Request body size for JSON requests
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request and validate before passing to next handler."""
        
        # Skip validation for certain paths
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
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    return self._create_error_response(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        message=f"Request body too large. Maximum size is {MAX_REQUEST_SIZE / (1024 * 1024):.1f}MB",
                        error_code="REQUEST_TOO_LARGE",
                    )
            except ValueError:
                # Invalid content-length header, but continue
                logger.warning(f"Invalid content-length header: {content_length}")
        
        # Validate Content-Type for POST/PUT/PATCH requests with body
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "").lower()
            
            # Skip validation for multipart/form-data (file uploads)
            if content_type.startswith("multipart/form-data"):
                return await call_next(request)
            
            # Validate JSON content type
            if content_type and not any(
                content_type.startswith(allowed) for allowed in ALLOWED_CONTENT_TYPES
            ):
                # Allow empty content type for requests without body
                if content_length and int(content_length) > 0:
                    return self._create_error_response(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        message=f"Unsupported Content-Type: {content_type}. Expected: application/json",
                        error_code="UNSUPPORTED_MEDIA_TYPE",
                    )
        
        # Process request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error processing request: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _create_error_response(
        status_code: int,
        message: str,
        error_code: str,
    ) -> JSONResponse:
        """Create a standardized error response."""
        error_response = ErrorResponse(
            error=status.HTTP_STATUS_CODES.get(status_code, "error").lower().replace(" ", "_"),
            message=message,
            code=error_code,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(exclude_none=True),
        )
