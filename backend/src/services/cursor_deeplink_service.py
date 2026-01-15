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
        # Build the message for the agent
        message_parts = [
            f"Szedd le git-ből ezt a projektet, nézd át és hozd létre az InTracker-ben:",
            "",
            f"Repository: {repo_url}",
            f"Owner: {repo_owner}",
            f"Name: {repo_name}",
            "",
            "Lépések:",
            "",
            "1. **Git clone és projekt átnézése:**",
            f"   - Klónozd le a repository-t: `git clone {repo_url}`",
            "   - Nézd át a projekt struktúráját, fájlokat, dokumentációt (README.md, package.json, requirements.txt, stb.)",
            "   - Elemezd a kódot, technológiákat, függőségeket",
            "   - Olvasd el a README-t és egyéb dokumentációt",
            "",
            "2. **InTracker projekt létrehozása:**",
            "   - Használd az MCP tool-okat az InTracker-ben",
            "   - Hozd létre a projektet az `mcp_create_project` tool-lal",
            "   - Töltsd ki MINDEN mezőt alaposan:",
            "     * **name**: A projekt neve (pl. a repository neve vagy egy leíró név)",
            "     * **description**: Részletes leírás a projekt céljáról, funkcionalitásáról (README alapján)",
            "     * **tags**: Célszerű címkék (pl. ai, web-app, api, stb.)",
            "     * **technology_tags**: Használt technológiák (pl. react, typescript, python, fastapi, stb.)",
            "     * **cursor_instructions**: Részletes utasítások az AI agenteknek a projektről",
            "     * **github_repo_url**: A repository URL-je",
        ]
        
        if team_id:
            message_parts.append(f"     * **team_id**: {team_id}")
        
        message_parts.extend([
            "",
            "3. **Feature branch-ek létrehozása:**",
        ])
        
        if feature_branches:
            message_parts.append("   - A következő feature branch-eket hozd létre feature-ként az InTracker-ben:")
            for branch in feature_branches:
                message_parts.append(f"     * {branch}")
            message_parts.append("   - Használd az `mcp_create_feature` tool-t minden feature branch-hez")
        else:
            message_parts.append("   - Ha vannak feature branch-ek (feature/*, feat/*, stb.), hozd létre őket feature-ként")
            message_parts.append("   - Használd az `mcp_create_feature` tool-t")
        
        message_parts.extend([
            "",
            "4. **Goals és Constraints kitöltése:**",
            "   - A projekt elemzése alapján töltse ki a goals-t és constraints-et",
            "   - Használd az `mcp_update_project` tool-t",
            "   - A goals tartalmazza a projekt fő céljait, célközönségét",
            "   - A constraints tartalmazza a technikai korlátokat, architektúra döntéseket",
            "",
            "5. **Projekt struktúra elemzése (opcionális):**",
            "   - Ha van lehetőség, elemezd a projekt fájlstruktúráját",
            "   - Hozz létre project element-eket a főbb modulokhoz/komponensekhez",
            "",
            "**Fontos:**",
            "- Minden mezőt alaposan tölts ki, ne hagyj üres mezőket!",
            "- A description legyen részletes és informatív",
            "- A cursor_instructions legyen hasznos az AI agenteknek",
            "- A technology_tags tartalmazza az összes használt technológiát",
            "",
            "**MCP Tools használata:**",
            "- `mcp_create_project`: Projekt létrehozása",
            "- `mcp_create_feature`: Feature-k létrehozása feature branch-ekhez",
            "- `mcp_update_project`: Goals és constraints frissítése",
            "- `mcp_parse_file_structure`: Projekt struktúra elemzése (opcionális)",
        ])
        
        message = "\n".join(message_parts)
        
        # Encode message for URL
        encoded_message = quote(message)
        
        # Generate deeplink
        deeplink = f"cursor://chat?message={encoded_message}"
        
        return deeplink


# Global instance
cursor_deeplink_service = CursorDeeplinkService()
