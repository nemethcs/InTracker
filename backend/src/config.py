"""Configuration management using Pydantic Settings.

This module provides centralized configuration management with:
- Environment-based settings loading
- Validation and type checking
- Helper methods for common checks
- Organized settings by category
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, Literal
import os


class Settings(BaseSettings):
    """Application settings with validation and helper methods.
    
    Settings are loaded from environment variables or .env file.
    All settings are validated on initialization.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )

    # ==================== Database ====================
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL database connection URL",
    )

    # ==================== JWT Authentication ====================
    JWT_SECRET: str = Field(
        default="dev-secret-key-min-32-chars-long-for-testing",
        min_length=32,
        description="Secret key for JWT token signing (min 32 chars)",
    )
    JWT_REFRESH_SECRET: str = Field(
        default="dev-refresh-secret-min-32-chars-long-for-testing",
        min_length=32,
        description="Secret key for JWT refresh token signing (min 32 chars)",
    )
    JWT_EXPIRES_IN: str = Field(
        default="15m",
        description="JWT token expiration time (e.g., '15m', '1h', '7d')",
    )
    JWT_REFRESH_EXPIRES_IN: str = Field(
        default="7d",
        description="JWT refresh token expiration time (e.g., '15m', '1h', '7d')",
    )

    # ==================== GitHub ====================
    GITHUB_TOKEN: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (fallback if user OAuth not available)",
    )
    
    # GitHub OAuth
    GITHUB_OAUTH_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="GitHub OAuth App client ID",
    )
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="GitHub OAuth App client secret",
    )
    GITHUB_OAUTH_ENCRYPTION_KEY: Optional[str] = Field(
        default=None,
        description="Fernet key for token encryption (base64 encoded)",
    )

    # ==================== Redis ====================
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL (overrides REDIS_HOST, REDIS_PORT, REDIS_DB if set)",
    )
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis host address",
    )
    REDIS_PORT: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis port number",
    )
    REDIS_DB: int = Field(
        default=0,
        ge=0,
        description="Redis database number",
    )

    # ==================== Server ====================
    PORT: int = Field(
        default=3000,
        ge=1,
        le=65535,
        description="Server port number",
    )
    NODE_ENV: Literal["development", "production", "test"] = Field(
        default="development",
        description="Application environment",
    )

    # ==================== CORS ====================
    CORS_ORIGIN: str = Field(
        default="*",
        description="CORS allowed origins (use '*' for all origins, or comma-separated list)",
    )
    
    # ==================== MCP Server ====================
    MCP_API_KEY: str = Field(
        default="test",
        description="MCP Server API Key (for SignalR broadcast from MCP)",
    )
    
    # ==================== Azure Communication Services Email ====================
    AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING: Optional[str] = Field(
        default=None,
        description="Azure Communication Services connection string",
    )
    AZURE_EMAIL_SENDER_ADDRESS: str = Field(
        default="DoNotReply@kesmarki.com",
        description="Email sender address",
    )
    AZURE_EMAIL_SERVICE_NAME: str = Field(
        default="intracker-email-service",
        description="Azure email service name",
    )
    
    # ==================== URLs ====================
    FRONTEND_URL: str = Field(
        default="https://intracker.kesmarki.com",
        description="Frontend application URL",
    )
    BACKEND_URL: Optional[str] = Field(
        default=None,
        description="Backend application URL (defaults to FRONTEND_URL if not set)",
    )

    # ==================== Validators ====================
    @field_validator("JWT_SECRET", "JWT_REFRESH_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Validate JWT secret length."""
        if len(v) < 32:
            raise ValueError(f"{info.field_name} must be at least 32 characters long")
        return v
    
    @field_validator("NODE_ENV")
    @classmethod
    def validate_node_env(cls, v: str) -> str:
        """Validate NODE_ENV value."""
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"NODE_ENV must be one of {allowed}")
        return v

    # ==================== Helper Methods ====================
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.NODE_ENV == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.NODE_ENV == "development"
    
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.NODE_ENV == "test"
    
    def get_backend_url(self) -> str:
        """Get backend URL, falling back to FRONTEND_URL if not set."""
        return self.BACKEND_URL or self.FRONTEND_URL
    
    def get_redis_url(self) -> Optional[str]:
        """Get Redis connection URL, constructing from components if REDIS_URL not set."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def is_github_oauth_configured(self) -> bool:
        """Check if GitHub OAuth is properly configured."""
        return bool(
            self.GITHUB_OAUTH_CLIENT_ID and
            self.GITHUB_OAUTH_CLIENT_SECRET and
            self.GITHUB_OAUTH_ENCRYPTION_KEY
        )
    
    def is_email_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING)


# Global settings instance
# This is initialized once when the module is imported
settings = Settings()
