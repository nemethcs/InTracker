"""Todo controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models import ProjectElement
from src.api.middleware.auth import get_current_user
from src.services.todo_service import todo_service
from src.services.project_service import project_service
from src.services.feature_service import feature_service
from src.services.signalr_hub import broadcast_todo_update, broadcast_feature_update
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
            priority=todo_data.priority,
            created_by=UUID(current_user["user_id"]),
            assigned_to=todo_data.assigned_to,
        )
        
        # Broadcast todo creation via SignalR
        element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
        if element:
            background_tasks.add_task(
                broadcast_todo_update,
                str(element.project_id),
                str(todo.id),
                UUID(current_user["user_id"]),
                {
                    "title": todo.title,
                    "status": todo.status,
                    "action": "created"
                }
            )
            
            # Update feature progress if todo is linked to a feature
            if todo.feature_id:
                progress = feature_service.calculate_feature_progress(db=db, feature_id=todo.feature_id)
                feature = feature_service.get_feature_by_id(db=db, feature_id=todo.feature_id)
                background_tasks.add_task(
                    broadcast_feature_update,
                    str(element.project_id),
                    str(todo.feature_id),
                    progress["percentage"],
                    feature.status if feature else None
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
    skip = (page - 1) * page_size

    # Priority: project_id > feature_id > element_id > assigned_to
    if project_id:
        # Get all todos for the project
        # Check project access
        from src.services.project_service import project_service
        if not project_service.check_user_access(
            db=db,
            user_id=user_id,
            project_id=project_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )
        
        todos, total = todo_service.get_todos_by_project(
            db=db,
            project_id=project_id,
            status=status_filter,
            skip=skip,
            limit=page_size,
        )
        
        # Additional filters
        if feature_id:
            todos = [t for t in todos if t.feature_id == feature_id]
        if element_id:
            todos = [t for t in todos if t.element_id == element_id]
        if assigned_to:
            todos = [t for t in todos if t.assigned_to == assigned_to]
    elif feature_id:
        # Get todos for a specific feature
        todos = todo_service.get_todos_by_feature(
            db=db,
            feature_id=feature_id,
            status=status_filter,
        )
        total = len(todos)
        # Apply pagination
        todos = todos[skip:skip + page_size]
    elif element_id:
        # Get todos for a specific element
        todos = todo_service.get_todos_by_element(
            db=db,
            element_id=element_id,
            status=status_filter,
        )
        total = len(todos)
        # Apply pagination
        todos = todos[skip:skip + page_size]
    else:
        # Default: get todos assigned to current user
        if assigned_to is None:
            assigned_to = user_id
        
        todos, total = todo_service.get_todos_by_user(
            db=db,
            user_id=assigned_to,
            status=status_filter,
            skip=skip,
            limit=page_size,
        )

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
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
            priority=todo_data.priority,
            blocker_reason=todo_data.blocker_reason,
            assigned_to=todo_data.assigned_to,
            feature_id=todo_data.feature_id,
            expected_version=expected_version or todo.version,
        )

        if not updated_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )

        # Broadcast todo update via SignalR
        element = db.query(ProjectElement).filter(ProjectElement.id == updated_todo.element_id).first()
        if element:
            changes = {
                "title": todo_data.title if todo_data.title is not None else None,
                "description": todo_data.description if todo_data.description is not None else None,
                "status": todo_data.status if todo_data.status is not None else None,
                "priority": todo_data.priority if todo_data.priority is not None else None,
                "assigned_to": str(todo_data.assigned_to) if todo_data.assigned_to is not None else None,
            }
            # Remove None values
            changes = {k: v for k, v in changes.items() if v is not None}
            background_tasks.add_task(
                broadcast_todo_update,
                str(element.project_id),
                str(updated_todo.id),
                UUID(current_user["user_id"]),
                changes
            )
            
            # Update feature progress if todo is linked to a feature and status changed
            if updated_todo.feature_id and todo_data.status is not None:
                progress = feature_service.calculate_feature_progress(db=db, feature_id=updated_todo.feature_id)
                feature = feature_service.get_feature_by_id(db=db, feature_id=updated_todo.feature_id)
                background_tasks.add_task(
                    broadcast_feature_update,
                    str(element.project_id),
                    str(updated_todo.feature_id),
                    progress["percentage"],
                    feature.status if feature else None
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
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

    # Store feature_id before deletion for broadcast
    feature_id = todo.feature_id

    success = todo_service.delete_todo(db=db, todo_id=todo_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # Broadcast todo deletion via SignalR
    if element:
        background_tasks.add_task(
            broadcast_todo_update,
            str(element.project_id),
            str(todo_id),
            UUID(current_user["user_id"]),
            {
                "action": "deleted",
                "todoId": str(todo_id)
            }
        )
        
        # Update feature progress if todo was linked to a feature
        if feature_id:
            progress = feature_service.calculate_feature_progress(db=db, feature_id=feature_id)
            feature = feature_service.get_feature_by_id(db=db, feature_id=feature_id)
            background_tasks.add_task(
                broadcast_feature_update,
                str(element.project_id),
                str(feature_id),
                progress["percentage"],
                feature.status if feature else None
            )


@router.put("/{todo_id}/status", response_model=TodoResponse)
async def update_todo_status(
    todo_id: UUID,
    status: str = Query(..., pattern="^(new|in_progress|tested|done)$"),
    expected_version: Optional[int] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
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

        # Broadcast todo status update via SignalR
        element = db.query(ProjectElement).filter(ProjectElement.id == updated_todo.element_id).first()
        if element:
            background_tasks.add_task(
                broadcast_todo_update,
                str(element.project_id),
                str(updated_todo.id),
                UUID(current_user["user_id"]),
                {"status": status}
            )
            
            # Update feature progress if todo is linked to a feature
            if updated_todo.feature_id:
                progress = feature_service.calculate_feature_progress(db=db, feature_id=updated_todo.feature_id)
                feature = feature_service.get_feature_by_id(db=db, feature_id=updated_todo.feature_id)
                background_tasks.add_task(
                    broadcast_feature_update,
                    str(element.project_id),
                    str(updated_todo.feature_id),
                    progress["percentage"],
                    feature.status if feature else None
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
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

    # Broadcast todo assignment via SignalR
    if element:
        background_tasks.add_task(
            broadcast_todo_update,
            str(element.project_id),
            str(updated_todo.id),
            UUID(current_user["user_id"]),
            {
                "assigned_to": str(user_id)
            }
        )

    return updated_todo
