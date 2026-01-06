"""Todo controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.todo_service import todo_service
from src.services.project_service import project_service
from src.api.schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoListResponse,
)

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new todo."""
    try:
        todo = todo_service.create_todo(
            db=db,
            element_id=todo_data.element_id,
            title=todo_data.title,
            description=todo_data.description,
            status=todo_data.status,
            feature_id=todo_data.feature_id,
            position=todo_data.position,
            estimated_effort=todo_data.estimated_effort,
            created_by=UUID(current_user["user_id"]),
            assigned_to=todo_data.assigned_to,
        )
        return todo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    project_id: Optional[UUID] = Query(None),
    feature_id: Optional[UUID] = Query(None),
    element_id: Optional[UUID] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List todos with filtering."""
    user_id = UUID(current_user["user_id"])

    # If assigned_to is not specified, default to current user's todos
    if assigned_to is None:
        assigned_to = user_id

    # If assigned_to is current user, get their todos
    if assigned_to == user_id:
        skip = (page - 1) * page_size
        todos, total = todo_service.get_todos_by_user(
            db=db,
            user_id=user_id,
            status=status_filter,
            skip=skip,
            limit=page_size,
        )
    else:
        # For other users, need to check project access
        # This is simplified - in production, you'd want more sophisticated filtering
        todos = []
        total = 0

    # Filter by feature_id if provided
    if feature_id:
        todos = [t for t in todos if t.feature_id == feature_id]

    # Filter by element_id if provided
    if element_id:
        todos = [t for t in todos if t.element_id == element_id]

    return TodoListResponse(
        todos=todos,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get todo by ID."""
    todo = todo_service.get_todo_by_id(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # Check project access through element
    from src.database.models import ProjectElement
    element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
    if element:
        if not project_service.check_user_access(
            db=db,
            user_id=UUID(current_user["user_id"]),
            project_id=element.project_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this todo's project",
            )

    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID,
    todo_data: TodoUpdate,
    expected_version: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update todo with optimistic locking."""
    todo = todo_service.get_todo_by_id(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # Check project access through element
    from src.database.models import ProjectElement
    element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
    if element:
        if not project_service.check_user_access(
            db=db,
            user_id=UUID(current_user["user_id"]),
            project_id=element.project_id,
            required_role="editor",
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this todo",
            )

    try:
        updated_todo = todo_service.update_todo(
            db=db,
            todo_id=todo_id,
            title=todo_data.title,
            description=todo_data.description,
            status=todo_data.status,
            position=todo_data.position,
            estimated_effort=todo_data.estimated_effort,
            blocker_reason=todo_data.blocker_reason,
            assigned_to=todo_data.assigned_to,
            expected_version=expected_version or todo.version,
        )

        if not updated_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )

        return updated_todo
    except ValueError as e:
        if "modified by another user" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete todo."""
    todo = todo_service.get_todo_by_id(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # Check project access through element
    from src.database.models import ProjectElement
    element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
    if element:
        if not project_service.check_user_access(
            db=db,
            user_id=UUID(current_user["user_id"]),
            project_id=element.project_id,
            required_role="editor",
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this todo",
            )

    success = todo_service.delete_todo(db=db, todo_id=todo_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )


@router.put("/{todo_id}/status", response_model=TodoResponse)
async def update_todo_status(
    todo_id: UUID,
    status: str = Query(..., pattern="^(todo|in_progress|blocked|done)$"),
    expected_version: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update todo status with optimistic locking."""
    todo = todo_service.get_todo_by_id(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # Check project access
    from src.database.models import ProjectElement
    element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
    if element:
        if not project_service.check_user_access(
            db=db,
            user_id=UUID(current_user["user_id"]),
            project_id=element.project_id,
            required_role="editor",
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this todo",
            )

    try:
        updated_todo = todo_service.update_todo_status(
            db=db,
            todo_id=todo_id,
            status=status,
            expected_version=expected_version or todo.version,
        )

        if not updated_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )

        return updated_todo
    except ValueError as e:
        if "modified by another user" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{todo_id}/assign", response_model=TodoResponse)
async def assign_todo(
    todo_id: UUID,
    user_id: UUID = Query(..., alias="user_id"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign todo to a user."""
    todo = todo_service.get_todo_by_id(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # Check project access
    from src.database.models import ProjectElement
    element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
    if element:
        if not project_service.check_user_access(
            db=db,
            user_id=UUID(current_user["user_id"]),
            project_id=element.project_id,
            required_role="editor",
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to assign todos in this project",
            )

    updated_todo = todo_service.update_todo(
        db=db,
        todo_id=todo_id,
        assigned_to=user_id,
        expected_version=todo.version,
    )

    if not updated_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    return updated_todo
