"""MCP Server for InTracker."""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent
from src.config import settings
from src.mcp.tools import (
    project,
    feature,
    todo,
    session,
    document,
    github,
    idea,
    import_tools,
    onboarding,
    team,
)
from src.mcp.server_handlers.tool_router import tool_router
# Pre-import resources to ensure they're available at initialization
from src.mcp.resources import project_resources, feature_resources, document_resources

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
        # project.get_project_structure_tool(),  # REMOVED: Redundant - already in get_project_context
        project.get_active_todos_tool(),
        project.get_create_project_tool(),
        project.get_list_projects_tool(),
        project.get_update_project_tool(),
        project.get_identify_project_by_path_tool(),
        project.get_load_cursor_rules_tool(),
        project.get_enforce_workflow_tool(),
        # Feature tools
        feature.get_create_feature_tool(),
        feature.get_get_feature_tool(),
        feature.get_list_features_tool(),
        feature.get_update_feature_status_tool(),
        # feature.get_get_feature_todos_tool(),  # REMOVED: Redundant - already in get_feature
        # feature.get_get_feature_elements_tool(),  # REMOVED: Redundant - already in get_feature
        feature.get_link_element_to_feature_tool(),
        feature.get_delete_feature_tool(),
        # Todo tools
        todo.get_create_todo_tool(),
        todo.get_update_todo_status_tool(),
        todo.get_list_todos_tool(),
        todo.get_assign_todo_tool(),
        todo.get_link_todo_to_feature_tool(),
        todo.get_delete_todo_tool(),
        # Session tools
        session.get_start_session_tool(),
        session.get_update_session_tool(),
        session.get_end_session_tool(),
        # Document tools
        document.get_get_document_tool(),
        document.get_list_documents_tool(),
        document.get_create_document_tool(),
        # GitHub tools
        github.get_connect_github_repo_tool(),
        github.get_get_repo_info_tool(),
        github.get_get_branch_info_tool(),  # Consolidated tool (replaces get_branches, get_feature_branches, get_branch_status, get_commits_for_feature)
        github.get_link_element_to_issue_tool(),
        github.get_get_github_issue_tool(),
        github.get_create_github_issue_tool(),
        github.get_link_todo_to_pr_tool(),
        github.get_get_github_pr_tool(),
        github.get_create_github_pr_tool(),
        github.get_create_branch_for_feature_tool(),
        github.get_link_branch_to_feature_tool(),
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
        # Onboarding tools
        onboarding.get_verify_connection_tool(),
        # Team tools
        team.get_list_teams_tool(),
        team.get_get_team_tool(),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls using centralized router."""
    return await tool_router.route_tool(name, arguments)


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List all available resources."""
    resources = []
    
    # Get project resources (already imported at module level)
    resources.extend(project_resources.get_project_resources())
    
    # Get feature resources (already imported at module level)
    resources.extend(feature_resources.get_feature_resources())
    
    # Get document resources (already imported at module level)
    resources.extend(document_resources.get_document_resources())
    
    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
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
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
