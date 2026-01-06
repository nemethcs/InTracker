"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with validation."""

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str = "dev-secret-key-min-32-chars-long-for-testing"
    JWT_REFRESH_SECRET: str = "dev-refresh-secret-min-32-chars-long-for-testing"
    JWT_EXPIRES_IN: str = "15m"
    JWT_REFRESH_EXPIRES_IN: str = "7d"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Server
    PORT: int = 3000
    NODE_ENV: str = "development"

    # CORS
    CORS_ORIGIN: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
