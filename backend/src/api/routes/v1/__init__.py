"""API v1 routes."""
from fastapi import APIRouter
from src.api.controllers import (
    auth_controller,
    project_controller,
    feature_controller,
    todo_controller,
    element_controller,
    session_controller,
    document_controller,
    github_controller,
    idea_controller,
    signalr_controller,
    mcp_controller,
    admin_controller,
    team_controller,
    mcp_key_controller,
    audit_controller,
    task_queue_controller,
)

# Create v1 API router
v1_router = APIRouter(prefix="/v1", tags=["v1"])

# Include all controllers (they will be accessible at /v1/{controller_prefix})
v1_router.include_router(auth_controller.router)
v1_router.include_router(project_controller.router)
v1_router.include_router(feature_controller.router)
v1_router.include_router(todo_controller.router)
v1_router.include_router(element_controller.router)
v1_router.include_router(session_controller.router)
v1_router.include_router(document_controller.router)
v1_router.include_router(github_controller.router)
v1_router.include_router(idea_controller.router)
v1_router.include_router(signalr_controller.router)
v1_router.include_router(mcp_controller.router)
v1_router.include_router(admin_controller.router)
v1_router.include_router(team_controller.router)
v1_router.include_router(mcp_key_controller.router)
v1_router.include_router(audit_controller.router)
v1_router.include_router(task_queue_controller.router)

__all__ = ["v1_router"]
