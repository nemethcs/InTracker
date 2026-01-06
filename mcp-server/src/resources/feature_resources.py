"""MCP Resources for features."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.models import Feature, Project


def get_feature_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get feature resources."""
    db = get_db_session()
    try:
        if project_id:
            features = db.query(Feature).filter(Feature.project_id == UUID(project_id)).all()
            return [
                Resource(
                    uri=f"intracker://feature/{f.id}",
                    name=f"Feature: {f.name}",
                    description=f"{f.description or ''} ({f.progress_percentage}% complete)",
                    mimeType="application/json",
                )
                for f in features
            ]
        else:
            # List all features
            features = db.query(Feature).all()
            return [
                Resource(
                    uri=f"intracker://feature/{f.id}",
                    name=f"Feature: {f.name}",
                    description=f"{f.description or ''} ({f.progress_percentage}% complete)",
                    mimeType="application/json",
                )
                for f in features
            ]
    finally:
        db.close()


async def read_feature_resource(uri: str) -> str:
    """Read feature resource."""
    # Parse URI: intracker://feature/{feature_id}
    if not uri.startswith("intracker://feature/"):
        raise ValueError(f"Invalid feature resource URI: {uri}")

    feature_id = uri.replace("intracker://feature/", "")
    db = get_db_session()
    try:
        feature = db.query(Feature).filter(Feature.id == UUID(feature_id)).first()
        if not feature:
            raise ValueError(f"Feature not found: {feature_id}")

        # Get todos
        from src.models import Todo
        todos = db.query(Todo).filter(Todo.feature_id == UUID(feature_id)).all()

        import json
        return json.dumps({
            "id": str(feature.id),
            "name": feature.name,
            "description": feature.description,
            "status": feature.status,
            "progress_percentage": feature.progress_percentage,
            "total_todos": feature.total_todos,
            "completed_todos": feature.completed_todos,
            "todos": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                }
                for t in todos
            ],
        }, indent=2)
    finally:
        db.close()
