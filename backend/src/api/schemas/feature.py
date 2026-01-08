"""Pydantic schemas for features."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class FeatureBase(BaseModel):
    """Base feature schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="new", pattern="^(new|in_progress|done|tested|merged)$")
    assigned_to: Optional[UUID] = None


class FeatureCreate(FeatureBase):
    """Schema for creating a feature."""
    project_id: UUID
    element_ids: Optional[List[UUID]] = Field(default_factory=list)


class FeatureUpdate(BaseModel):
    """Schema for updating a feature."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(new|in_progress|done|tested|merged)$")
    assigned_to: Optional[UUID] = None


class FeatureResponse(FeatureBase):
    """Schema for feature response."""
    id: UUID
    project_id: UUID
    progress_percentage: int
    total_todos: int
    completed_todos: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureListResponse(BaseModel):
    """Schema for feature list response."""
    features: List[FeatureResponse]
    total: int
