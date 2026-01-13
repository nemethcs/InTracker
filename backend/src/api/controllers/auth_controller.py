"""Authentication controller."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime
from src.database.base import get_db
from src.database.models import User
from src.services.auth_service import auth_service
from src.services.github_oauth_service import github_oauth_service
from src.services.cache_service import get_redis_client
from src.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
)
from src.api.middleware.auth import get_current_user, get_optional_user
from src.services.github_token_service import github_token_service
from src.services.onboarding_service import update_setup_completed

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user with invitation code."""
    try:
        user = auth_service.register(
            db,
            request.email,
            request.password,
            request.invitation_code,
            request.name,
        )
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
                github_connected_at=user.github_connected_at.isoformat() if user.github_connected_at else None,
                github_token_expires_at=user.github_token_expires_at.isoformat() if user.github_token_expires_at else None,
                onboarding_step=user.onboarding_step,
                mcp_verified_at=user.mcp_verified_at.isoformat() if user.mcp_verified_at else None,
                setup_completed=user.setup_completed,
                is_active=user.is_active,
                role=user.role,
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
                github_connected_at=user.github_connected_at.isoformat() if user.github_connected_at else None,
                github_token_expires_at=user.github_token_expires_at.isoformat() if user.github_token_expires_at else None,
                onboarding_step=user.onboarding_step,
                mcp_verified_at=user.mcp_verified_at.isoformat() if user.mcp_verified_at else None,
                setup_completed=user.setup_completed,
                is_active=user.is_active,
                role=user.role,
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

    # Update setup_completed status (always check on /auth/me call)
    update_setup_completed(db, UUID(current_user["user_id"]))
    
    # Re-query user to get updated setup_completed and onboarding_step
    # This ensures we get the latest values from the database
    # Use merge=False to get a fresh instance from the database
    user_id = UUID(current_user["user_id"])
    user = db.query(User).filter(User.id == user_id).first()
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
        github_connected_at=user.github_connected_at.isoformat() if user.github_connected_at else None,
        github_token_expires_at=user.github_token_expires_at.isoformat() if user.github_token_expires_at else None,
        onboarding_step=user.onboarding_step,
        mcp_verified_at=user.mcp_verified_at.isoformat() if user.mcp_verified_at else None,
        setup_completed=user.setup_completed,
        is_active=user.is_active,
        role=user.role,
    )


