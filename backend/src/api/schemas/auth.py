"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    """Register request schema."""
    email: EmailStr
    password: str
    name: Optional[str] = None
    invitation_code: str  # Required invitation code

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "name": "John Doe",
                "invitation_code": "abc123xyz...",
            }
        }


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    name: Optional[str]
    github_username: Optional[str]
    avatar_url: Optional[str]
    github_connected_at: Optional[str] = None
    github_token_expires_at: Optional[str] = None  # Token expiration timestamp
    onboarding_step: int = 0  # 0=not_started, 1=welcome, 2=mcp_key, 3=mcp_verified, 4=github, 5=complete
    mcp_verified_at: Optional[str] = None  # Timestamp when MCP was verified
    setup_completed: bool = False  # True when both MCP key exists AND GitHub connected
    is_active: bool
    role: Optional[str] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Auth response with user and tokens."""
    message: str
    user: UserResponse
    tokens: TokenResponse
