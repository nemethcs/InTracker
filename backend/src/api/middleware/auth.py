"""Authentication middleware."""
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models import User
from src.services.auth_service import auth_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Get current authenticated user from JWT token with role."""
    token = credentials.credentials

    try:
        payload = auth_service.verify_token(token, is_refresh=False)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Get user from database to get role
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": user.role,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """Get optional authenticated user (doesn't fail if no token)."""
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token, is_refresh=False)
        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Get user from database to get role
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": user.role,
        }
    except (ValueError, Exception):
        return None


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current user and verify admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_team_leader(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current user and verify team leader or admin role."""
    role = current_user.get("role")
    if role not in ["admin", "team_leader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team leader or admin access required",
        )
    return current_user
