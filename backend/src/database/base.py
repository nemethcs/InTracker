"""Database base configuration."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
