"""MCP Tools for GitHub integration."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.models import Project, GitHubBranch


def get_get_branches_tool() -> MCPTool:
    """Get branches tool definition."""
    return MCPTool(
        name="mcp_get_branches",
        description="Get branches for a project or feature",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "featureId": {"type": "string", "description": "Optional feature UUID"},
            },
            "required": ["projectId"],
        },
    )


async def handle_get_branches(project_id: str, feature_id: Optional[str] = None) -> dict:
    """Handle get branches tool call."""
    db = get_db_session()
    try:
        query = db.query(GitHubBranch).filter(GitHubBranch.project_id == UUID(project_id))
        if feature_id:
            query = query.filter(GitHubBranch.feature_id == UUID(feature_id))

        branches = query.order_by(GitHubBranch.created_at.desc()).all()

        return {
            "project_id": project_id,
            "branches": [
                {
                    "id": str(b.id),
                    "name": b.branch_name,
                    "status": b.status,
                    "feature_id": str(b.feature_id) if b.feature_id else None,
                }
                for b in branches
            ],
            "count": len(branches),
        }
    finally:
        db.close()
