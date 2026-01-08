"""Feature controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.feature_service import feature_service
from src.services.project_service import project_service
from src.services.signalr_hub import broadcast_feature_update
from src.api.schemas.feature import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
    FeatureListResponse,
)

router = APIRouter(prefix="/features", tags=["features"])


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    feature_data: FeatureCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new feature."""
    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature_data.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create features in this project",
        )

    feature = feature_service.create_feature(
        db=db,
        project_id=feature_data.project_id,
        name=feature_data.name,
        description=feature_data.description,
        status=feature_data.status,
        created_by=UUID(current_user["user_id"]),
        assigned_to=feature_data.assigned_to,
        element_ids=feature_data.element_ids,
    )
    return feature


@router.get("/project/{project_id}", response_model=FeatureListResponse)
async def list_features(
    project_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    sort: Optional[str] = Query("updated_at_desc", description="Sort order: updated_at_desc (default), updated_at_asc, created_at_desc, created_at_asc, name_asc, name_desc"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List features for a project. Default sort: updated_at DESC (newest first)."""
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

    features, total = feature_service.get_features_by_project(
        db=db,
        project_id=project_id,
        status=status_filter,
        sort=sort,
    )

    return FeatureListResponse(features=features, total=total)


@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(
    feature_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get feature by ID."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this feature's project",
        )

    return feature


@router.put("/{feature_id}", response_model=FeatureResponse)
async def update_feature(
    feature_id: UUID,
    feature_data: FeatureUpdate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update feature."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this feature",
        )

    updated_feature = feature_service.update_feature(
        db=db,
        feature_id=feature_id,
        name=feature_data.name,
        description=feature_data.description,
        status=feature_data.status,
        assigned_to=feature_data.assigned_to,
    )
    
    # Broadcast feature update via SignalR
    if updated_feature:
        background_tasks.add_task(
            broadcast_feature_update,
            str(updated_feature.project_id),
            str(updated_feature.id),
            updated_feature.progress_percentage
        )

    return updated_feature


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    feature_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete feature."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access (owner only)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
        required_role="owner",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete features",
        )

    success = feature_service.delete_feature(db=db, feature_id=feature_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )


@router.get("/{feature_id}/todos")
async def get_feature_todos(
    feature_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get todos for a feature."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this feature's project",
        )

    todos = feature_service.get_feature_todos(
        db=db,
        feature_id=feature_id,
        status=status_filter,
    )

    return {"todos": todos, "count": len(todos)}


@router.get("/{feature_id}/elements")
async def get_feature_elements(
    feature_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get elements linked to a feature."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this feature's project",
        )

    elements = feature_service.get_feature_elements(db=db, feature_id=feature_id)

    return {"elements": elements, "count": len(elements)}


@router.post("/{feature_id}/elements/{element_id}", status_code=status.HTTP_201_CREATED)
async def link_element_to_feature(
    feature_id: UUID,
    element_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link an element to a feature."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this feature",
        )

    success = feature_service.link_element_to_feature(
        db=db,
        feature_id=feature_id,
        element_id=element_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Element is already linked to this feature",
        )

    return {"message": "Element linked to feature successfully"}


@router.post("/{feature_id}/calculate-progress")
async def calculate_feature_progress(
    feature_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate and update feature progress."""
    feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=feature.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this feature's project",
        )

    progress = feature_service.calculate_feature_progress(db=db, feature_id=feature_id)
    
    # Broadcast feature progress update via SignalR
    background_tasks.add_task(
        broadcast_feature_update,
        str(feature.project_id),
        str(feature_id),
        progress["percentage"]
    )
    
    return progress
