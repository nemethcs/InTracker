"""Element controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.element_service import element_service
from src.services.project_service import project_service
from src.api.schemas.element import (
    ElementCreate,
    ElementUpdate,
    ElementResponse,
    ElementTreeResponse,
    ElementWithTodosResponse,
    DependencyCreate,
    DependencyResponse,
)

router = APIRouter(prefix="/elements", tags=["elements"])


@router.post("", response_model=ElementResponse, status_code=status.HTTP_201_CREATED)
async def create_element(
    element_data: ElementCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new element."""
    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element_data.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create elements in this project",
        )

    try:
        element = element_service.create_element(
            db=db,
            project_id=element_data.project_id,
            type=element_data.type,
            title=element_data.title,
            description=element_data.description,
            status=element_data.status,
            parent_id=element_data.parent_id,
            position=element_data.position,
            definition_of_done=element_data.definition_of_done,
        )
        return element
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/project/{project_id}/tree")
async def get_project_elements_tree(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get project elements as a tree structure."""
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

    tree = element_service.build_element_tree(db=db, project_id=project_id)
    return {"project_id": str(project_id), "elements": tree}


@router.get("/{element_id}", response_model=ElementWithTodosResponse)
async def get_element(
    element_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get element with todos and dependencies."""
    element_data = element_service.get_element_with_todos(db=db, element_id=element_id)
    if not element_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )

    element = element_data["element"]

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this element's project",
        )

    return {
        "id": element.id,
        "project_id": element.project_id,
        "parent_id": element.parent_id,
        "type": element.type,
        "title": element.title,
        "description": element.description,
        "status": element.status,
        "position": element.position,
        "definition_of_done": element.definition_of_done,
        "github_issue_number": element.github_issue_number,
        "github_issue_url": element.github_issue_url,
        "created_at": element.created_at,
        "updated_at": element.updated_at,
        "todos": [
            {
                "id": str(todo.id),
                "title": todo.title,
                "status": todo.status,
                "feature_id": str(todo.feature_id) if todo.feature_id else None,
            }
            for todo in element_data["todos"]
        ],
        "dependencies": [
            {
                "id": str(dep.id),
                "depends_on_element_id": str(dep.depends_on_element_id),
                "dependency_type": dep.dependency_type,
            }
            for dep in element_data["dependencies"]
        ],
    }


@router.put("/{element_id}", response_model=ElementResponse)
async def update_element(
    element_id: UUID,
    element_data: ElementUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update element."""
    element = element_service.get_element_by_id(db=db, element_id=element_id)
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this element",
        )

    try:
        updated_element = element_service.update_element(
            db=db,
            element_id=element_id,
            title=element_data.title,
            description=element_data.description,
            status=element_data.status,
            position=element_data.position,
            definition_of_done=element_data.definition_of_done,
            parent_id=element_data.parent_id,
        )

        if not updated_element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Element not found",
            )

        return updated_element
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_element(
    element_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete element."""
    element = element_service.get_element_by_id(db=db, element_id=element_id)
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )

    # Check project access (owner only)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element.project_id,
        required_role="owner",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete elements",
        )

    success = element_service.delete_element(db=db, element_id=element_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )


@router.post("/{element_id}/dependencies", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
async def add_dependency(
    element_id: UUID,
    dependency_data: DependencyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add dependency to an element."""
    element = element_service.get_element_by_id(db=db, element_id=element_id)
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this element",
        )

    try:
        dependency = element_service.add_dependency(
            db=db,
            element_id=element_id,
            depends_on_element_id=dependency_data.depends_on_element_id,
            dependency_type=dependency_data.dependency_type,
        )
        return dependency
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{element_id}/dependencies")
async def get_element_dependencies(
    element_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dependencies for an element."""
    element = element_service.get_element_by_id(db=db, element_id=element_id)
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this element's project",
        )

    dependencies = element_service.get_element_dependencies(db=db, element_id=element_id)
    return {"dependencies": dependencies}


@router.delete("/{element_id}/dependencies/{depends_on_element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_dependency(
    element_id: UUID,
    depends_on_element_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove dependency."""
    element = element_service.get_element_by_id(db=db, element_id=element_id)
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=element.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this element",
        )

    success = element_service.remove_dependency(
        db=db,
        element_id=element_id,
        depends_on_element_id=depends_on_element_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )
