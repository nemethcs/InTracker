"""Tool router for MCP server - routes tool calls to appropriate handlers."""
from typing import Callable, Optional
from mcp.types import TextContent
from src.mcp.server_handlers import (
    handle_project_tool,
    handle_feature_tool,
    handle_todo_tool,
    handle_session_tool,
    handle_document_tool,
    handle_github_tool,
    handle_idea_tool,
    handle_import_tool,
    handle_onboarding_tool,
    handle_team_tool,
)


class ToolRouter:
    """Routes tool calls to appropriate handlers based on tool name prefix."""
    
    # Map tool name prefixes to their handlers
    # Order matters - more specific prefixes should come first
    HANDLER_MAP: list[tuple[str, Callable]] = [
        # Project tools (most common, check first)
        ("mcp_get_project", handle_project_tool),
        ("mcp_get_resume", handle_project_tool),
        ("mcp_get_active_todos", handle_project_tool),
        ("mcp_create_project", handle_project_tool),
        ("mcp_list_projects", handle_project_tool),
        ("mcp_update_project", handle_project_tool),
        ("mcp_identify_project", handle_project_tool),
        ("mcp_load_cursor", handle_project_tool),
        ("mcp_enforce_workflow", handle_project_tool),
        # Feature tools
        ("mcp_create_feature", handle_feature_tool),
        ("mcp_get_feature", handle_feature_tool),
        ("mcp_list_features", handle_feature_tool),
        ("mcp_update_feature", handle_feature_tool),
        ("mcp_link_element_to_feature", handle_feature_tool),
        ("mcp_delete_feature", handle_feature_tool),
        # Todo tools
        ("mcp_create_todo", handle_todo_tool),
        ("mcp_update_todo", handle_todo_tool),
        ("mcp_list_todos", handle_todo_tool),
        ("mcp_assign_todo", handle_todo_tool),
        ("mcp_link_todo", handle_todo_tool),
        ("mcp_delete_todo", handle_todo_tool),
        # Session tools
        ("mcp_start_session", handle_session_tool),
        ("mcp_update_session", handle_session_tool),
        ("mcp_end_session", handle_session_tool),
        # Document tools
        ("mcp_get_document", handle_document_tool),
        ("mcp_list_documents", handle_document_tool),
        ("mcp_create_document", handle_document_tool),
        # GitHub tools
        ("mcp_connect_github", handle_github_tool),
        ("mcp_get_repo", handle_github_tool),
        ("mcp_get_branch_info", handle_github_tool),  # New consolidated tool
        ("mcp_get_branches", handle_github_tool),  # Deprecated but kept for compatibility
        ("mcp_link_element_to_issue", handle_github_tool),
        ("mcp_get_github_issue", handle_github_tool),
        ("mcp_create_github_issue", handle_github_tool),
        ("mcp_link_todo_to_pr", handle_github_tool),
        ("mcp_get_github_pr", handle_github_tool),
        ("mcp_create_github_pr", handle_github_tool),
        ("mcp_create_branch", handle_github_tool),
        ("mcp_link_branch", handle_github_tool),
        ("mcp_get_feature_branches", handle_github_tool),
        ("mcp_get_branch_status", handle_github_tool),
        ("mcp_get_commits", handle_github_tool),
        ("mcp_parse_commit", handle_github_tool),
        # Idea tools
        ("mcp_create_idea", handle_idea_tool),
        ("mcp_list_ideas", handle_idea_tool),
        ("mcp_get_idea", handle_idea_tool),
        ("mcp_update_idea", handle_idea_tool),
        ("mcp_convert_idea", handle_idea_tool),
        # Import tools
        ("mcp_parse_file", handle_import_tool),
        ("mcp_import_github_issues", handle_import_tool),
        ("mcp_import_github_milestones", handle_import_tool),
        ("mcp_analyze_codebase", handle_import_tool),
        # Onboarding tools
        ("mcp_verify_connection", handle_onboarding_tool),
        # Team tools
        ("mcp_list_teams", handle_team_tool),
        ("mcp_get_team", handle_team_tool),
    ]
    
    @classmethod
    async def route_tool(cls, name: str, arguments: dict) -> list[TextContent]:
        """Route tool call to appropriate handler.
        
        Args:
            name: Tool name (e.g., "mcp_get_project_context")
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
            
        Raises:
            ValueError if tool is unknown
        """
        # Find handler by matching tool name prefix
        for prefix, handler in cls.HANDLER_MAP:
            if name.startswith(prefix):
                result = await handler(name, arguments)
                if result is not None:
                    return result
        
        # If no handler found, try fallback: iterate through all handlers
        # This handles edge cases where prefix matching might miss a tool
        handlers = [
            handle_project_tool,
            handle_feature_tool,
            handle_todo_tool,
            handle_session_tool,
            handle_document_tool,
            handle_github_tool,
            handle_idea_tool,
            handle_import_tool,
            handle_onboarding_tool,
            handle_team_tool,
        ]
        
        for handler in handlers:
            result = await handler(name, arguments)
            if result is not None:
                return result
        
        # Unknown tool
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# Global router instance
tool_router = ToolRouter()
