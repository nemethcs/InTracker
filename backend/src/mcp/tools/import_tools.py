"""MCP Tools for project import and structure generation - refactored into smaller modules.

This module re-exports functions from:
- import_file_structure: File structure parsing
- import_github_issues: GitHub issues import
- import_github_milestones: GitHub milestones import
- import_codebase_analysis: Codebase analysis
"""

# Re-export from import_file_structure
from .import_file_structure import (
    get_parse_file_structure_tool,
    handle_parse_file_structure,
)

# Re-export from import_github_issues
from .import_github_issues import (
    get_import_github_issues_tool,
    handle_import_github_issues,
)

# Re-export from import_github_milestones
from .import_github_milestones import (
    get_import_github_milestones_tool,
    handle_import_github_milestones,
)

# Re-export from import_codebase_analysis
from .import_codebase_analysis import (
    get_analyze_codebase_tool,
    handle_analyze_codebase,
)

__all__ = [
    # File structure
    "get_parse_file_structure_tool",
    "handle_parse_file_structure",
    # GitHub issues
    "get_import_github_issues_tool",
    "handle_import_github_issues",
    # GitHub milestones
    "get_import_github_milestones_tool",
    "handle_import_github_milestones",
    # Codebase analysis
    "get_analyze_codebase_tool",
    "handle_analyze_codebase",
]
