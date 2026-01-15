"""MCP Resources for features."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.services.feature_service import FeatureService


def get_feature_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get feature resources.
    
    PERFORMANCE OPTIMIZATION: Returns empty list to speed up MCP initialization.
    Resources are accessed dynamically via read_resource() when needed.
    This prevents slow database queries during initial connection.
    """
    # Return empty list for fast initialization
    # Resources will be loaded dynamically when accessed via read_resource()
    return []


async def read_feature_resource(uri: str) -> str:
    """Read feature resource."""
    # Convert URI to string (MCP SDK may pass AnyUrl object)
    uri_str = str(uri)
    
    # Parse URI: intracker://feature/{feature_id}
    if not uri_str.startswith("intracker://feature/"):
        raise ValueError(f"Invalid feature resource URI: {uri_str}")

    feature_id = uri_str.replace("intracker://feature/", "")
    db = SessionLocal()
    try:
        # Use FeatureService to get feature
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            raise ValueError(f"Feature not found: {feature_id}")

        # Use FeatureService to get todos
        todos = FeatureService.get_feature_todos(db, UUID(feature_id))

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
