"""Cursor Rules Generator Service - Dynamic rules generation based on project configuration."""
from typing import Dict, List, Optional
from src.database.models import Project
from .rules_section import RulesSection
from .rules_builder import RulesBuilder
from .project_analyzer import ProjectAnalyzer
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
        team_language = self._get_team_language(project)
        
        # Build rules content using modular builders
        rules_content = RulesBuilder.build_header(project)
        rules_content += RulesBuilder.build_project_info(project)
        rules_content += RulesBuilder.build_cursor_instructions(cursor_instructions)
        rules_content += RulesBuilder.build_environment_strategy()
        
        # Add conditional sections
        rules_content += self._build_sections(project, team_language)
        
        # Add project-specific information
        rules_content += RulesBuilder.build_project_specific_info(project)
        
        return rules_content
    
    def _get_team_language(self, project: Project) -> str:
        """Get team language (default to 'en' if not set)."""
        if project.team and project.team.language:
            return project.team.language
        return 'en'  # Default language
    
    def _build_sections(self, project: Project, team_language: str) -> str:
        """Build and add conditional sections."""
        from .rules_sections.language_content import replace_language_placeholders
        
        placeholder_replacements = RulesBuilder.get_placeholder_replacements(project)
        sections_content = ""
        
        for section in self.sections:
            if section.should_include(project):
                content = section.content
                
                # Replace all placeholders
                for placeholder, replacement in placeholder_replacements.items():
                    content = content.replace(placeholder, replacement)
                
                # Replace language placeholder if present
                if "{LANGUAGE}" in content:
                    content = content.replace("{LANGUAGE}", team_language)
                
                # Replace language-specific placeholders (e.g., {LANG:key})
                content = replace_language_placeholders(content, team_language)
                
                sections_content += content + "\n"
        
        return sections_content
    
    
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
