"""Database base configuration with optimized connection pooling.

This module provides:
- Optimized connection pooling for production and development
- Connection health checks (pool_pre_ping)
- Automatic connection recycling
- Environment-based pool sizing
"""
import os
import contextvars
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Context variable to store current user ID for audit trail
# This is set by services/controllers before database operations
current_user_id: contextvars.ContextVar = contextvars.ContextVar('current_user_id', default=None)


def set_current_user_id(user_id) -> contextvars.Token:
    """Set current user ID for audit trail.
    
    Args:
        user_id: UUID of the current user
    
    Returns:
        Token that can be used to reset the context variable.
    
    Usage:
        token = set_current_user_id(user_id)
        try:
            # ... database operations ...
        finally:
            reset_current_user_id(token)
    """
    return current_user_id.set(user_id)


def reset_current_user_id(token: contextvars.Token) -> None:
    """Reset current user ID context variable."""
    current_user_id.reset(token)

# Get database URL from environment or config
def get_database_url() -> str:
    """Get database URL from environment or config."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    try:
        from src.config import settings
        return settings.DATABASE_URL
    except Exception:
        # Fallback for Alembic when config is not available
        return os.getenv("DATABASE_URL", "postgresql://intracker:intracker_dev@localhost:5433/intracker")


def get_pool_config() -> dict:
    """Get connection pool configuration based on environment.
    
    Returns:
        Dictionary with pool configuration parameters
    """
    try:
        from src.config import settings
        is_production = settings.is_production()
    except Exception:
        is_production = os.getenv("NODE_ENV") == "production"
    
    if is_production:
        # Production: larger pool for higher concurrency
        return {
            "pool_size": 20,  # Base pool size
            "max_overflow": 10,  # Additional connections beyond pool_size
            "pool_timeout": 30,  # Seconds to wait for connection from pool
            "pool_recycle": 3600,  # Recycle connections after 1 hour (PostgreSQL default idle timeout is ~10 min)
            "pool_pre_ping": True,  # Verify connections before using
            "echo": False,  # Disable SQL logging in production
        }
    else:
        # Development: smaller pool, more verbose
        return {
            "pool_size": 5,  # Smaller pool for development
            "max_overflow": 10,  # Additional connections
            "pool_timeout": 30,  # Seconds to wait for connection
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Verify connections before using
            "echo": False,  # Can be set to True for SQL debugging
        }


# Create database engine with optimized pooling
pool_config = get_pool_config()
database_url = get_database_url()

engine = create_engine(
    database_url,
    poolclass=QueuePool,  # Explicitly use QueuePool (default, but explicit is better)
    **pool_config,
    # PostgreSQL-specific connection arguments
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "application_name": "intracker_backend",  # Identify connections in PostgreSQL
        "options": "-c statement_timeout=30000",  # 30 second statement timeout (in milliseconds)
    },
)

logger.info(
    f"Database engine created with pool_size={pool_config['pool_size']}, "
    f"max_overflow={pool_config['max_overflow']}, "
    f"pool_recycle={pool_config['pool_recycle']}s"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# SQLAlchemy event listeners for audit trail
@event.listens_for(Session, "before_flush")
def set_audit_fields(session, flush_context, instances):
    """Automatically set created_by and updated_by fields for audit trail."""
    user_id = current_user_id.get()
    if not user_id:
        return  # No user context, skip audit trail
    
    # Get all new and modified instances
    for instance in session.new:
        # Set created_by if not already set and model has the field
        if hasattr(instance, 'created_by') and instance.created_by is None:
            instance.created_by = user_id
        # Set updated_by on create (first update)
        if hasattr(instance, 'updated_by'):
            instance.updated_by = user_id
    
    for instance in session.dirty:
        # Set updated_by on update if model has the field
        if hasattr(instance, 'updated_by'):
            instance.updated_by = user_id
