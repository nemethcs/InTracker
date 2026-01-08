"""MCP Tools for GitHub commits."""
import re
from mcp.types import Tool as MCPTool


def get_parse_commit_message_tool() -> MCPTool:
    """Get parse commit message tool definition."""
    return MCPTool(
        name="mcp_parse_commit_message",
        description="Parse commit message for metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "commitMessage": {"type": "string", "description": "Commit message"},
            },
            "required": ["commitMessage"],
        },
    )


async def handle_parse_commit_message(commit_message: str) -> dict:
    """Handle parse commit message tool call."""
    # Parse conventional commit format: "type(scope): description [feature:id]"
    pattern = r"^(\w+)(?:\(([^)]+)\))?:\s*(.+?)(?:\s*\[feature:([^\]]+)\])?$"
    match = re.match(pattern, commit_message.split("\n")[0])
    
    if match:
        commit_type, scope, description, feature_id = match.groups()
        return {
            "type": commit_type,
            "scope": scope,
            "description": description.strip(),
            "feature_id": feature_id,
            "format": "conventional",
        }
    
    # Fallback: simple parsing
    return {
        "type": None,
        "scope": None,
        "description": commit_message.split("\n")[0],
        "feature_id": None,
        "format": "simple",
    }
