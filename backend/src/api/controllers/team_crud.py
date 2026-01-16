"""Team CRUD endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.services.team_service import TeamService
from src.api.middleware.auth import get_current_user, get_current_team_leader, get_current_admin_user
from src.api.schemas.team import (
    TeamCreateRequest,
    TeamUpdateRequest,
    TeamResponse,
    TeamListResponse,
)

# Import shared router from team_controller
# Note: Import at end to avoid circular import
from .team_controller import router  # noqa: E402


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
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    """List teams with pagination. Returns user's teams or all teams if admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")

    skip = (page - 1) * page_size
    # Admins can see all teams, others only their teams
    if user_role == "admin":
        teams, total = TeamService.list_teams(db, user_id=None, skip=skip, limit=page_size)
    else:
        teams, total = TeamService.list_teams(db, user_id=user_id, skip=skip, limit=page_size)

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
    return TeamListResponse(teams=teams_data, total=total, page=page, page_size=page_size)


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
