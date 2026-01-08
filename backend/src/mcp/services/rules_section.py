"""Rules section model for cursor rules generation."""
from typing import Dict, Optional
from src.database.models import Project


class RulesSection:
    """Represents a rules section that can be conditionally included."""
    
    def __init__(self, name: str, content: str, conditions: Optional[Dict] = None):
        self.name = name
        self.content = content
        self.conditions = conditions or {}
    
    def should_include(self, project: Project) -> bool:
        """Check if this section should be included based on project configuration."""
        if not self.conditions:
            return True
        
        # Check technology tags
        if "technology_tags" in self.conditions:
            required_tags = self.conditions["technology_tags"]
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            project_tags = [tag.lower() for tag in (project.technology_tags or [])]
            if not any(tag.lower() in project_tags for tag in required_tags):
                return False
        
        # Check tags
        if "tags" in self.conditions:
            required_tags = self.conditions["tags"]
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            project_tags = [tag.lower() for tag in (project.tags or [])]
            if not any(tag.lower() in project_tags for tag in required_tags):
                return False
        
        # Check status
        if "status" in self.conditions:
            if project.status not in self.conditions["status"]:
                return False
        
        # Check has_github_repo
        if "has_github_repo" in self.conditions:
            if bool(project.github_repo_url) != self.conditions["has_github_repo"]:
                return False
        
        return True