@router.get("/github/authorize")
async def github_authorize(
    current_user: dict = Depends(get_current_user),
    state: Optional[str] = Query(None),
):
    """Generate GitHub OAuth authorization URL with PKCE.
    
    Returns authorization URL and stores code_verifier in Redis with state as key.
    Also stores user_id in Redis for callback authentication.
    """
    try:
        user_id = UUID(current_user["user_id"])
        
        # Generate authorization URL with PKCE
        authorization_url, code_verifier = github_oauth_service.generate_authorization_url(state=state)
        
        # Store code_verifier in Redis with state as key (expires in 10 minutes)
        # Use the state from the generated URL (it might have been generated)
        # Extract state from URL
        import urllib.parse
        parsed = urllib.parse.urlparse(authorization_url)
        params = urllib.parse.parse_qs(parsed.query)
        state_value = params.get('state', [state])[0] if state else params.get('state', [])[0]
        
        if not state_value:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate state parameter",
            )
        
        # Store in Redis (state is used as-is, no URL encoding needed for Redis key)
        cache_key = f"github_oauth:state:{state_value}"
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex(cache_key, 600, code_verifier)  # 10 minutes TTL
            # Also store user_id for callback authentication
            redis_client.setex(f"github_oauth:user:{state_value}", 600, str(user_id))  # 10 minutes TTL
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Redis is not available",
            )
        
        return {
            "authorization_url": authorization_url,
            "state": state_value,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Handle GitHub OAuth callback and store tokens.
    
    Exchanges authorization code for tokens, stores encrypted tokens in User model,
    and updates user's GitHub username and avatar.
    
    Note: User can be authenticated via token (current_user) or via state parameter
    stored in Redis during authorization flow.
    """
    try:
        # Try to get user_id from authenticated user first
        user_id = None
        if current_user:
            user_id = UUID(current_user["user_id"])
        else:
            # If no authenticated user, try to get user_id from state in Redis
            # The state should have been stored with user_id during authorization
            redis_client = get_redis_client()
            if redis_client:
                # Try to get user_id from state (if we stored it)
                user_id_data = redis_client.get(f"github_oauth:user:{state}")
                if user_id_data:
                    # Handle both bytes and string (depending on Redis client version)
                    if isinstance(user_id_data, bytes):
                        user_id = UUID(user_id_data.decode('utf-8'))
                    else:
                        user_id = UUID(user_id_data)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated. Please ensure you are logged in.",
            )
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Retrieve code_verifier from Redis
        # State parameter comes from URL, might be URL-encoded by GitHub
        # Try both the original state and URL-decoded version
        import urllib.parse
        decoded_state = urllib.parse.unquote(state)
        
        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Redis is not available",
            )
        
        code_verifier = None
        # Try original state first
        cache_key = f"github_oauth:state:{state}"
        code_verifier_raw = redis_client.get(cache_key)
        
        # If not found, try URL-decoded state
        if not code_verifier_raw and decoded_state != state:
            cache_key_decoded = f"github_oauth:state:{decoded_state}"
            code_verifier_raw = redis_client.get(cache_key_decoded)
            if code_verifier_raw:
                cache_key = cache_key_decoded
        
        # Delete state from cache (one-time use)
        if code_verifier_raw:
            redis_client.delete(cache_key)
            # Handle both bytes and string (depending on Redis client version)
            if isinstance(code_verifier_raw, bytes):
                code_verifier = code_verifier_raw.decode('utf-8')
            else:
                code_verifier = code_verifier_raw
        
        if not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or expired state parameter. State: {state[:20]}...",
            )
        
        # Exchange code for tokens
        token_data = await github_oauth_service.exchange_code_for_tokens(
            code=code,
            code_verifier=code_verifier,
            state=state,
        )
        
        # Encrypt tokens
        encrypted_access_token = github_oauth_service.encrypt_token(token_data["access_token"])
        encrypted_refresh_token = None
        if token_data.get("refresh_token"):
            encrypted_refresh_token = github_oauth_service.encrypt_token(token_data["refresh_token"])
        
        # Update user with encrypted tokens and GitHub info
        user.github_access_token_encrypted = encrypted_access_token
        user.github_refresh_token_encrypted = encrypted_refresh_token
        user.github_token_expires_at = token_data["expires_at"]
        user.github_refresh_token_expires_at = token_data.get("refresh_expires_at")
        user.github_connected_at = datetime.utcnow()
        
        # Update GitHub username and avatar from user_info
        user_info = token_data.get("user_info", {})
        if user_info:
            user.github_username = user_info.get("login")
            user.avatar_url = user_info.get("avatar_url")
        
        # Update onboarding_step to 4 (github_connected) if not already higher
        if user.onboarding_step < 4:
            user.onboarding_step = 4
        
        db.commit()
        db.refresh(user)
        
        # Update setup_completed status
        update_setup_completed(db, user_id)
        
        return {
            "message": "GitHub OAuth connection successful",
            "github_username": user.github_username,
            "avatar_url": user.avatar_url,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process OAuth callback: {str(e)}",
        )


@router.post("/github/disconnect")
async def github_disconnect(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect GitHub account by clearing tokens."""
    try:
        user_id = UUID(current_user["user_id"])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Disconnect GitHub by clearing all token-related fields
        github_token_service.disconnect_github(db, user_id)
        
        return {"message": "GitHub account disconnected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect GitHub account: {str(e)}",
        )
