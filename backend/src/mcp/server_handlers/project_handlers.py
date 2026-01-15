"""Project tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import project


async def handle_project_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle project tool calls."""
    # Convert string booleans/integers to proper types (JSON may send them as strings)
    def to_bool(val, default):
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)
    
    def to_int(val, default):
        if val is None:
            return default
        if isinstance(val, int):
            return val
        if isinstance(val, str):
            try:
                return int(val)
            except ValueError:
                return default
        return default
    
    try:
        if name == "mcp_get_project_context":
            result = await project.handle_get_project_context(
                arguments["projectId"],
                include_features=to_bool(arguments.get("includeFeatures"), True),
                include_todos=to_bool(arguments.get("includeTodos"), True),
                include_structure=to_bool(arguments.get("includeStructure"), True),
                include_resume_context=to_bool(arguments.get("includeResumeContext"), True),
                features_limit=to_int(arguments.get("featuresLimit"), 20),
                todos_limit=to_int(arguments.get("todosLimit"), 50),
                summary_only=to_bool(arguments.get("summaryOnly"), False),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "mcp_get_resume_context":
            result = await project.handle_get_resume_context(
                arguments["projectId"],
                arguments.get("userId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_update_resume_context":
            result = await project.handle_update_resume_context(
                arguments["projectId"],
                arguments["resumeContext"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_project_structure":
            result = await project.handle_get_project_structure(arguments["projectId"])
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_active_todos":
            result = await project.handle_get_active_todos(
                arguments["projectId"],
                arguments.get("status"),
                arguments.get("featureId"),
                arguments.get("userId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_create_project":
            result = await project.handle_create_project(
                arguments["name"],
                arguments["teamId"],
                arguments.get("description"),
                arguments.get("status", "active"),
                arguments.get("tags"),
                arguments.get("technologyTags"),
                arguments.get("cursorInstructions"),
                arguments.get("githubRepoUrl"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_projects":
            result = await project.handle_list_projects(
                arguments.get("status"),
                arguments.get("userId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_update_project":
            result = await project.handle_update_project(
                arguments["projectId"],
                arguments.get("name"),
                arguments.get("description"),
                arguments.get("status"),
                arguments.get("tags"),
                arguments.get("technologyTags"),
                arguments.get("cursorInstructions"),
                arguments.get("githubRepoUrl"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_identify_project_by_path":
            # Path is required according to tool definition
            if "path" not in arguments:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Path parameter is required. In Docker environment, MCP server cannot access local file system without explicit path."
                }, indent=2))]
            result = await project.handle_identify_project_by_path(
                arguments["path"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_load_cursor_rules":
            result = await project.handle_load_cursor_rules(
                arguments["projectId"],
                arguments.get("projectPath"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_enforce_workflow":
            result = await project.handle_enforce_workflow(
                arguments.get("path"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
