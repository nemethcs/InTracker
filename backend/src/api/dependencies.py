"""Dependency injection for FastAPI - centralized service dependencies."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.api.middleware.auth import get_current_user
from src.services.project_service import ProjectService
from src.services.feature_service import FeatureService
from src.services.todo_service import TodoService
from src.services.element_service import ElementService
from src.services.session_service import SessionService
from src.services.document_service import DocumentService
from src.services.idea_service import IdeaService
from src.services.team_service import TeamService
from src.services.invitation_service import InvitationService
from src.services.auth_service import AuthService
from src.services.github_service import GitHubService
from src.services.mcp_key_service import McpKeyService


# Type aliases for cleaner dependency annotations
DatabaseDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[dict, Depends(get_current_user)]


# Service dependencies - using global instances for stateless services
# These are singletons that don't maintain state, so global instances are safe
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    from src.services.project_service import project_service
    return project_service


def get_feature_service() -> FeatureService:
    """Get FeatureService instance."""
    from src.services.feature_service import feature_service
    return feature_service


def get_todo_service() -> TodoService:
    """Get TodoService instance."""
    from src.services.todo_service import todo_service
    return todo_service


def get_element_service() -> ElementService:
    """Get ElementService instance."""
    from src.services.element_service import element_service
    return element_service


def get_session_service() -> SessionService:
    """Get SessionService instance."""
    from src.services.session_service import session_service
    return session_service


def get_document_service() -> DocumentService:
    """Get DocumentService instance."""
    from src.services.document_service import document_service
    return document_service


def get_idea_service() -> IdeaService:
    """Get IdeaService instance."""
    return IdeaService()


def get_team_service() -> TeamService:
    """Get TeamService instance (static methods, no instance needed)."""
    return TeamService


def get_invitation_service() -> InvitationService:
    """Get InvitationService instance."""
    return InvitationService()


def get_auth_service() -> AuthService:
    """Get AuthService instance."""
    from src.services.auth_service import auth_service
    return auth_service


def get_github_service() -> GitHubService:
    """Get GitHubService instance."""
    from src.services.github_service import github_service
    return github_service


def get_mcp_key_service() -> McpKeyService:
    """Get McpKeyService instance."""
    from src.services.mcp_key_service import mcp_key_service
    return mcp_key_service


# Type aliases for service dependencies
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
FeatureServiceDep = Annotated[FeatureService, Depends(get_feature_service)]
TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]
ElementServiceDep = Annotated[ElementService, Depends(get_element_service)]
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
IdeaServiceDep = Annotated[IdeaService, Depends(get_idea_service)]
TeamServiceDep = Annotated[type[TeamService], Depends(get_team_service)]
InvitationServiceDep = Annotated[InvitationService, Depends(get_invitation_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
GitHubServiceDep = Annotated[GitHubService, Depends(get_github_service)]
McpKeyServiceDep = Annotated[McpKeyService, Depends(get_mcp_key_service)]
