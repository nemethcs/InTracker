"""Service for generating Cursor chat deeplinks."""
from typing import Optional, List, Dict, Any
from urllib.parse import quote


class CursorDeeplinkService:
    """Service for generating Cursor chat deeplinks."""
    
    @staticmethod
    def generate_project_import_deeplink(
        repo_url: str,
        repo_owner: str,
        repo_name: str,
        feature_branches: Optional[List[str]] = None,
        goals: Optional[str] = None,
        constraints: Optional[str] = None,
    ) -> str:
        """Generate a Cursor chat deeplink for importing a GitHub project into InTracker.
        
        Args:
            repo_url: GitHub repository URL
            repo_owner: Repository owner
            repo_name: Repository name
            feature_branches: Optional list of feature branch names
            goals: Optional project goals
            constraints: Optional project constraints
            
        Returns:
            Cursor chat deeplink URL
        """
        # Build the message for the agent
        message_parts = [
            f"Please analyze the GitHub repository: {repo_url}",
            "",
            "Tasks:",
            "1. Review the project structure, codebase, and documentation",
            "2. Create the project in InTracker using MCP tools",
            "3. If there are feature branches (feature/*, feat/*, etc.), create them as features in InTracker",
            "4. If possible, fill in the project goals and constraints based on the repository analysis",
            "",
            f"Repository: {repo_owner}/{repo_name}",
            f"URL: {repo_url}",
        ]
        
        if feature_branches:
            message_parts.append("")
            message_parts.append("Feature branches found:")
            for branch in feature_branches:
                message_parts.append(f"- {branch}")
            message_parts.append("")
            message_parts.append("Please create these as features in InTracker.")
        
        if goals:
            message_parts.append("")
            message_parts.append("Suggested goals:")
            message_parts.append(goals)
        
        if constraints:
            message_parts.append("")
            message_parts.append("Suggested constraints:")
            message_parts.append(constraints)
        
        message_parts.append("")
        message_parts.append("Use MCP tools to:")
        message_parts.append("- mcp_create_project: Create the project")
        message_parts.append("- mcp_create_feature: Create features for each feature branch")
        message_parts.append("- mcp_update_project: Update goals and constraints")
        
        message = "\n".join(message_parts)
        
        # Encode message for URL
        encoded_message = quote(message)
        
        # Generate deeplink
        deeplink = f"cursor://chat?message={encoded_message}"
        
        return deeplink


# Global instance
cursor_deeplink_service = CursorDeeplinkService()
