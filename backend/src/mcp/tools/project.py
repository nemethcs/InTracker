"""MCP Tools for project management - refactored into smaller modules.

This module re-exports functions from:
- project_context: Context retrieval tools
- project_crud: CRUD operations
- project_workflow: Workflow and cursor rules
"""

# Re-export from project_context
from .project_context import (
    get_project_context_tool,
    handle_get_project_context,
    get_resume_context_tool,
    handle_get_resume_context,
    get_project_structure_tool,
    build_element_tree,
    handle_get_project_structure,
    get_active_todos_tool,
    handle_get_active_todos,
)

# Re-export from project_crud
from .project_crud import (
    get_create_project_tool,
    handle_create_project,
    get_list_projects_tool,
    handle_list_projects,
    get_update_project_tool,
    handle_update_project,
    get_identify_project_by_path_tool,
    handle_identify_project_by_path,
)

# Re-export from project_workflow
from .project_workflow import (
    get_load_cursor_rules_tool,
    handle_load_cursor_rules,
    get_enforce_workflow_tool,
    handle_enforce_workflow,
)

__all__ = [
    # Context tools
    "get_project_context_tool",
    "handle_get_project_context",
    "get_resume_context_tool",
    "handle_get_resume_context",
    "get_project_structure_tool",
    "build_element_tree",
    "handle_get_project_structure",
    "get_active_todos_tool",
    "handle_get_active_todos",
    # CRUD tools
    "get_create_project_tool",
    "handle_create_project",
    "get_list_projects_tool",
    "handle_list_projects",
    "get_update_project_tool",
    "handle_update_project",
    "get_identify_project_by_path_tool",
    "handle_identify_project_by_path",
    # Workflow tools
    "get_load_cursor_rules_tool",
    "handle_load_cursor_rules",
    "get_enforce_workflow_tool",
    "handle_enforce_workflow",
]
