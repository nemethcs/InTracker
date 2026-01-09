"""Idea controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.idea_service import IdeaService
from src.services.team_service import TeamService
from src.services.signalr_hub import broadcast_idea_update, broadcast_project_update
from src.api.schemas.idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaListResponse,
    IdeaConvertRequest,
)
from src.api.schemas.project import ProjectResponse

router = APIRouter(prefix="/ideas", tags=["ideas"])

idea_service = IdeaService()


@router.post("", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    idea_data: IdeaCreate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new idea for a team."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    team_id = idea_data.team_id
    
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
    
    user_id = UUID(current_user["user_id"])
    idea = idea_service.create_idea(
        db=db,
        team_id=team_id,
        title=idea_data.title,
        description=idea_data.description,
        status=idea_data.status,
        tags=idea_data.tags,
        current_user_id=user_id,
    )
    
    # Broadcast idea creation via SignalR
    background_tasks.add_task(
        broadcast_idea_update,
        str(team_id),
        str(idea.id),
        {
            "action": "created",
            "title": idea.title,
            "status": idea.status
        }
    )
    
    return idea


@router.get("", response_model=IdeaListResponse)
async def list_ideas(
    status_filter: Optional[str] = Query(None, alias="status"),
    team_id: Optional[UUID] = Query(None, description="Filter by team ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List ideas accessible to the user (from teams where user is a member)."""
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
    ideas, total = idea_service.get_ideas(
        db=db,
        user_id=user_id,
        team_id=team_id,
        status=status_filter,
        skip=skip,
        limit=page_size,
    )

    return IdeaListResponse(ideas=ideas, total=total)


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get idea by ID. User must be a member of the team that owns the idea."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    
    idea = idea_service.get_idea_by_id(db=db, idea_id=idea_id)
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    
    # Check if user has access to the team that owns the idea
    if user_role != "admin" and not TeamService.is_team_member(db, idea.team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this idea",
        )
    
    return idea


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: UUID,
    idea_data: IdeaUpdate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update idea. User must be a team leader or admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    
    idea = idea_service.get_idea_by_id(db=db, idea_id=idea_id)
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    
    # Check if user has access (admin or team leader)
    if user_role != "admin" and not TeamService.is_team_leader(db, idea.team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders can edit ideas",
        )
    
    user_id = UUID(current_user["user_id"])
    idea = idea_service.update_idea(
        db=db,
        idea_id=idea_id,
        title=idea_data.title,
        description=idea_data.description,
        status=idea_data.status,
        tags=idea_data.tags,
        current_user_id=user_id,
    )
    
    # Broadcast idea update via SignalR
    changes = {}
    if idea_data.title is not None:
        changes["title"] = idea_data.title
    if idea_data.description is not None:
        changes["description"] = idea_data.description
    if idea_data.status is not None:
        changes["status"] = idea_data.status
    if idea_data.tags is not None:
        changes["tags"] = idea_data.tags
    
    if changes:
        background_tasks.add_task(
            broadcast_idea_update,
            str(idea.team_id),
            str(idea_id),
            changes
        )
    
    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete idea. User must be a team leader or admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    
    idea = idea_service.get_idea_by_id(db=db, idea_id=idea_id)
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    
    # Check if user has access (admin or team leader)
    if user_role != "admin" and not TeamService.is_team_leader(db, idea.team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders can delete ideas",
        )

    # Store team_id before deletion for broadcast
    team_id = idea.team_id
    
    success = idea_service.delete_idea(db=db, idea_id=idea_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    # Broadcast idea deletion via SignalR
    background_tasks.add_task(
        broadcast_idea_update,
        str(team_id),
        str(idea_id),
        {
            "action": "deleted"
        }
    )


@router.post("/{idea_id}/convert", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def convert_idea_to_project(
    idea_id: UUID,
    convert_data: IdeaConvertRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert idea to project. User must be a team leader or admin."""
    user_id = UUID(current_user["user_id"])
    user_role = current_user.get("role")
    
    idea = idea_service.get_idea_by_id(db=db, idea_id=idea_id)
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    
    # Check if user has access (admin or team leader)
    if user_role != "admin" and not TeamService.is_team_leader(db, idea.team_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders can convert ideas to projects",
        )
    
    # Store team_id before conversion for broadcast
    team_id = idea.team_id
    
    project = idea_service.convert_idea_to_project(
        db=db,
        idea_id=idea_id,
        project_name=convert_data.project_name,
        project_description=convert_data.project_description,
        project_status=convert_data.project_status,
        project_tags=convert_data.project_tags,
        technology_tags=convert_data.technology_tags,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    
    # Broadcast idea conversion (idea deleted + project created)
    background_tasks.add_task(
        broadcast_idea_update,
        str(team_id),
        str(idea_id),
        {
            "action": "converted",
            "project_id": str(project.id)
        }
    )
    
    # Also broadcast project creation
    background_tasks.add_task(
        broadcast_project_update,
        str(project.id),
        {
            "action": "created",
            "name": project.name,
            "status": project.status,
            "team_id": str(project.team_id),
            "converted_from_idea_id": str(idea_id)
        }
    )
    
    return project
