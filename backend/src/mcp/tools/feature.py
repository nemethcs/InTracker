"""MCP Tools for feature management."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.signalr_hub import broadcast_feature_update
from src.services.feature_service import FeatureService
from src.services.todo_service import TodoService


def get_create_feature_tool() -> MCPTool:
    """Get create feature tool definition."""
    return MCPTool(
        name="mcp_create_feature",
        description="Create a new feature for a project. Features group related todos and track progress. Can optionally link existing project elements. The feature will be created with status 'new'.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "name": {"type": "string", "description": "Feature name"},
                "description": {"type": "string", "description": "Feature description"},
                "elementIds": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional element IDs to link",
                },
            },
            "required": ["projectId", "name"],
        },
    )


async def handle_create_feature(
    project_id: str,
    name: str,
    description: Optional[str] = None,
    element_ids: Optional[List[str]] = None,
) -> dict:
    """Handle create feature tool call."""
    db = SessionLocal()
    try:
        # Use FeatureService to create feature
        element_uuid_list = [UUID(eid) for eid in element_ids] if element_ids else None
        feature = FeatureService.create_feature(
            db=db,
            project_id=UUID(project_id),
            name=name,
            description=description,
            status="new",
            element_ids=element_uuid_list,
        )

        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        cache_service.delete(f"feature:{feature.id}")

        # Broadcast SignalR update (fire and forget)
        import asyncio
        asyncio.create_task(
            broadcast_feature_update(
                project_id,
                str(feature.id),
                feature.progress_percentage,
                feature.status
            )
        )

        return {
            "id": str(feature.id),
            "name": feature.name,
            "description": feature.description,
            "status": feature.status,
            "progress_percentage": feature.progress_percentage,
        }
    finally:
        db.close()


def get_get_feature_tool() -> MCPTool:
    """Get feature tool definition."""
    return MCPTool(
        name="mcp_get_feature",
        description="Get feature with todos and elements",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
            },
            "required": ["featureId"],
        },
    )


async def handle_get_feature(feature_id: str) -> dict:
    """Handle get feature tool call."""
    cache_key = f"feature:{feature_id}"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use FeatureService to get feature
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            return {"error": "Feature not found"}

        # Use FeatureService to get todos
        todos = FeatureService.get_feature_todos(db, UUID(feature_id))

        # Use FeatureService to get elements
        elements = FeatureService.get_feature_elements(db, UUID(feature_id))

        result = {
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
            "elements": [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "type": e.type,
                }
                for e in elements
            ],
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_list_features_tool() -> MCPTool:
    """Get list features tool definition."""
    return MCPTool(
        name="mcp_list_features",
        description="List features for a project with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "status": {
                    "type": "string",
                    "enum": ["new", "in_progress", "done", "tested", "merged"],
                    "description": "Filter by status",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_list_features(
    project_id: str,
    status: Optional[str] = None,
) -> dict:
    """Handle list features tool call."""
    cache_key = f"project:{project_id}:features"
    if status:
        cache_key += f":status:{status}"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use FeatureService to get features by project
        features, _ = FeatureService.get_features_by_project(
            db=db,
            project_id=UUID(project_id),
            status=status,
        )

        result = {
            "project_id": project_id,
            "features": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "description": f.description,
                    "status": f.status,
                    "progress_percentage": f.progress_percentage,
                    "total_todos": f.total_todos,
                    "completed_todos": f.completed_todos,
                }
                for f in features
            ],
            "count": len(features),
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_update_feature_status_tool() -> MCPTool:
    """Get update feature status tool definition."""
    return MCPTool(
        name="mcp_update_feature_status",
        description="Update a feature's status (new → in_progress → done → tested → merged) and automatically recalculate progress percentage based on linked todos. Progress is calculated as: (completed todos / total todos) * 100. Completed todos are those with status: done.",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
                "status": {
                    "type": "string",
                    "enum": ["new", "in_progress", "done", "tested", "merged"],
                    "description": "New status",
                },
            },
            "required": ["featureId", "status"],
        },
    )


async def handle_update_feature_status(feature_id: str, status: str) -> dict:
    """Handle update feature status tool call."""
    from src.mcp.utils.validation import validate_feature_status_transition, ValidationError
    
    db = SessionLocal()
    try:
        # Validate the status transition before updating
        try:
            validate_feature_status_transition(
                db=db,
                feature_id=UUID(feature_id),
                new_status=status,
                require_all_todos_done=True,
            )
        except ValidationError as e:
            return {"error": str(e)}

        # Use FeatureService to update feature status
        feature = FeatureService.update_feature(
            db=db,
            feature_id=UUID(feature_id),
            status=status,
        )
        
        if not feature:
            return {"error": "Feature not found"}

        # Use FeatureService to recalculate progress (this also auto-updates status based on todos)
        FeatureService.calculate_feature_progress(db, UUID(feature_id))
        
        # Refresh to get updated progress
        db.refresh(feature)

        # Invalidate cache
        cache_service.delete(f"feature:{feature_id}")
        cache_service.clear_pattern(f"project:{feature.project_id}:*")
        
        # Broadcast SignalR update (fire and forget)
        import asyncio
        asyncio.create_task(
            broadcast_feature_update(
                str(feature.project_id),
                str(feature_id),
                feature.progress_percentage,
                feature.status
            )
        )

        return {
            "id": str(feature.id),
            "status": feature.status,
            "progress_percentage": feature.progress_percentage,
        }
    finally:
        db.close()


def get_get_feature_todos_tool() -> MCPTool:
    """Get feature todos tool definition."""
    return MCPTool(
        name="mcp_get_feature_todos",
        description="Get todos for a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
            },
            "required": ["featureId"],
        },
    )


async def handle_get_feature_todos(feature_id: str) -> dict:
    """Handle get feature todos tool call."""
    cache_key = f"feature:{feature_id}:todos"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use FeatureService to get feature todos
        todos = FeatureService.get_feature_todos(db, UUID(feature_id))

        result = {
            "feature_id": feature_id,
            "todos": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "assigned_to": str(t.assigned_to) if t.assigned_to else None,
                }
                for t in todos
            ],
            "count": len(todos),
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_get_feature_elements_tool() -> MCPTool:
    """Get feature elements tool definition."""
    return MCPTool(
        name="mcp_get_feature_elements",
        description="Get elements linked to a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
            },
            "required": ["featureId"],
        },
    )


async def handle_get_feature_elements(feature_id: str) -> dict:
    """Handle get feature elements tool call."""
    cache_key = f"feature:{feature_id}:elements"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use FeatureService to get feature elements
        elements = FeatureService.get_feature_elements(db, UUID(feature_id))

        result = {
            "feature_id": feature_id,
            "elements": [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "type": e.type,
                    "status": e.status,
                }
                for e in elements
            ],
            "count": len(elements),
        }

        cache_service.set(cache_key, result, ttl=300)  # 5 min TTL
        return result
    finally:
        db.close()


def get_link_element_to_feature_tool() -> MCPTool:
    """Get link element to feature tool definition."""
    return MCPTool(
        name="mcp_link_element_to_feature",
        description="Link an element to a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
                "elementId": {"type": "string", "description": "Element UUID"},
            },
            "required": ["featureId", "elementId"],
        },
    )


async def handle_link_element_to_feature(feature_id: str, element_id: str) -> dict:
    """Handle link element to feature tool call."""
    db = SessionLocal()
    try:
        # Get feature before linking to get project_id
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            return {"error": "Feature not found"}
        
        # Use FeatureService to link element to feature
        success = FeatureService.link_element_to_feature(
            db=db,
            feature_id=UUID(feature_id),
            element_id=UUID(element_id),
        )
        
        if not success:
            return {"error": "Element already linked to feature"}

        # Refresh feature to get updated progress after linking element
        db.refresh(feature)
        updated_feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        
        # Invalidate cache
        cache_service.delete(f"feature:{feature_id}")
        cache_service.delete(f"feature:{feature_id}:elements")

        # Broadcast SignalR update (fire and forget) - element linked may affect progress
        if updated_feature:
            import asyncio
            asyncio.create_task(
                broadcast_feature_update(
                    str(updated_feature.project_id),
                    feature_id,
                    updated_feature.progress_percentage,
                    updated_feature.status
                )
            )

        return {"success": True, "message": "Element linked to feature"}
    finally:
        db.close()


def get_delete_feature_tool() -> MCPTool:
    """Get delete feature tool definition."""
    return MCPTool(
        name="mcp_delete_feature",
        description="Delete a feature. This will also delete all todos linked to the feature.",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID to delete"},
            },
            "required": ["featureId"],
        },
    )


async def handle_delete_feature(feature_id: str) -> dict:
    """Handle delete feature tool call."""
    db = SessionLocal()
    try:
        # Get feature before deletion for broadcast and cache invalidation
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            return {"error": "Feature not found"}
        
        project_id = feature.project_id
        
        # Delete feature using FeatureService
        success = FeatureService.delete_feature(db=db, feature_id=UUID(feature_id))
        if not success:
            return {"error": "Failed to delete feature"}

        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        cache_service.delete(f"feature:{feature_id}")

        # Broadcast SignalR update (fire and forget)
        import asyncio
        asyncio.create_task(
            broadcast_feature_update(
                str(project_id),
                str(feature_id),
                0,  # progress is 0 for deleted features
                "deleted"  # status indicates deletion
            )
        )

        return {
            "success": True,
            "deleted_feature_id": str(feature_id),
            "message": "Feature deleted successfully",
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()
