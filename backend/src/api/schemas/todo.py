"""Pydantic schemas for todos."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class TodoBase(BaseModel):
    """Base todo schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="new", pattern="^(new|in_progress|tested|done)$")
    position: Optional[int] = None
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")
    blocker_reason: Optional[str] = None
    assigned_to: Optional[UUID] = None


class TodoCreate(TodoBase):
    """Schema for creating a todo."""
    element_id: UUID
    feature_id: Optional[UUID] = None


class TodoUpdate(BaseModel):
    """Schema for updating a todo."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(new|in_progress|tested|done)$")
    position: Optional[int] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    blocker_reason: Optional[str] = None
    assigned_to: Optional[UUID] = None
    feature_id: Optional[UUID] = None


class TodoResponse(TodoBase):
    """Schema for todo response."""
    id: UUID
    element_id: UUID
    feature_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    version: int
    github_issue_number: Optional[int] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    """Schema for todo list response."""
    todos: list[TodoResponse]
    total: int
    page: int
    page_size: int
