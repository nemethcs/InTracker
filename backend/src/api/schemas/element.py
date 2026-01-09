"""Pydantic schemas for project elements."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ElementBase(BaseModel):
    """Base element schema."""
    type: str = Field(
        ...,
        pattern="^(module|feature|component|milestone|technical_block|decision_point)$",
    )
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="new", pattern="^(new|in_progress|tested|done)$")
    position: Optional[int] = None
    definition_of_done: Optional[str] = None


class ElementCreate(ElementBase):
    """Schema for creating an element."""
    project_id: UUID
    parent_id: Optional[UUID] = None


class ElementUpdate(BaseModel):
    """Schema for updating an element."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(new|in_progress|tested|done)$")
    position: Optional[int] = None
    definition_of_done: Optional[str] = None
    parent_id: Optional[UUID] = None


class ElementResponse(ElementBase):
    """Schema for element response."""
    id: UUID
    project_id: UUID
    parent_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ElementTreeResponse(ElementResponse):
    """Schema for element with children tree."""
    children: List["ElementTreeResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ElementWithTodosResponse(ElementResponse):
    """Schema for element with todos."""
    todos: List[dict] = Field(default_factory=list)
    dependencies: List[dict] = Field(default_factory=list)


class DependencyCreate(BaseModel):
    """Schema for creating a dependency."""
    depends_on_element_id: UUID
    dependency_type: str = Field(..., pattern="^(blocks|requires|related)$")


class DependencyResponse(BaseModel):
    """Schema for dependency response."""
    id: UUID
    element_id: UUID
    depends_on_element_id: UUID
    dependency_type: str
    created_at: datetime

    class Config:
        from_attributes = True
