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
    
    # GitHub OAuth
    GITHUB_OAUTH_CLIENT_ID: Optional[str] = None
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = None
    GITHUB_OAUTH_ENCRYPTION_KEY: Optional[str] = None  # Fernet key for token encryption (base64 encoded)

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
    
    # MCP Server API Key (for SignalR broadcast from MCP)
    MCP_API_KEY: str = "test"
    
    # Azure Communication Services Email
    AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING: Optional[str] = None
    AZURE_EMAIL_SENDER_ADDRESS: str = "DoNotReply@kesmarki.com"
    AZURE_EMAIL_SERVICE_NAME: str = "intracker-email-service"
    FRONTEND_URL: str = "https://intracker.kesmarki.com"
    BACKEND_URL: Optional[str] = None  # For OAuth callback URL (defaults to FRONTEND_URL if not set)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
