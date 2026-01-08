"""Document controller."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.document_service import document_service
from src.services.project_service import project_service
from src.services.signalr_hub import broadcast_project_update
from src.api.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new document."""
    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=document_data.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create documents in this project",
        )

    document = document_service.create_document(
        db=db,
        project_id=document_data.project_id,
        type=document_data.type,
        title=document_data.title,
        content=document_data.content,
        element_id=document_data.element_id,
        tags=document_data.tags,
    )
    
    # Broadcast document creation via SignalR
    background_tasks.add_task(
        broadcast_project_update,
        str(document_data.project_id),
        {
            "action": "document_created",
            "document_id": str(document.id),
            "document_type": document.type,
            "document_title": document.title,
            "element_id": str(document.element_id) if document.element_id else None
        }
    )
    
    return document


@router.get("/project/{project_id}", response_model=DocumentListResponse)
async def list_project_documents(
    project_id: UUID,
    type_filter: Optional[str] = Query(None, alias="type"),
    element_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List documents for a project."""
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

    skip = (page - 1) * page_size
    documents, total = document_service.get_documents_by_project(
        db=db,
        project_id=project_id,
        type=type_filter,
        element_id=element_id,
        search=search,
        skip=skip,
        limit=page_size,
    )

    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get document by ID."""
    document = document_service.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=document.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document's project",
        )

    return document


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get document content (markdown)."""
    document = document_service.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check project access
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=document.project_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document's project",
        )

    return {
        "id": str(document.id),
        "title": document.title,
        "type": document.type,
        "content": document.content,
        "version": document.version,
    }


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update document."""
    document = document_service.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=document.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this document",
        )

    updated_document = document_service.update_document(
        db=db,
        document_id=document_id,
        title=document_data.title,
        content=document_data.content,
        tags=document_data.tags,
    )

    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Broadcast document update via SignalR
    changes = {
        "action": "document_updated",
        "document_id": str(document_id)
    }
    if document_data.title is not None:
        changes["title"] = document_data.title
    if document_data.content is not None:
        changes["content_updated"] = True  # Don't send full content, just flag
    if document_data.tags is not None:
        changes["tags"] = document_data.tags
    
    background_tasks.add_task(
        broadcast_project_update,
        str(document.project_id),
        changes
    )

    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete document."""
    document = document_service.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check project access (editor or owner)
    if not project_service.check_user_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        project_id=document.project_id,
        required_role="editor",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document",
        )

    # Store project_id before deletion for broadcast
    project_id = document.project_id

    success = document_service.delete_document(db=db, document_id=document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Broadcast document deletion via SignalR
    background_tasks.add_task(
        broadcast_project_update,
        str(project_id),
        {
            "action": "document_deleted",
            "document_id": str(document_id)
        }
    )
