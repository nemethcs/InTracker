"""MCP API Key schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class McpApiKeyCreate(BaseModel):
    """Schema for creating an MCP API key."""
    name: Optional[str] = Field(None, max_length=255, description="Optional name/description for the key")
    expires_in_days: Optional[int] = Field(None, ge=1, description="Optional expiration in days from now")


class McpApiKeyResponse(BaseModel):
    """Schema for MCP API key response."""
    id: UUID
    user_id: UUID
    name: Optional[str] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class McpApiKeyCreateResponse(BaseModel):
    """Schema for MCP API key creation response (includes plain text key)."""
    key: McpApiKeyResponse
    plain_text_key: str = Field(..., description="The API key in plain text. Show this once and never store it!")


class McpApiKeyListResponse(BaseModel):
    """Schema for MCP API key list response with pagination."""
    keys: list[McpApiKeyResponse]
    total: int
    page: Optional[int] = Field(None, description="Current page number (1-indexed)")
    page_size: Optional[int] = Field(None, description="Number of items per page")