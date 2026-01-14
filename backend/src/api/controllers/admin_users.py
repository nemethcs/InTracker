"""Admin user management endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Header, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.database.base import get_db
from src.database.models import User, TeamMember, Team
from src.services.auth_service import AuthService
from src.services.team_service import TeamService
from src.api.middleware.auth import get_current_admin_user, get_optional_user
from src.config import settings

# Import shared router from admin_controller
from .admin_controller import router

security = HTTPBearer(auto_error=False)


@router.post("/create-user")
async def create_user(
    email: str,
    password: str,
    name: str = None,
    role: str = "member",
    team_id: str = None,
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """Create a user. Requires admin role or API key.
    
    Non-admin users (member, team_leader) must be assigned to a team.
    If team_id is not provided for non-admin users, a default team will be created.
    """
    # Check API key first (for MCP/admin scripts)
    if api_key and api_key == settings.MCP_API_KEY:
        # API key is valid, allow access
        pass
    else:
        # No valid API key, check for admin user via JWT
        current_user = await get_optional_user(credentials, db)
        if not current_user or current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key or admin access required",
            )
    
    # Validate role
    valid_roles = ["admin", "team_leader", "member"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {
                "message": f"User {email} already exists",
                "status": "exists",
                "user_id": str(existing_user.id),
            }
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()  # Flush to get user.id
        
        # For non-admin users, ensure they are in a team
        if role != "admin":
            if not team_id:
                # Create a default team for the user
                team_name = f"{name}'s Team" if name else f"{email.split('@')[0]}'s Team"
                # Ensure unique team name
                base_name = team_name
                counter = 1
                while db.query(Team).filter(Team.name == team_name).first():
                    team_name = f"{base_name} {counter}"
                    counter += 1
                
                team = TeamService.create_team(
                    db=db,
                    name=team_name,
                    created_by=user.id,
                    description=None,
                )
                team_id = str(team.id)
            else:
                # Verify team exists
                team = TeamService.get_team_by_id(db, UUID(team_id))
                if not team:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Team {team_id} not found",
                    )
            
            # Add user to team
            team_member = TeamMember(
                team_id=UUID(team_id),
                user_id=user.id,
                role="team_leader" if role == "team_leader" else "member",
            )
            db.add(team_member)
        
        db.commit()
        db.refresh(user)
        
        return {
            "message": "User created successfully",
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update a user's role. Requires admin role.
    
    Non-admin users (member, team_leader) must be members of at least one team.
    If changing from admin to non-admin and user has no team membership, an error is raised.
    """
    # Validate role
    valid_roles = ["admin", "team_leader", "member"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )

    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        old_role = user.role
        
        # If changing from admin to non-admin, ensure user has team membership
        if old_role == "admin" and role != "admin":
            has_membership = TeamService.has_team_membership(db, UUID(user_id))
            if not has_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change user from admin to non-admin role without team membership. Please add user to a team first.",
                )
        
        # If changing to non-admin, ensure user has team membership
        if role != "admin":
            has_membership = TeamService.has_team_membership(db, UUID(user_id))
            if not has_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Non-admin users must be members of at least one team. Please add user to a team first.",
                )
        
        user.role = role
        db.commit()
        db.refresh(user)

        return {
            "message": f"User role updated from {old_role} to {role}",
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )


@router.put("/users/by-email/{email}/role")
async def update_user_role_by_email(
    email: str,
    role: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update a user's role by email. Requires admin role."""
    # Validate role
    valid_roles = ["admin", "team_leader", "member"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )

    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found",
            )

        old_role = user.role
        user.role = role
        db.commit()
        db.refresh(user)

        return {
            "message": f"User role updated from {old_role} to {role}",
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )


@router.get("/users", status_code=status.HTTP_200_OK)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """List all users. Requires admin role."""
    query = db.query(User)

    # Filter by role
    if role:
        valid_roles = ["admin", "team_leader", "member"]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )
        query = query.filter(User.role == role)

    # Search by email or name
    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            User.name.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "users": [
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                "github_username": user.github_username,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat(),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            }
            for user in users
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get user by ID. Requires admin role."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "github_username": user.github_username,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.put("/users/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update user. Requires admin role."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        # Update fields
        if name is not None:
            user.name = name
        if email is not None:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == email, User.id != user.id).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email {email} already exists",
                )
            user.email = email
        if is_active is not None:
            user.is_active = is_active

        db.commit()
        db.refresh(user)

        return {
            "message": "User updated successfully",
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete user by ID. Requires admin role."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        # Prevent deleting yourself
        if str(user.id) == current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account",
            )

        # Delete related MCP API keys first to avoid constraint violations
        # The CASCADE should handle this, but we delete explicitly to avoid audit trail issues
        from src.database.models import McpApiKey
        mcp_keys = db.query(McpApiKey).filter(McpApiKey.user_id == user.id).all()
        for key in mcp_keys:
            db.delete(key)

        # Before deleting user, we need to handle related records that have NOT NULL created_by constraints
        # For teams, we can't set created_by to NULL, so we need to either:
        # 1. Delete teams created by this user (CASCADE will handle team_members), or
        # 2. Transfer ownership to another user
        # For now, we'll delete teams created by this user
        from src.database.models import Team, InvitationCode
        teams_created_by_user = db.query(Team).filter(Team.created_by == user.id).all()
        for team in teams_created_by_user:
            db.delete(team)
        
        # Also delete invitation codes created by this user (created_by is NOT NULL)
        invitation_codes_created_by_user = db.query(InvitationCode).filter(InvitationCode.created_by == user.id).all()
        for invitation_code in invitation_codes_created_by_user:
            db.delete(invitation_code)
        
        # Set used_by to NULL for invitation codes used by this user
        # (used_by is nullable, so we can set it to NULL instead of deleting)
        invitation_codes_used_by_user = db.query(InvitationCode).filter(InvitationCode.used_by == user.id).all()
        for invitation_code in invitation_codes_used_by_user:
            invitation_code.used_by = None

        user_email = user.email
        db.delete(user)
        db.commit()

        return {
            "message": f"User {user_email} deleted successfully",
            "status": "success",
            "deleted_user_id": user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )
