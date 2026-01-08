"""MCP Tools for file structure parsing and import."""
from typing import Optional, List, Dict
from uuid import UUID
from pathlib import Path
import os
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.project_service import ProjectService
from src.services.element_service import ElementService


def get_parse_file_structure_tool() -> MCPTool:
    """Get parse file structure tool definition."""
    return MCPTool(
        name="mcp_parse_file_structure",
        description="Parse project file structure and automatically create project elements. Analyzes the codebase directory structure and creates hierarchical elements (modules, components) based on folders and files. Useful for new projects to quickly set up the project structure.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Project directory path (defaults to current working directory if not provided)",
                },
                "maxDepth": {
                    "type": "integer",
                    "description": "Maximum directory depth to parse (default: 3)",
                    "default": 3,
                },
                "ignorePatterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File/folder patterns to ignore (e.g., ['node_modules', '.git', '__pycache__'])",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_parse_file_structure(
    project_id: str,
    project_path: Optional[str] = None,
    max_depth: int = 3,
    ignore_patterns: Optional[List[str]] = None,
) -> dict:
    """Handle parse file structure tool call."""
    if not project_path:
        project_path = os.getcwd()
    
    path_obj = Path(project_path).resolve()
    
    # Default ignore patterns
    default_ignore = [
        "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
        ".next", ".nuxt", "dist", "build", ".idea", ".vscode", ".cursor",
        ".DS_Store", "*.pyc", "*.pyo", "*.pyd", ".pytest_cache",
        "coverage", ".coverage", "htmlcov", ".tox", ".mypy_cache",
    ]
    ignore_patterns = ignore_patterns or default_ignore
    
    db = SessionLocal()
    try:
        # Use ProjectService to verify project exists
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}
        
        # Check if project already has elements using ElementService
        existing_elements_list = ElementService.get_project_elements_tree(db, UUID(project_id))
        existing_elements = len(existing_elements_list)
        
        if existing_elements > 0:
            return {
                "warning": "Project already has elements. Use 'mcp_import_github_issues' or manual element creation instead.",
                "existing_elements_count": existing_elements,
            }
        
        # Parse directory structure
        elements_created = []
        element_map: Dict[str, UUID] = {}  # Map path -> element_id
        
        def should_ignore(path: Path) -> bool:
            """Check if path should be ignored."""
            path_str = str(path)
            for pattern in ignore_patterns:
                if pattern in path_str or path.name.startswith('.'):
                    return True
            return False
        
        def determine_element_type(path: Path, is_file: bool) -> str:
            """Determine element type based on path and content."""
            if is_file:
                return "component"
            
            # Check for common patterns
            name_lower = path.name.lower()
            if any(x in name_lower for x in ["api", "routes", "endpoints", "controllers"]):
                return "module"
            elif any(x in name_lower for x in ["components", "ui", "views", "pages"]):
                return "module"
            elif any(x in name_lower for x in ["services", "utils", "helpers", "lib"]):
                return "module"
            elif any(x in name_lower for x in ["models", "schemas", "types"]):
                return "module"
            elif any(x in name_lower for x in ["tests", "test", "__tests__"]):
                return "module"
            elif any(x in name_lower for x in ["config", "settings", "setup"]):
                return "module"
            else:
                return "module"  # Default to module
        
        def parse_directory(dir_path: Path, parent_element_id: Optional[UUID], depth: int) -> None:
            """Recursively parse directory structure."""
            if depth > max_depth:
                return
            
            if should_ignore(dir_path):
                return
            
            # Create element for directory
            element_type = determine_element_type(dir_path, is_file=False)
            element_title = dir_path.name.replace("_", " ").replace("-", " ").title()
            
            # Try to read README or package.json for description
            description = None
            readme_path = dir_path / "README.md"
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        description = f.read()[:500]  # First 500 chars
                except:
                    pass
            
            # Use ElementService to create element
            element = ElementService.create_element(
                db=db,
                project_id=UUID(project_id),
                type=element_type,
                title=element_title,
                description=description,
                status="new",
                parent_id=parent_element_id,
                position=None,
            )
            
            element_map[str(dir_path)] = element.id
            elements_created.append({
                "id": str(element.id),
                "title": element_title,
                "type": element_type,
                "path": str(dir_path),
            })
            
            # Parse subdirectories
            try:
                for item in sorted(dir_path.iterdir()):
                    if item.is_dir() and not should_ignore(item):
                        parse_directory(item, element.id, depth + 1)
            except PermissionError:
                pass  # Skip directories we can't access
        
        # Start parsing from project root
        parse_directory(path_obj, None, 0)
        
        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        
        return {
            "success": True,
            "project_id": project_id,
            "elements_created": len(elements_created),
            "elements": elements_created,
            "message": f"Created {len(elements_created)} project elements from file structure",
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        db.close()
