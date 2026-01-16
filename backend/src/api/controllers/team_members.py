"""Team members endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.services.team_service import TeamService
from src.api.middleware.auth import get_current_user, get_current_team_leader
from src.api.schemas.team import (
    TeamMemberResponse,
    TeamMemberListResponse,
)

# Import shared router from team_controller
# Note: Import at end to avoid circular import
from .team_controller import router  # noqa: E402


@router.get("/{team_id}/members", response_model=TeamMemberListResponse)
async def get_team_members(
    team_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all members of a team with pagination. User must be a member or admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")

    # Check if user is admin or team member
    if user_role != "admin" and not TeamService.is_team_member(db, team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    skip = (page - 1) * page_size
    members_with_users, total = TeamService.get_team_members_with_users(
        db, team_id, skip=skip, limit=page_size
    )
    
    # Convert UUIDs to strings for response and include user information
    members = [
        TeamMemberResponse(
            id=str(member.id),
            team_id=str(member.team_id),
            user_id=str(member.user_id),
            role=member.role,
            joined_at=member.joined_at,
            user_name=user.name,
            user_email=user.email,
        )
        for member, user in members_with_users
    ]
    
    return TeamMemberListResponse(
        members=members,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    team_id: UUID,
    user_id: UUID,
    role: str = "member",
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Add a member to a team. Only team leaders or admins can add members."""
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can add members",
        )

    try:
        team_member = TeamService.add_member(db, team_id, user_id, role)
        # Convert UUIDs to strings for response
        return {
            "id": str(team_member.id),
            "team_id": str(team_member.team_id),
            "user_id": str(team_member.user_id),
            "role": team_member.role,
            "joined_at": team_member.joined_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    team_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Remove a member from a team. Only team leaders or admins can remove members."""
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can remove members",
        )

    try:
        # Check if current user is admin - if so, pass removed_by_admin=True
        removed_by_admin = user_role == "admin"
        success = TeamService.remove_member(db, team_id, user_id, removed_by_admin=removed_by_admin)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{team_id}/members/{user_id}/role", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    role: str,
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Update a team member's role. Only team leaders or admins can update roles."""
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can update member roles",
        )

    try:
        team_member = TeamService.update_member_role(db, team_id, user_id, role)
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found",
            )
        # Convert UUIDs to strings for response
        return {
            "id": str(team_member.id),
            "team_id": str(team_member.team_id),
            "user_id": str(team_member.user_id),
            "role": team_member.role,
            "joined_at": team_member.joined_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
