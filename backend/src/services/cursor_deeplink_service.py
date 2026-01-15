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
        team_id: Optional[str] = None,
        feature_branches: Optional[List[str]] = None,
        goals: Optional[str] = None,
        constraints: Optional[str] = None,
    ) -> str:
        """Generate a Cursor chat deeplink for importing a GitHub project into InTracker.
        
        Args:
            repo_url: GitHub repository URL
            repo_owner: Repository owner
            repo_name: Repository name
            team_id: Optional team ID for the project
            feature_branches: Optional list of feature branch names
            goals: Optional project goals
            constraints: Optional project constraints
            
        Returns:
            Cursor chat deeplink URL
        """
        # Build the message for the agent (shortened to avoid URL length limits)
        message_parts = [
            f"Szedd le git-ből ezt a projektet, nézd át és hozd létre az InTracker-ben: {repo_url}",
            "",
            "Lépések:",
            f"1. Klónozd: `git clone {repo_url}`",
            "2. Nézd át a projektet (struktúra, README, kód, tech stack)",
            "3. Hozd létre az InTracker-ben az mcp_create_project tool-lal:",
            "   - name, description (README alapján), tags, technology_tags",
            "   - cursor_instructions (AI agenteknek), github_repo_url",
        ]
        
        if team_id:
            message_parts.append(f"   - team_id: {team_id}")
        
        message_parts.append("4. Feature branch-ek létrehozása (ha vannak):")
        
        if feature_branches:
            branches_str = ", ".join(feature_branches[:5])  # Limit to first 5
            if len(feature_branches) > 5:
                branches_str += f" (+{len(feature_branches)-5} more)"
            message_parts.append(f"   - {branches_str}")
            message_parts.append("   - Használd az mcp_create_feature tool-t")
        else:
            message_parts.append("   - Ha vannak feature/* vagy feat/* branch-ek, hozd létre őket")
        
        message_parts.extend([
            "5. Goals és constraints kitöltése (mcp_update_project)",
            "",
            "Fontos: Minden mezőt tölts ki alaposan!",
        ])
        
        message = "\n".join(message_parts)
        
        # Encode message for URL
        encoded_message = quote(message)
        
        # Generate deeplink
        deeplink = f"cursor://chat?message={encoded_message}"
        
        return deeplink


# Global instance
cursor_deeplink_service = CursorDeeplinkService()
