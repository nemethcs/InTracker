"""Onboarding tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import onboarding


async def handle_onboarding_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle onboarding tool calls."""
    try:
        if name == "mcp_verify_connection":
            result = await onboarding.handle_verify_connection()
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
