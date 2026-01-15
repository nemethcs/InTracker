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
        """Generate cursor rules for a project.
        
        Also automatically updates resume_context with current project state if needed.
        """
        # Auto-update resume context periodically (every time rules are generated)
        # This ensures immediate_goals and constraints stay up-to-date
        self._update_resume_context_if_needed(project)
        
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
        from .rules_sections.language_content import replace_language_placeholders
        
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
                # Replace language-specific placeholders (e.g., {LANG:key})
                content = replace_language_placeholders(content, team_language)
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

**To update resume context (immediate_goals, constraints, blockers):**
- `mcp_update_resume_context(projectId, resumeContext)` - Update resume context fields
  - Example: `mcp_update_resume_context(projectId, {now: {immediate_goals: ["Goal 1", "Goal 2"]}, constraints: ["Constraint 1"]})`
  - Supports partial updates - only provided fields will be updated
  - Use this periodically to keep resume context up-to-date

---

**Generated by InTracker MCP Server**
**Last updated:** {project.updated_at.isoformat() if project.updated_at else 'Unknown'}
**Project:** {project.name}
"""
        
        return rules_content
    
    def _update_resume_context_if_needed(self, project: Project) -> None:
        """Update resume context with current project state if needed.
        
        This method extracts immediate goals and constraints from the project state
        and updates the resume_context. Called automatically when rules are generated.
        """
        from src.database.base import SessionLocal
        from src.services.project_service import ProjectService
        from src.services.todo_service import TodoService
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            # Get current project with fresh data
            current_project = ProjectService.get_project_by_id(db, project.id)
            if not current_project:
                return
            
            # Get current resume context
            resume_context = current_project.resume_context or {}
            
            # Check if we need to update (e.g., last update was more than 1 hour ago)
            # or if resume_context is empty/missing key fields
            needs_update = False
            if not resume_context:
                needs_update = True
            elif "now" not in resume_context:
                needs_update = True
            elif "immediate_goals" not in resume_context.get("now", {}):
                needs_update = True
            
            # If resume_context exists but immediate_goals is empty, try to populate it
            if not needs_update:
                now = resume_context.get("now", {})
                immediate_goals = now.get("immediate_goals", [])
                if not immediate_goals or len(immediate_goals) == 0:
                    needs_update = True
            
            if needs_update:
                # Get active todos to extract immediate goals
                all_todos, _ = TodoService.get_todos_by_project(
                    db=db,
                    project_id=project.id,
                    status=None,
                    skip=0,
                    limit=100,
                )
                
                # Extract immediate goals from high-priority todos
                immediate_goals = []
                high_priority_todos = [
                    t for t in all_todos 
                    if t.status in ["new", "in_progress"] 
                    and t.priority in ["critical", "high"]
                ][:5]  # Top 5 high-priority todos
                
                for todo in high_priority_todos:
                    goal = f"Complete: {todo.title}"
                    if todo.feature_id:
                        # Try to get feature name
                        from src.services.feature_service import FeatureService
                        feature = FeatureService.get_feature_by_id(db, todo.feature_id)
                        if feature:
                            goal = f"Complete: {todo.title} (Feature: {feature.name})"
                    immediate_goals.append(goal)
                
                # Extract constraints from cursor_instructions or project description
                constraints = []
                if project.cursor_instructions:
                    # Extract key constraints from cursor_instructions
                    # Look for lines that start with "MUST", "NEVER", "ALWAYS", "REQUIRED"
                    lines = project.cursor_instructions.split('\n')
                    for line in lines:
                        line = line.strip()
                        if any(keyword in line.upper() for keyword in ["MUST", "NEVER", "ALWAYS", "REQUIRED", "CONSTRAINT"]):
                            if len(line) > 10:  # Only add meaningful constraints
                                constraints.append(line)
                
                # Update resume_context
                if "now" not in resume_context:
                    resume_context["now"] = {}
                
                # Only update if we have new data
                if immediate_goals:
                    resume_context["now"]["immediate_goals"] = immediate_goals
                
                if constraints:
                    resume_context["constraints"] = constraints
                
                # Save updated resume_context
                if immediate_goals or constraints:
                    ProjectService.update_project(
                        db=db,
                        project_id=project.id,
                        resume_context=resume_context,
                        current_user_id=None,
                    )
                    db.commit()
        except Exception as e:
            # Don't fail rules generation if resume_context update fails
            import logging
            logging.warning(f"Failed to auto-update resume_context for project {project.id}: {e}")
        finally:
            db.close()
    
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
