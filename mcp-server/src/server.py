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
    idea,
    import_tools,
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
        project.get_create_project_tool(),
        project.get_list_projects_tool(),
        project.get_update_project_tool(),
        project.get_identify_project_by_path_tool(),
        project.get_load_cursor_rules_tool(),
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
        document.get_create_document_tool(),
        # GitHub tools
        github.get_get_branches_tool(),
        github.get_connect_github_repo_tool(),
        github.get_get_repo_info_tool(),
        github.get_link_element_to_issue_tool(),
        github.get_get_github_issue_tool(),
        github.get_create_github_issue_tool(),
        github.get_link_todo_to_pr_tool(),
        github.get_get_github_pr_tool(),
        github.get_create_github_pr_tool(),
        github.get_create_branch_for_feature_tool(),
        github.get_get_active_branch_tool(),
        github.get_link_branch_to_feature_tool(),
        github.get_get_feature_branches_tool(),
        github.get_get_branch_status_tool(),
        github.get_get_commits_for_feature_tool(),
        github.get_parse_commit_message_tool(),
        # Idea tools
        idea.get_create_idea_tool(),
        idea.get_list_ideas_tool(),
        idea.get_get_idea_tool(),
        idea.get_update_idea_tool(),
        idea.get_convert_idea_to_project_tool(),
        # Import tools
        import_tools.get_parse_file_structure_tool(),
        import_tools.get_import_github_issues_tool(),
        import_tools.get_import_github_milestones_tool(),
        import_tools.get_analyze_codebase_tool(),
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
            result = await project.handle_get_resume_context(
                arguments["projectId"],
                arguments.get("userId"),
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
            result = await project.handle_identify_project_by_path(
                arguments.get("path"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_load_cursor_rules":
            result = await project.handle_load_cursor_rules(
                arguments["projectId"],
                arguments.get("projectPath"),
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

        # GitHub tools
        elif name == "mcp_get_branches":
            result = await github.handle_get_branches(
                arguments["projectId"],
                arguments.get("featureId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_connect_github_repo":
            result = await github.handle_connect_github_repo(
                arguments["projectId"],
                arguments["owner"],
                arguments["repo"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_repo_info":
            result = await github.handle_get_repo_info(
                arguments["projectId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_link_element_to_issue":
            result = await github.handle_link_element_to_issue(
                arguments["elementId"],
                arguments["issueNumber"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_github_issue":
            result = await github.handle_get_github_issue(
                arguments["projectId"],
                arguments["issueNumber"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_create_github_issue":
            result = await github.handle_create_github_issue(
                arguments["projectId"],
                arguments["title"],
                arguments.get("body"),
                arguments.get("labels"),
                arguments.get("elementId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_link_todo_to_pr":
            result = await github.handle_link_todo_to_pr(
                arguments["todoId"],
                arguments["prNumber"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_github_pr":
            result = await github.handle_get_github_pr(
                arguments["projectId"],
                arguments["prNumber"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_create_github_pr":
            result = await github.handle_create_github_pr(
                arguments["projectId"],
                arguments["title"],
                arguments["head"],
                arguments.get("body"),
                arguments.get("base", "main"),
                arguments.get("todoId"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_create_branch_for_feature":
            result = await github.handle_create_branch_for_feature(
                arguments["featureId"],
                arguments.get("baseBranch", "main"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_active_branch":
            result = await github.handle_get_active_branch(
                arguments["projectId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_link_branch_to_feature":
            result = await github.handle_link_branch_to_feature(
                arguments["featureId"],
                arguments["branchName"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_feature_branches":
            result = await github.handle_get_feature_branches(
                arguments["featureId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_branch_status":
            result = await github.handle_get_branch_status(
                arguments["projectId"],
                arguments["branchName"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_get_commits_for_feature":
            result = await github.handle_get_commits_for_feature(
                arguments["featureId"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_parse_commit_message":
            result = await github.handle_parse_commit_message(
                arguments["commitMessage"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        # Idea tools
        elif name == "mcp_create_idea":
            result = await idea.handle_create_idea(
                arguments["title"],
                arguments.get("description"),
                arguments.get("status", "draft"),
                arguments.get("tags"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_list_ideas":
            result = await idea.handle_list_ideas(
                arguments.get("status"),
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

        # Import tools
        elif name == "mcp_parse_file_structure":
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
    
    # Convert URI to string (MCP SDK may pass AnyUrl object)
    uri_str = str(uri)
    
    if uri_str.startswith("intracker://project/"):
        return await project_resources.read_project_resource(uri_str)
    elif uri_str.startswith("intracker://feature/"):
        return await feature_resources.read_feature_resource(uri_str)
    elif uri_str.startswith("intracker://document/"):
        return await document_resources.read_document_resource(uri_str)
    else:
        raise ValueError(f"Unknown resource URI: {uri_str}")


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
