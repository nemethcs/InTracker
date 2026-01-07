"""Configuration management for MCP Server."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """MCP Server settings."""

    # Database
    DATABASE_URL: str = "postgresql://intracker:intracker_dev@localhost:5433/intracker"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # MCP
    MCP_API_KEY: Optional[str] = None
    MCP_HTTP_PORT: int = 3001
    MCP_HTTP_HOST: str = "0.0.0.0"
    
    # Backend API (for SignalR broadcast)
    # Will be determined dynamically based on environment
    BACKEND_API_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
