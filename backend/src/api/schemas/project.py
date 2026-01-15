"""Pydantic schemas for projects."""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|paused|blocked|completed|archived)$")
    tags: Optional[List[str]] = Field(default_factory=list)
    technology_tags: Optional[List[str]] = Field(default_factory=list)
    cursor_instructions: Optional[str] = None
    github_repo_url: Optional[str] = None
    github_repo_id: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    team_id: UUID = Field(..., description="Team ID that will own this project")


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
    team_id: Optional[UUID] = Field(None, description="Team ID that will own this project")
    resume_context: Optional[Dict[str, Any]] = Field(None, description="Resume context JSON object")


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: UUID
    team_id: UUID
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    last_session_at: Optional[datetime] = None
    resume_context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    @field_serializer('id', 'team_id', 'created_by', 'updated_by')
    def serialize_uuid(self, value: UUID | str | None, _info) -> Optional[str]:
        """Serialize UUID to string."""
        if value is None:
            return None
        return str(value) if isinstance(value, UUID) else value


class ProjectListResponse(BaseModel):
    """Schema for project list response."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
