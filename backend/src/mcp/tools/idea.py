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
        description="Create a new idea for a team",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Idea title"},
                "teamId": {"type": "string", "description": "Team UUID that will own this idea"},
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
            "required": ["title", "teamId"],
        },
    )


async def handle_create_idea(
    title: str,
    team_id: str,
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
            team_id=UUID(team_id),
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
            "team_id": str(idea.team_id),
            "tags": idea.tags,
            "converted_to_project_id": str(idea.converted_to_project_id) if idea.converted_to_project_id else None,
        }
    finally:
        db.close()


def get_list_ideas_tool() -> MCPTool:
    """Get list ideas tool definition."""
    return MCPTool(
        name="mcp_list_ideas",
        description="List ideas with optional filters. If userId is provided, returns ideas from teams where user is a member.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["draft", "active", "archived"],
                    "description": "Filter by status",
                },
                "userId": {
                    "type": "string",
                    "description": "Optional: User UUID to filter ideas by team membership",
                },
                "teamId": {
                    "type": "string",
                    "description": "Optional: Team UUID to filter ideas by team",
                },
            },
        },
    )


async def handle_list_ideas(status: Optional[str] = None, user_id: Optional[str] = None, team_id: Optional[str] = None) -> dict:
    """Handle list ideas tool call.
    
    If user_id is not provided, automatically extracts it from MCP API key if available.
    """
    from src.mcp.middleware.auth import get_current_user_id
    
    # Auto-extract user_id from MCP API key if not provided
    if not user_id:
        current_user_id = get_current_user_id()
        if current_user_id:
            user_id = str(current_user_id)
    
    cache_key = f"ideas:list"
    if status:
        cache_key += f":status:{status}"
    if user_id:
        cache_key += f":user:{user_id}"
    if team_id:
        cache_key += f":team:{team_id}"
    
    # Check cache
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = SessionLocal()
    try:
        # Use IdeaService to get ideas (with optional user_id and team_id filtering)
        ideas, _ = IdeaService.get_ideas(
            db=db,
            user_id=UUID(user_id) if user_id else None,
            team_id=UUID(team_id) if team_id else None,
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
                    "team_id": str(i.team_id),
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
            "team_id": str(idea.team_id),
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
    """Handle update idea tool call with validation."""
    db = SessionLocal()
    try:
        # Get idea first to check if it's already converted
        idea = IdeaService.get_idea_by_id(db, UUID(idea_id))
        if not idea:
            return {"error": "Idea not found"}
        
        # Validate: cannot update idea that has been converted to project
        if idea.converted_to_project_id:
            return {
                "error": f"Cannot update idea: idea has already been converted to project. "
                f"Project ID: {idea.converted_to_project_id}"
            }
        
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
            "team_id": str(idea.team_id),
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
    """Handle convert idea to project tool call with validation. The project will belong to the same team as the idea."""
    db = SessionLocal()
    try:
        # Get idea first to validate
        idea = IdeaService.get_idea_by_id(db, UUID(idea_id))
        if not idea:
            return {"error": "Idea not found"}
        
        # Validate: cannot convert idea that has already been converted
        if idea.converted_to_project_id:
            existing_project = ProjectService.get_project_by_id(db, idea.converted_to_project_id)
            if existing_project:
                return {
                    "id": str(existing_project.id),
                    "name": existing_project.name,
                    "description": existing_project.description,
                    "status": existing_project.status,
                    "team_id": str(existing_project.team_id),
                    "message": "Idea was already converted to this project",
                }
            return {
                "error": f"Cannot convert idea to project: idea has already been converted. "
                f"Project ID: {idea.converted_to_project_id}"
            }
        
        # Validate: idea should be 'active' or 'draft' status to convert
        if idea.status == "archived":
            return {
                "error": f"Cannot convert idea to project: idea is 'archived'. "
                f"Change idea status to 'active' or 'draft' before converting."
            }
        
        # Use IdeaService to convert idea to project (team_id comes from idea)
        project = IdeaService.convert_idea_to_project(
            db=db,
            idea_id=UUID(idea_id),
            project_name=project_name,
            project_description=project_description,
            project_status=project_status,
            project_tags=project_tags,
            technology_tags=technology_tags,
        )
        
        if not project:
            return {"error": "Failed to convert idea to project"}
                existing_project = ProjectService.get_project_by_id(db, idea.converted_to_project_id)
                if existing_project:
                    return {
                        "id": str(existing_project.id),
                        "name": existing_project.name,
                        "description": existing_project.description,
                        "status": existing_project.status,
                        "team_id": str(existing_project.team_id),
                        "message": "Idea was already converted to this project",
                    }
            return {"error": "Failed to convert idea to project"}

        # Get idea for response
        idea = IdeaService.get_idea_by_id(db, UUID(idea_id))

        # Invalidate cache
        cache_service.delete(f"idea:{idea_id}")
        cache_service.clear_pattern("ideas:*")
        cache_service.clear_pattern(f"project:{project.id}:*")

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "team_id": str(project.team_id),
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "idea_id": str(idea.id),
            "message": "Idea successfully converted to project",
        }
    finally:
        db.close()
