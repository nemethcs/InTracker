"""MCP Tools for codebase analysis."""
from typing import Optional
from uuid import UUID
from pathlib import Path
import os
import json
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.services.project_service import ProjectService


def get_analyze_codebase_tool() -> MCPTool:
    """Get analyze codebase tool definition."""
    return MCPTool(
        name="mcp_analyze_codebase",
        description="Analyze existing codebase and suggest initial project structure. Examines the codebase to identify modules, components, and suggest a hierarchical structure. Useful for existing projects that need to be set up in InTracker.",
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
            },
            "required": ["projectId"],
        },
    )


async def handle_analyze_codebase(
    project_id: str,
    project_path: Optional[str] = None,
) -> dict:
    """Handle analyze codebase tool call."""
    if not project_path:
        project_path = os.getcwd()
    
    path_obj = Path(project_path).resolve()
    
    db = SessionLocal()
    try:
        # Use ProjectService to verify project exists
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}
        
        # Analyze codebase structure
        suggestions = {
            "modules": [],
            "components": [],
            "suggested_structure": [],
        }
        
        # Look for common patterns
        common_modules = {
            "backend": ["api", "routes", "controllers", "services", "models"],
            "frontend": ["components", "pages", "hooks", "stores", "utils"],
            "shared": ["types", "schemas", "utils", "constants"],
        }
        
        # Scan for package.json, requirements.txt, etc. to detect tech stack
        tech_stack = []
        if (path_obj / "package.json").exists():
            tech_stack.append("node")
            try:
                with open(path_obj / "package.json", "r") as f:
                    pkg = json.load(f)
                    if "react" in str(pkg.get("dependencies", {})).lower():
                        tech_stack.append("react")
                    if "vue" in str(pkg.get("dependencies", {})).lower():
                        tech_stack.append("vue")
            except:
                pass
        
        if (path_obj / "requirements.txt").exists() or (path_obj / "pyproject.toml").exists():
            tech_stack.append("python")
            if (path_obj / "fastapi").exists() or any("fastapi" in str(f) for f in (path_obj / "requirements.txt").read_text().split("\n") if (path_obj / "requirements.txt").exists()):
                tech_stack.append("fastapi")
        
        # Generate suggestions based on detected structure
        for category, patterns in common_modules.items():
            for pattern in patterns:
                pattern_path = path_obj / pattern
                if pattern_path.exists() and pattern_path.is_dir():
                    suggestions["modules"].append({
                        "name": pattern.replace("_", " ").title(),
                        "path": str(pattern_path),
                        "type": "module",
                    })
        
        return {
            "success": True,
            "project_id": project_id,
            "tech_stack": tech_stack,
            "suggestions": suggestions,
            "message": "Codebase analysis complete. Use 'mcp_parse_file_structure' to create elements, or 'mcp_import_github_issues' to import existing issues.",
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        db.close()
