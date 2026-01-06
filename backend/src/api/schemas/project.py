"""Pydantic schemas for projects."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|paused|blocked|completed|archived)$")
    tags: List[str] = Field(default_factory=list)
    technology_tags: List[str] = Field(default_factory=list)
    cursor_instructions: Optional[str] = None
    github_repo_url: Optional[str] = None
    github_repo_id: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|blocked|completed|archived)$")
    tags: Optional[List[str]] = None
    technology_tags: Optional[List[str]] = None
    cursor_instructions: Optional[str] = None
    github_repo_url: Optional[str] = None
    github_repo_id: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_session_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for project list response."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
