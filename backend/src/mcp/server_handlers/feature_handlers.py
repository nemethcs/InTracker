"""Feature tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import feature


async def handle_feature_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle feature tool calls."""
    try:
        if name == "mcp_create_feature":
            result = await feature.handle_create_feature(
                arguments["projectId"],
                arguments["name"],
                arguments.get("description"),
                arguments.get("elementIds"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_feature":
            result = await feature.handle_get_feature(arguments["featureId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_features":
            result = await feature.handle_list_features(
                arguments["projectId"],
                arguments.get("status"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_update_feature_status":
            result = await feature.handle_update_feature_status(
                arguments["featureId"],
                arguments["status"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # REMOVED: mcp_get_feature_todos - Redundant, already in mcp_get_feature
        # elif name == "mcp_get_feature_todos":
        #     result = await feature.handle_get_feature_todos(arguments["featureId"])
        #     return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # REMOVED: mcp_get_feature_elements - Redundant, already in mcp_get_feature
        # elif name == "mcp_get_feature_elements":
        #     result = await feature.handle_get_feature_elements(arguments["featureId"])
        #     return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_link_element_to_feature":
            result = await feature.handle_link_element_to_feature(
                arguments["featureId"],
                arguments["elementId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_delete_feature":
            result = await feature.handle_delete_feature(arguments["featureId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
