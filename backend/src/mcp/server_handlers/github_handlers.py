"""GitHub tool handlers for MCP server."""
from mcp.types import TextContent
import json
from src.mcp.tools import github


async def handle_github_tool(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle GitHub tool calls."""
    try:
        if name == "mcp_get_branch_info":
            result = await github.handle_get_branch_info(
                arguments["projectId"],
                arguments.get("featureId"),
                arguments.get("branchName"),
                arguments.get("includeStatus", True),
                arguments.get("includeCommits", False),
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

        elif name == "mcp_link_branch_to_feature":
            result = await github.handle_link_branch_to_feature(
                arguments["featureId"],
                arguments["branchName"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        elif name == "mcp_parse_commit_message":
            result = await github.handle_parse_commit_message(
                arguments["commitMessage"],
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2) if isinstance(result, dict) else str(result))]

        return None
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
