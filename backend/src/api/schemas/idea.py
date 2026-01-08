"""Pydantic schemas for ideas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class IdeaBase(BaseModel):
    """Base idea schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")
    tags: Optional[List[str]] = Field(default_factory=list)


class IdeaCreate(IdeaBase):
    """Schema for creating an idea."""
    team_id: UUID = Field(..., description="Team ID that will own this idea")


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")
    tags: Optional[List[str]] = None


class IdeaResponse(IdeaBase):
    """Schema for idea response."""
    id: UUID
    team_id: UUID
    converted_to_project_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IdeaListResponse(BaseModel):
    """Schema for idea list response."""
    ideas: List[IdeaResponse]
    total: int


class IdeaConvertRequest(BaseModel):
    """Schema for converting idea to project."""
    project_name: Optional[str] = Field(None, min_length=1, max_length=255)
    project_description: Optional[str] = None
    project_status: str = Field(default="active", pattern="^(active|paused|blocked|completed|archived)$")
    project_tags: Optional[List[str]] = Field(default_factory=list)
    technology_tags: Optional[List[str]] = Field(default_factory=list)
