"""Pydantic schemas for documents."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DocumentBase(BaseModel):
    """Base document schema."""
    type: str = Field(
        ...,
        pattern="^(architecture|adr|notes)$",
    )
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    project_id: UUID
    element_id: Optional[UUID] = None
    feature_id: Optional[UUID] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: UUID
    project_id: UUID
    element_id: Optional[UUID] = None
    feature_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
