"""MCP API Key controller."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.mcp_key_service import mcp_key_service
from src.api.schemas.mcp_key import (
    McpApiKeyCreate,
    McpApiKeyResponse,
    McpApiKeyCreateResponse,
    McpApiKeyListResponse,
)

router = APIRouter(prefix="/mcp-keys", tags=["mcp-keys"])


@router.post("", response_model=McpApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_key(
    key_data: McpApiKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new MCP API key for the current user.
    
    The plain_text_key is returned only once and should be shown to the user.
    It cannot be retrieved again after creation.
    """
    user_id = UUID(current_user["user_id"])
    
    api_key, plain_text_key = mcp_key_service.create_key(
        db=db,
        user_id=user_id,
        name=key_data.name,
        expires_in_days=key_data.expires_in_days,
    )

    return McpApiKeyCreateResponse(
        key=McpApiKeyResponse(
            id=api_key.id,
            user_id=api_key.user_id,
            name=api_key.name,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
        ),
        plain_text_key=plain_text_key,
    )


@router.get("", response_model=McpApiKeyListResponse)
async def list_mcp_keys(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all MCP API keys for the current user."""
    user_id = UUID(current_user["user_id"])
    
    keys = mcp_key_service.get_keys_by_user(
        db=db,
        user_id=user_id,
        include_inactive=include_inactive,
    )

    return McpApiKeyListResponse(
        keys=[
            McpApiKeyResponse(
                id=key.id,
                user_id=key.user_id,
                name=key.name,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                is_active=key.is_active,
                created_at=key.created_at,
                updated_at=key.updated_at,
            )
            for key in keys
        ],
        total=len(keys),
    )


@router.get("/{key_id}", response_model=McpApiKeyResponse)
async def get_mcp_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific MCP API key by ID."""
    user_id = UUID(current_user["user_id"])
    
    api_key = mcp_key_service.get_key_by_id(db=db, key_id=key_id, user_id=user_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP API key not found",
        )

    return McpApiKeyResponse(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
    )


@router.post("/{key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_mcp_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) an MCP API key."""
    user_id = UUID(current_user["user_id"])
    
    success = mcp_key_service.revoke_key(db=db, key_id=key_id, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP API key not found or not authorized",
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an MCP API key permanently."""
    user_id = UUID(current_user["user_id"])
    
    success = mcp_key_service.delete_key(db=db, key_id=key_id, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP API key not found or not authorized",
        )
