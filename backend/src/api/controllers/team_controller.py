"""Team controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models import Team, TeamMember, User, User
from src.services.team_service import TeamService
from src.services.invitation_service import InvitationService
from src.api.middleware.auth import get_current_user, get_current_team_leader, get_current_admin_user
from src.api.schemas.team import (
    TeamCreateRequest,
    TeamUpdateRequest,
    TeamResponse,
    TeamMemberResponse,
    TeamListResponse,
    TeamInvitationResponse,
    TeamLanguageRequest,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    request: TeamCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new team. Only admins can create teams."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create teams",
        )

    try:
        team = TeamService.create_team(
            db=db,
            name=request.name,
            created_by=UUID(current_user["user_id"]),
            description=request.description,
        )
        # Convert UUIDs to strings for response
        return {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "language": team.language,
            "created_by": str(team.created_by),
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List teams. Returns user's teams or all teams if admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")

    # Admins can see all teams, others only their teams
    if user_role == "admin":
        teams, total = TeamService.list_teams(db, user_id=None, skip=skip, limit=limit)
    else:
        teams, total = TeamService.list_teams(db, user_id=user_id, skip=skip, limit=limit)

    # Convert UUIDs to strings for response
    teams_data = [
        {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "language": team.language,
            "created_by": str(team.created_by),
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        }
        for team in teams
    ]
    return TeamListResponse(teams=teams_data, total=total)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get team by ID. User must be a member or admin."""
    team = TeamService.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")

    # Check if user is admin or team member
    if user_role != "admin" and not TeamService.is_team_member(db, team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    # Convert UUIDs to strings for response
    return {
        "id": str(team.id),
        "name": team.name,
        "description": team.description,
        "language": team.language,
        "created_by": str(team.created_by),
        "created_at": team.created_at,
        "updated_at": team.updated_at,
    }


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    request: TeamUpdateRequest,
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Update team. Only team leaders or admins can update."""
    team = TeamService.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can update teams",
        )

    try:
        updated_team = TeamService.update_team(
            db=db,
            team_id=team_id,
            name=request.name,
            description=request.description,
        )
        if not updated_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        # Convert UUIDs to strings for response
        return {
            "id": str(updated_team.id),
            "name": updated_team.name,
            "description": updated_team.description,
            "language": updated_team.language,
            "created_by": str(updated_team.created_by),
            "created_at": updated_team.created_at,
            "updated_at": updated_team.updated_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete team. Only admins can delete teams."""
    success = TeamService.delete_team(db, team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def get_team_members(
    team_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all members of a team. User must be a member or admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")

    # Check if user is admin or team member
    if user_role != "admin" and not TeamService.is_team_member(db, team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    members_with_users = TeamService.get_team_members_with_users(db, team_id)
    # Convert UUIDs to strings for response and include user information
    return [
        {
            "id": str(member.id),
            "team_id": str(member.team_id),
            "user_id": str(member.user_id),
            "role": member.role,
            "joined_at": member.joined_at,
            "user_name": user.name,
            "user_email": user.email,
        }
        for member, user in members_with_users
    ]


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


@router.post("/{team_id}/language", response_model=TeamResponse, status_code=status.HTTP_200_OK)
async def set_team_language(
    team_id: UUID,
    request: TeamLanguageRequest,
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Set team language. Only team leaders can set language, and it can only be set once."""
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can set team language",
        )

    try:
        team = TeamService.set_team_language(
            db=db,
            team_id=team_id,
            language=request.language,
        )
        # Convert UUIDs to strings for response
        return {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "language": team.language,
            "created_by": str(team.created_by),
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{team_id}/invitations", response_model=TeamInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_team_invitation(
    team_id: UUID,
    expires_in_days: Optional[int] = Query(7, ge=1, le=365),
    send_email_to: Optional[str] = Query(None, description="Email address to send invitation to"),
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Create a team invitation code. Only team leaders can create invitations.
    
    Args:
        team_id: Team ID
        expires_in_days: Number of days until invitation expires (default: 7)
        send_email_to: Optional email address to send invitation to
    """
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can create team invitations",
        )

    try:
        # Get team and inviter info
        team = TeamService.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        
        inviter = db.query(User).filter(User.id == current_user_id).first()
        inviter_name = inviter.name if inviter else None

        invitation = InvitationService.generate_team_invitation(
            db=db,
            team_id=team_id,
            created_by=current_user_id,
            expires_in_days=expires_in_days,
        )
        
        # Send email if email address provided
        if send_email_to:
            from src.services.email_service import email_service
            email_sent = email_service.send_invitation_email(
                to_email=send_email_to,
                invitation_code=invitation.code,
                team_name=team.name,
                inviter_name=inviter_name,
                expires_in_days=expires_in_days,
            )
            if not email_sent:
                # Log warning but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send invitation email to {send_email_to}, but invitation was created")
        
        return TeamInvitationResponse(
            code=invitation.code,
            type=invitation.type,
            team_id=str(invitation.team_id) if invitation.team_id else None,
            expires_at=invitation.expires_at.isoformat() if invitation.expires_at else None,
            created_at=invitation.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
