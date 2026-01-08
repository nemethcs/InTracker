"""Project controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.project_service import project_service
from src.services.team_service import TeamService
from src.api.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project for a team."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    team_id = project_data.team_id
    
    # Verify team exists
    team = TeamService.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    
    # Check if user has access to the team (admin or team member)
    if user_role != "admin" and not TeamService.is_team_member(db, team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )
    
    project = project_service.create_project(
        db=db,
        team_id=team_id,
        name=project_data.name,
        description=project_data.description,
        status=project_data.status,
        tags=project_data.tags,
        technology_tags=project_data.technology_tags,
        cursor_instructions=project_data.cursor_instructions,
        github_repo_url=project_data.github_repo_url,
        github_repo_id=project_data.github_repo_id,
    )
    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status_filter: Optional[str] = Query(None, alias="status"),
    team_id: Optional[UUID] = Query(None, description="Filter by team ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List projects accessible to the user (from teams where user is a member)."""
    user_id = UUID(current_user["user_id"])
    
    # If team_id is provided, verify user has access to that team
    if team_id:
        user_role = current_user.get("role")
        if user_role != "admin" and not TeamService.is_team_member(db, team_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team",
            )
    
    skip = (page - 1) * page_size
    projects, total = project_service.get_user_projects(
        db=db,
        user_id=user_id,
        status=status_filter,
        team_id=team_id,
        skip=skip,
        limit=page_size,
    )

    return ProjectListResponse(
        projects=projects,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get project by ID."""
    # Check access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )

    project = project_service.get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update project."""
    # Check access (team leader or admin)
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    
    if user_role != "admin":
        project = project_service.get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Only team leaders can edit projects
        if not TeamService.is_team_leader(db, project.team_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team leaders can edit projects",
            )

    # If team_id is being updated, verify the new team exists and user has access
    if project_data.team_id is not None:
        new_team = TeamService.get_team_by_id(db, project_data.team_id)
        if not new_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        
        # Check if user has access to the new team (admin or team member)
        if user_role != "admin" and not TeamService.is_team_member(db, project_data.team_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team",
            )

    project = project_service.update_project(
        db=db,
        project_id=project_id,
        name=project_data.name,
        description=project_data.description,
        status=project_data.status,
        tags=project_data.tags,
        technology_tags=project_data.technology_tags,
        cursor_instructions=project_data.cursor_instructions,
        github_repo_url=project_data.github_repo_url,
        github_repo_id=project_data.github_repo_id,
        team_id=project_data.team_id,
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete project (owner only)."""
    # Check access (team leader or admin only)
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    
    if user_role != "admin":
        project = project_service.get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Only team leaders can delete projects
        if not TeamService.is_team_leader(db, project.team_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team leaders can delete projects",
            )

    success = project_service.delete_project(db=db, project_id=project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


@router.get("/{project_id}/active-users")
async def get_active_users(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get active users for a project (users with open MCP sessions on project todos).
    
    Active user = user with open session (ended_at IS NULL) on the project.
    If no open sessions, returns empty array.
    """
    from src.services.session_service import session_service
    
    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )

    active_users = session_service.get_active_users_for_project(db=db, project_id=project_id)
    return {"active_users": active_users, "count": len(active_users)}
