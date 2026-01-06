"""MCP Server for InTracker."""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent
from src.config import settings
from src.tools import (
    project,
    feature,
    todo,
    session,
    document,
    github,
)

# Create MCP server
server = Server("intracker-mcp-server")


# Register project tools
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        # Project tools
        project.get_project_context_tool(),
        project.get_resume_context_tool(),
        project.get_project_structure_tool(),
        project.get_active_todos_tool(),
        # Feature tools
        feature.get_create_feature_tool(),
        feature.get_get_feature_tool(),
        feature.get_list_features_tool(),
        feature.get_update_feature_status_tool(),
        feature.get_get_feature_todos_tool(),
        feature.get_get_feature_elements_tool(),
        feature.get_link_element_to_feature_tool(),
        # Todo tools
        todo.get_create_todo_tool(),
        todo.get_update_todo_status_tool(),
        todo.get_list_todos_tool(),
        todo.get_assign_todo_tool(),
        # Session tools
        session.get_start_session_tool(),
        session.get_update_session_tool(),
        session.get_end_session_tool(),
        # Document tools
        document.get_get_document_tool(),
        document.get_list_documents_tool(),
        # GitHub tools
        github.get_get_branches_tool(),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    from mcp.types import TextContent
    import json
    try:
        # Project tools
        if name == "mcp_get_project_context":
            result = await project.handle_get_project_context(arguments["projectId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "mcp_get_resume_context":
            result = await project.handle_get_resume_context(arguments["projectId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_project_structure":
            result = await project.handle_get_project_structure(arguments["projectId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_active_todos":
            result = await project.handle_get_active_todos(
                arguments["projectId"],
                arguments.get("status"),
                arguments.get("featureId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # Feature tools
        elif name == "mcp_create_feature":
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

        elif name == "mcp_get_feature_todos":
            result = await feature.handle_get_feature_todos(arguments["featureId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_feature_elements":
            result = await feature.handle_get_feature_elements(arguments["featureId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_link_element_to_feature":
            result = await feature.handle_link_element_to_feature(
                arguments["featureId"],
                arguments["elementId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # Todo tools
        elif name == "mcp_create_todo":
            result = await todo.handle_create_todo(
                arguments["elementId"],
                arguments["title"],
                arguments.get("description"),
                arguments.get("featureId"),
                arguments.get("estimatedEffort"),
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
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_assign_todo":
            result = await todo.handle_assign_todo(
                arguments["todoId"],
                arguments.get("userId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # Session tools
        elif name == "mcp_start_session":
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

        # Document tools
        elif name == "mcp_get_document":
            result = await document.handle_get_document(arguments["documentId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_documents":
            result = await document.handle_list_documents(
                arguments["projectId"],
                arguments.get("type"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # GitHub tools
        elif name == "mcp_get_branches":
            result = await github.handle_get_branches(
                arguments["projectId"],
                arguments.get("featureId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List all available resources."""
    from src.resources import project_resources, feature_resources, document_resources
    
    resources = []
    
    # Get project resources
    resources.extend(project_resources.get_project_resources())
    
    # Get feature resources
    resources.extend(feature_resources.get_feature_resources())
    
    # Get document resources
    resources.extend(document_resources.get_document_resources())
    
    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
    from src.resources import project_resources, feature_resources, document_resources
    
    if uri.startswith("intracker://project/"):
        return await project_resources.read_project_resource(uri)
    elif uri.startswith("intracker://feature/"):
        return await feature_resources.read_feature_resource(uri)
    elif uri.startswith("intracker://document/"):
        return await document_resources.read_document_resource(uri)
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


async def main():
    """Main entry point."""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        import sys
        print(f"Error in MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import sys
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
