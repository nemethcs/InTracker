"""Idea controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.idea_service import IdeaService
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new idea."""
    idea = idea_service.create_idea(
        db=db,
        title=idea_data.title,
        description=idea_data.description,
        status=idea_data.status,
        tags=idea_data.tags,
    )
    return idea


@router.get("", response_model=IdeaListResponse)
async def list_ideas(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List ideas with optional filtering."""
    skip = (page - 1) * page_size
    ideas, total = idea_service.get_ideas(
        db=db,
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
    """Get idea by ID."""
    idea = idea_service.get_idea_by_id(db=db, idea_id=idea_id)
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    return idea


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: UUID,
    idea_data: IdeaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update idea."""
    idea = idea_service.update_idea(
        db=db,
        idea_id=idea_id,
        title=idea_data.title,
        description=idea_data.description,
        status=idea_data.status,
        tags=idea_data.tags,
    )
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete idea."""
    success = idea_service.delete_idea(db=db, idea_id=idea_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )


@router.post("/{idea_id}/convert", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def convert_idea_to_project(
    idea_id: UUID,
    convert_data: IdeaConvertRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert idea to project."""
    project = idea_service.convert_idea_to_project(
        db=db,
        idea_id=idea_id,
        user_id=UUID(current_user["user_id"]),
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
    return project
