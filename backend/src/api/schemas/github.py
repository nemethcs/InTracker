"""Pydantic schemas for GitHub integration."""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class GitHubConnectRequest(BaseModel):
    """Schema for connecting GitHub repository."""
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)


class GitHubRepoResponse(BaseModel):
    """Schema for GitHub repository response."""
    id: int
    name: str
    full_name: str
    owner: str
    private: bool
    default_branch: str
    url: str


class BranchResponse(BaseModel):
    """Schema for branch response."""
    id: Optional[UUID] = None
    name: str
    sha: str
    protected: bool
    feature_id: Optional[UUID] = None
    status: Optional[str] = None


class BranchCreateRequest(BaseModel):
    """Schema for creating a branch."""
    feature_id: UUID
    branch_name: str = Field(..., min_length=1)
    from_branch: str = Field(default="main")


class GitHubWebhookPayload(BaseModel):
    """Schema for GitHub webhook payload (simplified)."""
    action: Optional[str] = None
    repository: Optional[dict] = None
    pull_request: Optional[dict] = None
    issue: Optional[dict] = None
    ref: Optional[str] = None


class CursorDeeplinkRequest(BaseModel):
    """Schema for generating Cursor deeplink."""
    repo_url: str = Field(..., min_length=1)


class CursorDeeplinkResponse(BaseModel):
    """Schema for Cursor deeplink response."""
    deeplink: str
    repo_url: str
    owner: str
    repo_name: str
    feature_branches: List[str]
