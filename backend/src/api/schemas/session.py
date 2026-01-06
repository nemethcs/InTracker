"""Pydantic schemas for sessions."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SessionBase(BaseModel):
    """Base session schema."""
    title: Optional[str] = None
    goal: Optional[str] = None
    feature_ids: List[UUID] = Field(default_factory=list)


class SessionCreate(SessionBase):
    """Schema for creating a session."""
    project_id: UUID


class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    title: Optional[str] = None
    goal: Optional[str] = None
    notes: Optional[str] = None
    todos_completed: Optional[List[UUID]] = None
    features_completed: Optional[List[UUID]] = None
    elements_updated: Optional[List[UUID]] = None


class SessionResponse(SessionBase):
    """Schema for session response."""
    id: UUID
    project_id: UUID
    user_id: Optional[UUID] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None
    todos_completed: List[UUID] = Field(default_factory=list)
    features_completed: List[UUID] = Field(default_factory=list)
    elements_updated: List[UUID] = Field(default_factory=list)
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for session list response."""
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int


class EndSessionRequest(BaseModel):
    """Schema for ending a session."""
    summary: Optional[str] = None
    notes: Optional[str] = None
    todos_completed: Optional[List[UUID]] = None
    features_completed: Optional[List[UUID]] = None
    elements_updated: Optional[List[UUID]] = None
