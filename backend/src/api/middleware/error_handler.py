"""Error handling middleware and utilities for standardized error responses."""
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from src.api.schemas.error import ErrorResponse, ErrorDetail
from src.config import settings


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[list[ErrorDetail]] = None,
    error_code: Optional[str] = None,
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        error_type: Error category (e.g., "validation_error", "not_found", "unauthorized")
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional list of detailed error information
        error_code: Optional error code for programmatic handling
    
    Returns:
        JSONResponse with standardized error format
    """
    error_response = ErrorResponse(
        error=error_type,
        message=message,
        details=details,
        code=error_code,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
    )


def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException with standardized error format."""
    # Map HTTP status codes to error types
    error_type_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_server_error",
        503: "service_unavailable",
    }
    
    error_type = error_type_map.get(exc.status_code, "error")
    
    # Extract error code from detail if it's a dict
    error_code = None
    message = str(exc.detail)
    
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))
        error_code = exc.detail.get("code")
    
    return create_error_response(
        error_type=error_type,
        message=message,
        status_code=exc.status_code,
        error_code=error_code,
    )


def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with standardized format."""
    details = []
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        details.append(
            ErrorDetail(
                field=field_path,
                message=error["msg"],
                code=error.get("type", "VALIDATION_ERROR").upper(),
            )
        )
    
    return create_error_response(
        error_type="validation_error",
        message="Invalid input data",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        error_code="VALIDATION_ERROR",
    )


def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions with standardized format."""
    import logging
    
    # Log the error for debugging
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal error details in production
    message = (
        str(exc) if settings.NODE_ENV == "development" 
        else "An internal server error occurred"
    )
    
    return create_error_response(
        error_type="internal_server_error",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
    )


# Helper function to raise standardized HTTP exceptions
def raise_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[list[ErrorDetail]] = None,
) -> None:
    """Raise an HTTPException with standardized format.
    
    This is a convenience function for controllers to raise errors
    that will be automatically formatted by the error handler.
    """
    detail = {"message": message}
    if error_code:
        detail["code"] = error_code
    if details:
        detail["details"] = [d.model_dump() for d in details]
    
    raise HTTPException(status_code=status_code, detail=detail)
