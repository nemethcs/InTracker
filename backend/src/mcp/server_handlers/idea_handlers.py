"""Idea tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import idea


async def handle_idea_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle idea tool calls."""
    try:
        if name == "mcp_create_idea":
            result = await idea.handle_create_idea(
                arguments["title"],
                arguments["teamId"],
                arguments.get("description"),
                arguments.get("status", "draft"),
                arguments.get("tags"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_ideas":
            result = await idea.handle_list_ideas(
                arguments.get("status"),
                arguments.get("userId"),
                arguments.get("teamId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_idea":
            result = await idea.handle_get_idea(arguments["ideaId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_update_idea":
            result = await idea.handle_update_idea(
                arguments["ideaId"],
                arguments.get("title"),
                arguments.get("description"),
                arguments.get("status"),
                arguments.get("tags"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_convert_idea_to_project":
            result = await idea.handle_convert_idea_to_project(
                arguments["ideaId"],
                arguments.get("projectName"),
                arguments.get("projectDescription"),
                arguments.get("projectStatus", "active"),
                arguments.get("projectTags"),
                arguments.get("technologyTags"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
