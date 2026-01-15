"""Team schemas."""
from pydantic import BaseModel, field_serializer
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TeamCreateRequest(BaseModel):
    """Team creation request schema."""
    name: str
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Development Team",
                "description": "Main development team",
            }
        }


class TeamUpdateRequest(BaseModel):
    """Team update request schema."""
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Team Name",
                "description": "Updated description",
            }
        }


class TeamMemberResponse(BaseModel):
    """Team member response schema."""
    id: str
    team_id: str
    user_id: str
    role: str
    joined_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer('id', 'team_id', 'user_id')
    def serialize_uuid(self, value: UUID | str, _info) -> str:
        """Serialize UUID to string."""
        return str(value) if isinstance(value, UUID) else value


class TeamResponse(BaseModel):
    """Team response schema."""
    id: str
    name: str
    description: Optional[str]
    language: Optional[str] = None  # 'hu' (Hungarian) or 'en' (English)
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('id', 'created_by')
    def serialize_uuid(self, value: UUID | str, _info) -> str:
        """Serialize UUID to string."""
        return str(value) if isinstance(value, UUID) else value


class TeamLanguageRequest(BaseModel):
    """Team language configuration request schema."""
    language: str  # 'hu' (Hungarian) or 'en' (English)

    class Config:
        json_schema_extra = {
            "example": {
                "language": "hu",
            }
        }


class TeamListResponse(BaseModel):
    """Team list response schema with pagination."""
    teams: List[TeamResponse]
    total: int
    page: Optional[int] = Field(None, description="Current page number (1-indexed)")
    page_size: Optional[int] = Field(None, description="Number of items per page")


class TeamInvitationResponse(BaseModel):
    """Team invitation response schema."""
    code: str
    type: str
    team_id: Optional[str]
    expires_at: Optional[str]
    created_at: str
    email_sent_to: Optional[str] = None
    email_sent_at: Optional[str] = None