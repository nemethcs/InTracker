"""Comprehensive error logging and monitoring utilities."""
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request
from src.config import settings

logger = logging.getLogger(__name__)


def log_error(
    error: Exception,
    request: Optional[Request] = None,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR,
) -> None:
    """Log an error with comprehensive context information.
    
    Args:
        error: The exception that occurred
        request: Optional FastAPI request object for context
        context: Optional additional context dictionary
        level: Logging level (default: ERROR)
    """
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    # Add request context if available
    if request:
        error_info["request"] = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Add user context if available
        if hasattr(request.state, "user_id"):
            error_info["request"]["user_id"] = str(request.state.user_id)
    
    # Add additional context
    if context:
        error_info["context"] = context
    
    # Add stack trace for errors
    if level >= logging.ERROR:
        error_info["traceback"] = traceback.format_exc()
    
    # Log with appropriate level
    log_message = f"Error: {error_info['error_type']} - {error_info['error_message']}"
    
    if level == logging.CRITICAL:
        logger.critical(log_message, extra={"error_info": error_info}, exc_info=True)
    elif level == logging.ERROR:
        logger.error(log_message, extra={"error_info": error_info}, exc_info=True)
    elif level == logging.WARNING:
        logger.warning(log_message, extra={"error_info": error_info})
    else:
        logger.info(log_message, extra={"error_info": error_info})


def log_http_error(
    status_code: int,
    message: str,
    request: Optional[Request] = None,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an HTTP error with context.
    
    Args:
        status_code: HTTP status code
        message: Error message
        request: Optional FastAPI request object
        error_code: Optional error code
        details: Optional error details
    """
    # Determine log level based on status code
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO
    
    error_info = {
        "status_code": status_code,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if request:
        error_info["request"] = {
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
        }
    
    if details:
        error_info["details"] = details
    
    log_message = f"HTTP {status_code}: {message}"
    
    if level == logging.ERROR:
        logger.error(log_message, extra={"error_info": error_info})
    elif level == logging.WARNING:
        logger.warning(log_message, extra={"error_info": error_info})
    else:
        logger.info(log_message, extra={"error_info": error_info})


def log_database_error(
    error: Exception,
    operation: str,
    table: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a database-related error.
    
    Args:
        error: The database exception
        operation: Database operation (e.g., "SELECT", "INSERT", "UPDATE")
        table: Optional table name
        context: Optional additional context
    """
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "operation": operation,
        "table": table,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if context:
        error_info["context"] = context
    
    log_message = f"Database error in {operation}" + (f" on {table}" if table else "")
    logger.error(log_message, extra={"error_info": error_info}, exc_info=True)


def log_external_api_error(
    service: str,
    error: Exception,
    endpoint: Optional[str] = None,
    status_code: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an error from an external API call.
    
    Args:
        service: Service name (e.g., "GitHub", "Azure")
        error: The exception that occurred
        endpoint: Optional API endpoint
        status_code: Optional HTTP status code
        context: Optional additional context
    """
    error_info = {
        "service": service,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "endpoint": endpoint,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if context:
        error_info["context"] = context
    
    log_message = f"External API error ({service})" + (f" at {endpoint}" if endpoint else "")
    logger.error(log_message, extra={"error_info": error_info}, exc_info=True)


def log_performance_issue(
    operation: str,
    duration_seconds: float,
    threshold_seconds: float = 1.0,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a performance issue when an operation takes too long.
    
    Args:
        operation: Operation name
        duration_seconds: How long the operation took
        threshold_seconds: Threshold for warning (default: 1.0s)
        context: Optional additional context
    """
    if duration_seconds < threshold_seconds:
        return  # Don't log if under threshold
    
    error_info = {
        "operation": operation,
        "duration_seconds": duration_seconds,
        "threshold_seconds": threshold_seconds,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if context:
        error_info["context"] = context
    
    log_message = f"Performance issue: {operation} took {duration_seconds:.2f}s (threshold: {threshold_seconds}s)"
    logger.warning(log_message, extra={"error_info": error_info})
