"""MCP Tools for idea management."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.idea_service import IdeaService
from src.services.project_service import ProjectService
from src.database.models import User


def get_create_idea_tool() -> MCPTool:
    """Get create idea tool definition."""
    return MCPTool(
        name="mcp_create_idea",
        description="Create a new idea",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Idea title"},
                "description": {"type": "string", "description": "Idea description"},
                "status": {
                    "type": "string",
                    "enum": ["draft", "active", "archived"],
                    "description": "Idea status",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Idea tags",
                },
            },
            "required": ["title"],
        },
    )


async def handle_create_idea(
    title: str,
    description: Optional[str] = None,
    status: str = "draft",
    tags: Optional[List[str]] = None,
) -> dict:
    """Handle create idea tool call."""
    db = SessionLocal()
    try:
        # Use IdeaService to create idea
        idea = IdeaService.create_idea(
            db=db,
            title=title,
            description=description,
            status=status,
            tags=tags,
        )

        # Invalidate cache
        cache_service.clear_pattern("ideas:*")

        return {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "status": idea.status,
            "tags": idea.tags,
            "converted_to_project_id": str(idea.converted_to_project_id) if idea.converted_to_project_id else None,
        }
    finally:
        db.close()


def get_list_ideas_tool() -> MCPTool:
    """Get list ideas tool definition."""
    return MCPTool(
        name="mcp_list_ideas",
        description="List ideas with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["draft", "active", "archived"],
                    "description": "Filter by status",
                },
            },
        },
    )


async def handle_list_ideas(status: Optional[str] = None) -> dict:
    """Handle list ideas tool call."""
    cache_key = f"ideas:list"
    if status:
        cache_key += f":status:{status}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use IdeaService to get ideas
        ideas, _ = IdeaService.get_ideas(
            db=db,
            status=status,
            skip=0,
            limit=1000,  # Large limit for MCP tools
        )

        result = {
            "ideas": [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "description": i.description,
                    "status": i.status,
                    "tags": i.tags,
                    "converted_to_project_id": str(i.converted_to_project_id) if i.converted_to_project_id else None,
                    "created_at": i.created_at.isoformat(),
                    "updated_at": i.updated_at.isoformat(),
                }
                for i in ideas
            ],
            "count": len(ideas),
        }

        cache_service.set(cache_key, result, ttl=120)  # 2 min TTL
        return result
    finally:
        db.close()


def get_get_idea_tool() -> MCPTool:
    """Get idea tool definition."""
    return MCPTool(
        name="mcp_get_idea",
        description="Get idea by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "ideaId": {"type": "string", "description": "Idea UUID"},
            },
            "required": ["ideaId"],
        },
    )


async def handle_get_idea(idea_id: str) -> dict:
    """Handle get idea tool call."""
    cache_key = f"idea:{idea_id}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use IdeaService to get idea
        idea = IdeaService.get_idea_by_id(db, UUID(idea_id))
        if not idea:
            return {"error": "Idea not found"}

        result = {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "status": idea.status,
            "tags": idea.tags,
            "converted_to_project_id": str(idea.converted_to_project_id) if idea.converted_to_project_id else None,
            "created_at": idea.created_at.isoformat(),
            "updated_at": idea.updated_at.isoformat(),
        }

        # Get converted project if exists using ProjectService
        if idea.converted_to_project_id:
            project = ProjectService.get_project_by_id(db, idea.converted_to_project_id)
            if project:
                result["converted_project"] = {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                }

        cache_service.set(cache_key, result, ttl=300)  # 5 min TTL
        return result
    finally:
        db.close()


def get_update_idea_tool() -> MCPTool:
    """Get update idea tool definition."""
    return MCPTool(
        name="mcp_update_idea",
        description="Update idea",
        inputSchema={
            "type": "object",
            "properties": {
                "ideaId": {"type": "string", "description": "Idea UUID"},
                "title": {"type": "string", "description": "Idea title"},
                "description": {"type": "string", "description": "Idea description"},
                "status": {
                    "type": "string",
                    "enum": ["draft", "active", "archived"],
                    "description": "Idea status",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Idea tags",
                },
            },
            "required": ["ideaId"],
        },
    )


async def handle_update_idea(
    idea_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    """Handle update idea tool call."""
    db = SessionLocal()
    try:
        # Use IdeaService to update idea
        idea = IdeaService.update_idea(
            db=db,
            idea_id=UUID(idea_id),
            title=title,
            description=description,
            status=status,
            tags=tags,
        )
        
        if not idea:
            return {"error": "Idea not found"}

        # Invalidate cache
        cache_service.delete(f"idea:{idea_id}")
        cache_service.clear_pattern("ideas:*")

        return {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "status": idea.status,
            "tags": idea.tags,
            "converted_to_project_id": str(idea.converted_to_project_id) if idea.converted_to_project_id else None,
        }
    finally:
        db.close()


def get_convert_idea_to_project_tool() -> MCPTool:
    """Get convert idea to project tool definition."""
    return MCPTool(
        name="mcp_convert_idea_to_project",
        description="Convert idea to project",
        inputSchema={
            "type": "object",
            "properties": {
                "ideaId": {"type": "string", "description": "Idea UUID"},
                "projectName": {"type": "string", "description": "Project name (optional, defaults to idea title)"},
                "projectDescription": {"type": "string", "description": "Project description (optional, defaults to idea description)"},
                "projectStatus": {
                    "type": "string",
                    "enum": ["active", "paused", "blocked", "completed", "archived"],
                    "description": "Project status",
                },
                "projectTags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Project tags (optional, defaults to idea tags)",
                },
                "technologyTags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Technology tags",
                },
            },
            "required": ["ideaId"],
        },
    )


async def handle_convert_idea_to_project(
    idea_id: str,
    project_name: Optional[str] = None,
    project_description: Optional[str] = None,
    project_status: str = "active",
    project_tags: Optional[List[str]] = None,
    technology_tags: Optional[List[str]] = None,
) -> dict:
    """Handle convert idea to project tool call."""
    db = SessionLocal()
    try:
        # Get first available user (for MCP context, we need a user)
        # In a real scenario, this would come from the MCP context/authentication
        user = db.query(User).first()
        if not user:
            return {"error": "No user available for project creation"}

        # Use IdeaService to convert idea to project
        project = IdeaService.convert_idea_to_project(
            db=db,
            idea_id=UUID(idea_id),
            user_id=user.id,
            project_name=project_name,
            project_description=project_description,
            project_status=project_status,
            project_tags=project_tags,
            technology_tags=technology_tags,
        )
        
        if not project:
            # Check if idea exists
            idea = IdeaService.get_idea_by_id(db, UUID(idea_id))
            if not idea:
                return {"error": "Idea not found"}
            # Idea exists but conversion failed - might be already converted
            if idea.converted_to_project_id:
                existing_project = ProjectService.get_project_by_id(db, idea.converted_to_project_id)
                if existing_project:
                    return {
                        "id": str(existing_project.id),
                        "name": existing_project.name,
                        "description": existing_project.description,
                        "status": existing_project.status,
                        "message": "Idea was already converted to this project",
                    }
            return {"error": "Failed to convert idea to project"}

        # Invalidate cache
        cache_service.delete(f"idea:{idea_id}")
        cache_service.clear_pattern("ideas:*")
        cache_service.clear_pattern(f"project:{project.id}:*")

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "idea_id": str(idea.id),
            "message": "Idea successfully converted to project",
        }
    finally:
        db.close()
