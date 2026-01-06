"""Authentication controller."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models import User
from src.services.auth_service import auth_service
from src.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
)
from src.api.middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user."""
    try:
        user = auth_service.register(db, request.email, request.password, request.name)
        token_data = {"sub": str(user.id), "email": user.email}
        tokens = {
            "access_token": auth_service.create_access_token(token_data),
            "refresh_token": auth_service.create_refresh_token(token_data),
        }

        return AuthResponse(
            message="User registered successfully",
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                github_username=user.github_username,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
            ),
            tokens=TokenResponse(**tokens),
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user."""
    try:
        user, tokens = auth_service.login(db, request.email, request.password)

        return AuthResponse(
            message="Login successful",
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                github_username=user.github_username,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
            ),
            tokens=TokenResponse(**tokens),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token."""
    try:
        tokens = auth_service.refresh_access_token(db, request.refresh_token)
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user info."""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        github_username=user.github_username,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
    )
