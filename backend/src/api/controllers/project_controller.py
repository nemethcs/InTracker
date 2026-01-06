"""Project controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.project_service import project_service
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
    """Create a new project."""
    project = project_service.create_project(
        db=db,
        user_id=UUID(current_user["user_id"]),
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's projects."""
    skip = (page - 1) * page_size
    projects, total = project_service.get_user_projects(
        db=db,
        user_id=UUID(current_user["user_id"]),
        status=status_filter,
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
    # Check access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this project",
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
    # Check access (owner only)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=project_id,
        required_role="owner",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete the project",
        )

    success = project_service.delete_project(db=db, project_id=project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
