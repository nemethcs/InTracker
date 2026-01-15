"""Document tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import document


async def handle_document_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle document tool calls."""
    try:
        if name == "mcp_get_document":
            result = await document.handle_get_document(arguments["documentId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_documents":
            result = await document.handle_list_documents(
                arguments["projectId"],
                arguments.get("type"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_create_document":
            result = await document.handle_create_document(
                arguments["projectId"],
                arguments["type"],
                arguments["title"],
                arguments["content"],
                arguments.get("elementId"),
                arguments.get("todoId"),
                arguments.get("tags"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
