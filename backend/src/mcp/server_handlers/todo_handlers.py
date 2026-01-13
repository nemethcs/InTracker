"""Todo tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import todo


async def handle_todo_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle todo tool calls."""
    try:
        if name == "mcp_create_todo":
            result = await todo.handle_create_todo(
                arguments["elementId"],
                arguments["title"],
                arguments.get("description"),
                arguments.get("featureId"),
                arguments.get("priority", "medium"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_update_todo_status":
            result = await todo.handle_update_todo_status(
                arguments["todoId"],
                arguments["status"],
                arguments.get("expectedVersion"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_todos":
            result = await todo.handle_list_todos(
                arguments["projectId"],
                arguments.get("status"),
                arguments.get("featureId"),
                arguments.get("userId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_assign_todo":
            result = await todo.handle_assign_todo(
                arguments["todoId"],
                arguments.get("userId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_link_todo_to_feature":
            result = await todo.handle_link_todo_to_feature(
                arguments["todoId"],
                arguments.get("featureId"),
                arguments.get("expectedVersion"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_delete_todo":
            result = await todo.handle_delete_todo(
                arguments["todoId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
