"""Session tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import session


async def handle_session_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle session tool calls."""
    try:
        if name == "mcp_start_session":
            result = await session.handle_start_session(
                arguments["projectId"],
                arguments.get("goal"),
                arguments.get("featureIds"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_update_session":
            result = await session.handle_update_session(
                arguments["sessionId"],
                arguments.get("completedTodos"),
                arguments.get("completedFeatures"),
                arguments.get("notes"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_end_session":
            result = await session.handle_end_session(
                arguments["sessionId"],
                arguments.get("summary"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
