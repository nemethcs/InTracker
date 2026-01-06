"""MCP Resources for projects."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.models import Project


def get_project_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get project resources."""
    db = get_db_session()
    try:
        if project_id:
            project = db.query(Project).filter(Project.id == UUID(project_id)).first()
            if project:
                return [
                    Resource(
                        uri=f"intracker://project/{project.id}",
                        name=f"Project: {project.name}",
                        description=project.description or "",
                        mimeType="application/json",
                    )
                ]
            return []
        else:
            # List all projects
            projects = db.query(Project).all()
            return [
                Resource(
                    uri=f"intracker://project/{p.id}",
                    name=f"Project: {p.name}",
                    description=p.description or "",
                    mimeType="application/json",
                )
                for p in projects
            ]
    finally:
        db.close()


async def read_project_resource(uri: str) -> str:
    """Read project resource."""
    # Parse URI: intracker://project/{project_id}
    if not uri.startswith("intracker://project/"):
        raise ValueError(f"Invalid project resource URI: {uri}")

    project_id = uri.replace("intracker://project/", "")
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        import json
        return json.dumps({
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "cursor_instructions": project.cursor_instructions,
            "resume_context": project.resume_context,
        }, indent=2)
    finally:
        db.close()
