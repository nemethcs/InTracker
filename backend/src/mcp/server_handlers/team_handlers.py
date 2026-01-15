"""Team tool handlers for MCP server."""
import json
from mcp.types import TextContent
from src.mcp.tools import team


async def handle_team_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle team-related tool calls."""
    
    if name == "mcp_list_teams":
        result = await team.handle_list_teams()
        return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]
    
    elif name == "mcp_get_team":
        result = await team.handle_get_team(arguments["teamId"])
        return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]
    
    return None
