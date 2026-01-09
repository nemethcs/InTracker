"""Cursor Rules Generator Service - Dynamic rules generation based on project configuration."""
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID
from src.database.models import Project
from .rules_section import RulesSection
from .rules_sections import (
    create_core_workflow_section,
    create_git_workflow_section,
    create_docker_section,
    create_mcp_server_section,
    create_frontend_section,
    create_github_section,
    create_intracker_integration_section,
    create_user_interaction_section,
)


class RulesGenerator:
    """Generates cursor rules dynamically based on project configuration."""
    
    def __init__(self):
        self.sections: List[RulesSection] = []
        self._register_default_sections()
    
    def _register_default_sections(self):
        """Register default rules sections."""
        self.sections.append(create_core_workflow_section())
        self.sections.append(create_git_workflow_section())
        self.sections.append(create_docker_section())
        self.sections.append(create_mcp_server_section())
        self.sections.append(create_frontend_section())
        self.sections.append(create_github_section())
        self.sections.append(create_intracker_integration_section())
        self.sections.append(create_user_interaction_section())
    
    def generate_rules(self, project: Project, custom_instructions: Optional[str] = None) -> str:
        """Generate cursor rules for a project."""
        cursor_instructions = custom_instructions or project.cursor_instructions or ""
        
        # Get team language (default to 'en' if not set)
        team_language = 'en'  # Default language
        if project.team and project.team.language:
            team_language = project.team.language
        elif hasattr(project, 'team_id') and project.team_id:
            # If team relationship not loaded, we'll need to load it
            # For now, use default - this will be handled by the caller if needed
            pass
        
        # Build project-specific service list
        docker_services = self._get_docker_services(project)
        mcp_service = "  mcp-server: MCP Server (port 3001)" if self._uses_mcp(project) else ""
        frontend_service = "  frontend: React + Vite (port 5173)" if self._has_frontend(project) else ""
        uses_mcp = self._uses_mcp(project)
        
        # Build restart info sections
        backend_restart = self._get_backend_restart_info(project)
        frontend_restart = self._get_frontend_restart_info(project)
        mcp_restart = self._get_mcp_restart_info(project)
        
        # Generate rules content
        rules_content = f"""---
name: intracker-project-rules
description: Cursor AI instructions for {project.name}
version: {datetime.utcnow().isoformat()}
---

# Cursor Rules for {project.name}

{project.description or ''}

## Project Information

- **Project ID:** {project.id}
- **Status:** {project.status}
- **Tags:** {', '.join(project.tags) if project.tags else 'None'}
- **Technology Tags:** {', '.join(project.technology_tags) if project.technology_tags else 'None'}
- **GitHub:** {project.github_repo_url or 'Not connected'}

## Cursor Instructions

{cursor_instructions}

## Development Rules

### Environment Strategy

- **MVP Phase:** All development in local Docker environment
- **Post-MVP:** Deploy to Azure (staging → production)
- **Never deploy to Azure during MVP development**

"""
        
        # Add conditional sections
        for section in self.sections:
            if section.should_include(project):
                content = section.content
                # Replace placeholders
                content = content.replace("{DOCKER_SERVICES}", docker_services)
                content = content.replace("{FRONTEND_SERVICE}", frontend_service)
                content = content.replace("{MCP_SERVICE}", mcp_service)
                content = content.replace("{BACKEND_RESTART_INFO}", backend_restart)
                content = content.replace("{FRONTEND_RESTART_INFO}", frontend_restart)
                content = content.replace("{MCP_RESTART_INFO}", mcp_restart)
                # Replace conditional placeholders (for f-string-like behavior in sections)
                if "{uses_mcp}" in content:
                    content = content.replace("{uses_mcp}", str(uses_mcp))
                # Replace language placeholder if present
                if "{LANGUAGE}" in content:
                    content = content.replace("{LANGUAGE}", team_language)
                rules_content += content + "\n"
        
        # Add project-specific information
        rules_content += f"""
### Project-Specific Information

**This section is dynamically generated for each project:**
- Project ID: {project.id}
- Current status: {project.status}
- Active features: Check resume context
- Next todos: Check resume context
- Blockers: Check resume context
- Constraints: Check resume context

**To get latest project state:**
- `mcp_get_resume_context(projectId)` - Full current state
- `mcp_get_project_context(projectId)` - Complete project info
- `mcp_get_active_todos(projectId)` - Current todos

---

**Generated by InTracker MCP Server**
**Last updated:** {project.updated_at.isoformat() if project.updated_at else 'Unknown'}
**Project:** {project.name}
"""
        
        return rules_content
    
    def _uses_mcp(self, project: Project) -> bool:
        """Check if project uses MCP."""
        return project.technology_tags and "mcp" in [tag.lower() for tag in project.technology_tags]
    
    def _has_frontend(self, project: Project) -> bool:
        """Check if project has frontend."""
        frontend_tags = ["react", "vue", "angular", "svelte", "frontend"]
        if not project.technology_tags:
            return False
        return any(tag.lower() in [t.lower() for t in project.technology_tags] for tag in frontend_tags)
    
    def _get_docker_services(self, project: Project) -> str:
        """Get Docker services list based on project."""
        services = []
        if "postgres" in [tag.lower() for tag in (project.technology_tags or [])]:
            services.append("  postgres: postgres:16 (port 5433 → 5432)")
        if "redis" in [tag.lower() for tag in (project.technology_tags or [])]:
            services.append("  redis: redis:7-alpine (port 6379)")
        if "fastapi" in [tag.lower() for tag in (project.technology_tags or [])] or "python" in [tag.lower() for tag in (project.technology_tags or [])]:
            services.append("  backend: FastAPI (port 3000)")
        return "\n".join(services) if services else "  # No services defined"
    
    def _get_backend_restart_info(self, project: Project) -> str:
        """Get backend restart information."""
        if "fastapi" in [tag.lower() for tag in (project.technology_tags or [])] or "python" in [tag.lower() for tag in (project.technology_tags or [])]:
            return """- **Backend changes:** 
  - `docker-compose restart backend` (restarts container)
  - Backend code is mounted, but Python imports may need restart
  - Always restart after adding new files/modules
  - Check logs: `docker-compose logs backend --tail=50`"""
        return ""
    
    def _get_frontend_restart_info(self, project: Project) -> str:
        """Get frontend restart information."""
        if self._has_frontend(project):
            return """- **Frontend changes:** 
  - Auto-reloads with Vite (no restart needed)
  - If issues: `docker-compose restart frontend`"""
        return ""
    
    def _get_mcp_restart_info(self, project: Project) -> str:
        """Get MCP server restart information."""
        if self._uses_mcp(project):
            return """- **MCP server changes:**
  - `docker-compose restart mcp-server` (restarts container)
  - **CRITICAL:** After MCP server restart, user MUST reload MCP connection in Cursor
  - MCP server code is mounted, but Python imports may need restart
  - Check logs: `docker-compose logs mcp-server --tail=50`"""
        return ""
    
    def add_custom_section(self, section: RulesSection):
        """Add a custom rules section."""
        self.sections.append(section)
    
    def update_section(self, name: str, content: str, conditions: Optional[Dict] = None):
        """Update an existing section."""
        for section in self.sections:
            if section.name == name:
                section.content = content
                if conditions:
                    section.conditions = conditions
                return
        # If not found, add as new section
        self.sections.append(RulesSection(name, content, conditions))


# Global instance
rules_generator = RulesGenerator()
