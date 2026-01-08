"""Import tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import import_tools


async def handle_import_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle import tool calls."""
    try:
        if name == "mcp_parse_file_structure":
            result = await import_tools.handle_parse_file_structure(
                arguments["projectId"],
                arguments.get("projectPath"),
                arguments.get("maxDepth", 3),
                arguments.get("ignorePatterns"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_import_github_issues":
            result = await import_tools.handle_import_github_issues(
                arguments["projectId"],
                arguments.get("labels"),
                arguments.get("state", "open"),
                arguments.get("createElements", True),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_import_github_milestones":
            result = await import_tools.handle_import_github_milestones(
                arguments["projectId"],
                arguments.get("state", "open"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_analyze_codebase":
            result = await import_tools.handle_analyze_codebase(
                arguments["projectId"],
                arguments.get("projectPath"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
