"""Project analyzer for rules generation - analyzes project configuration."""
from typing import List
from src.database.models import Project


class ProjectAnalyzer:
    """Analyzes project configuration for rules generation."""
    
    @staticmethod
    def uses_mcp(project: Project) -> bool:
        """Check if project uses MCP."""
        return project.technology_tags and "mcp" in [tag.lower() for tag in project.technology_tags]
    
    @staticmethod
    def has_frontend(project: Project) -> bool:
        """Check if project has frontend."""
        frontend_tags = ["react", "vue", "angular", "svelte", "frontend"]
        if not project.technology_tags:
            return False
        return any(tag.lower() in [t.lower() for t in project.technology_tags] for tag in frontend_tags)
    
    @staticmethod
    def get_docker_services(project: Project) -> str:
        """Get Docker services list based on project technology tags."""
        services: List[str] = []
        if not project.technology_tags:
            return "  # No services defined"
        
        tags_lower = [tag.lower() for tag in project.technology_tags]
        
        if "postgres" in tags_lower:
            services.append("  postgres: postgres:16 (port 5433 → 5432)")
        if "redis" in tags_lower:
            services.append("  redis: redis:7-alpine (port 6379)")
        if "fastapi" in tags_lower or "python" in tags_lower:
            services.append("  backend: FastAPI (port 3000)")
        
        return "\n".join(services) if services else "  # No services defined"
    
    @staticmethod
    def get_backend_restart_info(project: Project) -> str:
        """Get backend restart information."""
        if not project.technology_tags:
            return ""
        
        tags_lower = [tag.lower() for tag in project.technology_tags]
        if "fastapi" in tags_lower or "python" in tags_lower:
            return """- **Backend changes:** 
  - `docker-compose restart backend` (restarts container)
  - Backend code is mounted, but Python imports may need restart
  - Always restart after adding new files/modules
  - Check logs: `docker-compose logs backend --tail=50`"""
        return ""
    
    @staticmethod
    def get_frontend_restart_info(project: Project) -> str:
        """Get frontend restart information."""
        if ProjectAnalyzer.has_frontend(project):
            return """- **Frontend changes:** 
  - Auto-reloads with Vite (no restart needed)
  - If issues: `docker-compose restart frontend`"""
        return ""
    
    @staticmethod
    def get_mcp_restart_info(project: Project) -> str:
        """Get MCP server restart information."""
        if ProjectAnalyzer.uses_mcp(project):
            return """- **MCP server changes:**
  - `docker-compose restart mcp-server` (restarts container)
  - **CRITICAL:** After MCP server restart, user MUST reload MCP connection in Cursor
  - MCP server code is mounted, but Python imports may need restart
  - Check logs: `docker-compose logs mcp-server --tail=50`"""
        return ""
    
    @staticmethod
    def get_mcp_service_info(project: Project) -> str:
        """Get MCP service information string."""
        if ProjectAnalyzer.uses_mcp(project):
            return "  mcp-server: MCP Server (port 3001)"
        return ""
    
    @staticmethod
    def get_frontend_service_info(project: Project) -> str:
        """Get frontend service information string."""
        if ProjectAnalyzer.has_frontend(project):
            return "  frontend: React + Vite (port 5173)"
        return ""
