"""Admin controller for running migrations and creating users."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Header, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.database.base import get_db
from src.database.models import User, InvitationCode, TeamMember, Team
from src.services.auth_service import AuthService
from src.services.invitation_service import InvitationService
from src.services.team_service import TeamService
from src.api.middleware.auth import get_current_admin_user
from src.config import settings
from alembic import command
from alembic.config import Config
from pathlib import Path
import os

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/migrate")
async def run_migrations(
    api_key: str = Header(..., alias="X-API-Key"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Run database migrations. Requires admin role or API key."""
    # Check API key (for MCP/admin scripts) OR admin role
    if api_key != settings.MCP_API_KEY and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or admin access required",
        )
    
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DATABASE_URL not configured",
            )
        
        # Set up Alembic
        backend_dir = Path(__file__).resolve().parents[3]
        alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        return {
            "message": "Migrations completed successfully",
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}",
        )


@router.post("/create-user")
async def create_user(
    email: str,
    password: str,
    name: str = None,
    role: str = "member",
    team_id: str = None,
    api_key: str = Header(..., alias="X-API-Key"),
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a user. Requires admin role or API key.
    
    Non-admin users (member, team_leader) must be assigned to a team.
    If team_id is not provided for non-admin users, a default team will be created.
    """
    from src.services.team_service import TeamService
    from src.database.models import TeamMember
    from src.services.auth_service import AuthService as AuthServiceHelper
    
    # Check API key (for MCP/admin scripts) OR admin role
    if api_key != settings.MCP_API_KEY and current_user.get("role") != "admin":
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
        password_hash = AuthServiceHelper.hash_password(password)
        
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
                from src.database.models import Team
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
    from src.services.team_service import TeamService
    from src.database.models import TeamMember
    from src.database.models import Team
    
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


# Invitation Management Endpoints

@router.post("/invitations/admin", status_code=status.HTTP_201_CREATED)
async def create_admin_invitation(
    expires_in_days: Optional[int] = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create an admin invitation code. Requires admin role."""
    try:
        invitation = InvitationService.generate_admin_invitation(
            db=db,
            created_by=UUID(current_user["user_id"]),
            expires_in_days=expires_in_days,
        )
        return {
            "message": "Admin invitation code created successfully",
            "status": "success",
            "invitation": {
                "code": invitation.code,
                "type": invitation.type,
                "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
                "created_at": invitation.created_at.isoformat(),
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin invitation: {str(e)}",
        )


@router.get("/invitations", status_code=status.HTTP_200_OK)
async def list_invitations(
    type: Optional[str] = Query(None, description="Filter by type (admin, team)"),
    used: Optional[bool] = Query(None, description="Filter by used status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """List all invitations. Requires admin role."""
    invitations, total = InvitationService.get_all_invitations(
        db=db,
        type=type,
        used=used,
        skip=skip,
        limit=limit,
    )

    return {
        "invitations": [
            {
                "code": invitation.code,
                "type": invitation.type,
                "team_id": str(invitation.team_id) if invitation.team_id else None,
                "created_by": str(invitation.created_by),
                "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
                "used_at": invitation.used_at.isoformat() if invitation.used_at else None,
                "used_by": str(invitation.used_by) if invitation.used_by else None,
                "created_at": invitation.created_at.isoformat(),
            }
            for invitation in invitations
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/invitations/{code}", status_code=status.HTTP_200_OK)
async def get_invitation(
    code: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get invitation by code. Requires admin role."""
    invitation = InvitationService.get_invitation_by_code(db=db, code=code)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation code {code} not found",
        )

    return {
        "code": invitation.code,
        "type": invitation.type,
        "team_id": str(invitation.team_id) if invitation.team_id else None,
        "created_by": str(invitation.created_by),
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
        "used_at": invitation.used_at.isoformat() if invitation.used_at else None,
        "used_by": str(invitation.used_by) if invitation.used_by else None,
        "created_at": invitation.created_at.isoformat(),
    }


@router.delete("/invitations/{code}", status_code=status.HTTP_200_OK)
async def delete_invitation(
    code: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an invitation code. Requires admin role."""
    try:
        success = InvitationService.delete_invitation(db=db, code=code)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invitation code {code} not found",
            )

        return {
            "message": f"Invitation code {code} deleted successfully",
            "status": "success",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete invitation: {str(e)}",
        )
