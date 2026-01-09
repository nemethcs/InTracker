"""Database base configuration."""
import os
import contextvars
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

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
def get_database_url():
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

# Create database engine
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
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
