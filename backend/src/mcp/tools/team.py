"""MCP Tools for team management."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.middleware.auth import get_current_user_id
from src.services.team_service import TeamService
from src.database.models import Team, TeamMember, User


def get_list_teams_tool() -> MCPTool:
    """Get list teams tool definition."""
    return MCPTool(
        name="mcp_list_teams",
        description="List teams. Returns teams where the current user is a member, or all teams if user is admin.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


async def handle_list_teams() -> dict:
    """Handle list teams request."""
    db = SessionLocal()
    try:
        # Get current user ID from MCP API key
        user_id = get_current_user_id()
        
        # Get user to check if admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "teams": [],
                "total": 0,
                "message": "User not found"
            }
        
        # If admin, get all teams. Otherwise, get only teams where user is a member
        if user.role == "admin":
            teams, total = TeamService.list_teams(db, user_id=None)
        else:
            teams, total = TeamService.list_teams(db, user_id=user_id)
        
        return {
            "teams": [
                {
                    "id": str(team.id),
                    "name": team.name,
                    "description": team.description,
                    "language": team.language,
                    "created_at": team.created_at.isoformat() if team.created_at else None,
                    "created_by": str(team.created_by) if team.created_by else None,
                }
                for team in teams
            ],
            "total": total,
        }
    finally:
        db.close()


def get_get_team_tool() -> MCPTool:
    """Get team tool definition."""
    return MCPTool(
        name="mcp_get_team",
        description="Get team details by ID. Returns team information including members.",
        inputSchema={
            "type": "object",
            "properties": {
                "teamId": {
                    "type": "string",
                    "description": "Team UUID",
                },
            },
            "required": ["teamId"],
        },
    )


async def handle_get_team(team_id: str) -> dict:
    """Handle get team request."""
    db = SessionLocal()
    try:
        # Get current user ID from MCP API key
        user_id = get_current_user_id()
        
        # Get user to check if admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "error": "User not found"
            }
        
        # Get team
        team = TeamService.get_team_by_id(db, UUID(team_id))
        if not team:
            return {
                "error": f"Team {team_id} not found"
            }
        
        # Check if user has access to this team (admin or team member)
        if user.role != "admin" and not TeamService.is_team_member(db, UUID(team_id), user_id):
            return {
                "error": "You are not a member of this team"
            }
        
        # Get team members
        members = TeamService.get_team_members_with_users(db, UUID(team_id))
        
        return {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "language": team.language,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "created_by": str(team.created_by) if team.created_by else None,
            "members": [
                {
                    "user_id": str(member.user_id),
                    "email": user.email,
                    "name": user.name,
                    "role": member.role,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                }
                for member, user in members
            ],
        }
    finally:
        db.close()
