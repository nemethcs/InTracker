"""MCP Tools for project workflow and cursor rules."""
from typing import Optional
from pathlib import Path
import json as json_lib
from mcp.types import Tool as MCPTool
from src.mcp.tools.project_crud import handle_identify_project_by_path
from src.mcp.tools.project_context import handle_get_resume_context


def get_load_cursor_rules_tool() -> MCPTool:
    """Get load cursor rules tool definition."""
    return MCPTool(
        name="mcp_load_cursor_rules",
        description="Load Cursor Rules from project and save to .cursor/rules/intracker-project-rules.mdc file in the project directory. Works both locally and when MCP server is on Azure.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Project directory path where .cursor/rules/ directory exists. If not provided, will try to auto-detect from .intracker/config.json or use current working directory.",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_load_cursor_rules(project_id: str, project_path: Optional[str] = None) -> dict:
    """Handle load cursor rules tool call.
    
    This function returns the cursor rules content and automatically saves it to the project directory.
    Works both locally (Docker) and when MCP server is on Azure - in Azure case, returns content
    for Cursor to save locally.
    """
    from src.mcp.resources.project_resources import read_cursor_rules_resource
    
    try:
        # Get cursor rules content from resource
        content = await read_cursor_rules_resource(project_id)
        
        # Determine project directory
        project_dir = None
        
        if project_path:
            # Use provided path (from Cursor working directory)
            project_dir = Path(project_path)
        else:
            # Try to find project directory
            # In Docker, check /workspace (mounted project root)
            docker_project_dir = Path("/workspace")
            if docker_project_dir.exists() and (docker_project_dir / ".intracker" / "config.json").exists():
                try:
                    config_file = docker_project_dir / ".intracker" / "config.json"
                    with open(config_file) as f:
                        config = json_lib.load(f)
                        if config.get("project_id") == project_id:
                            project_dir = docker_project_dir
                except Exception:
                    pass
            
            # If not found in Docker mount, try current directory and parents
            if not project_dir:
                current_dir = Path.cwd()
                check_dir = current_dir
                for _ in range(5):  # Check up to 5 levels up
                    config_file = check_dir / ".intracker" / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file) as f:
                                config = json_lib.load(f)
                                if config.get("project_id") == project_id:
                                    project_dir = check_dir
                                    break
                        except Exception:
                            pass
                    check_dir = check_dir.parent
                    if check_dir == check_dir.parent:  # Reached root
                        break
                
                if not project_dir:
                    project_dir = current_dir
        
        # Try to write file if we have access to the directory
        file_written = False
        file_path = None
        file_size = None
        error_message = None
        
        try:
            # Create .cursor/rules directory if it doesn't exist
            rules_dir = project_dir / ".cursor" / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            
            # Write cursor rules file
            rules_file = rules_dir / "intracker-project-rules.mdc"
            rules_file.write_text(content, encoding="utf-8")
            
            file_written = True
            file_path = str(rules_file)
            file_size = rules_file.stat().st_size
        except (PermissionError, OSError, FileNotFoundError) as e:
            # If we can't write (e.g., MCP server on Azure), return content for Cursor to save
            error_message = f"Could not write file directly: {e}. Content returned for Cursor to save locally."
            file_path = ".cursor/rules/intracker-project-rules.mdc"
        
        # Always return the content, even if we couldn't write it
        # This allows Cursor to save it locally when MCP server is on Azure
        result = {
            "success": True,
            "project_id": project_id,
            "content": content,
            "target_path": file_path or ".cursor/rules/intracker-project-rules.mdc",
            "instructions": "Save the content to .cursor/rules/intracker-project-rules.mdc in your project directory",
        }
        
        if file_written:
            result["file_written"] = True
            result["file_path"] = file_path
            result["file_size"] = file_size
            result["message"] = f"Cursor Rules saved to {file_path}"
        else:
            result["file_written"] = False
            result["message"] = error_message or "File not written by server. Use the 'content' field to save it locally."
            result["note"] = "When MCP server is on Azure, Cursor should save the file locally using the 'content' field."
        
        return result
    except Exception as e:
        import traceback
        return {
            "success": False,
            "project_id": project_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def get_enforce_workflow_tool() -> MCPTool:
    """Get enforce workflow tool definition."""
    return MCPTool(
        name="mcp_enforce_workflow",
        description="""MANDATORY: Call this at the START of EVERY session to ensure proper workflow.
        
        This tool automatically:
        1. Identifies the current project (by path or auto-detection)
        2. Loads resume context (Last/Now/Blockers/Constraints)
        3. Loads cursor rules (project-specific rules)
        4. Returns a workflow checklist of what you MUST do
        
        ALWAYS call this first before doing any work! This ensures you never forget the workflow.
        
        If no project is found, it will return instructions to create one first.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Current working directory path (optional, auto-detected if not provided)",
                },
            },
        },
    )


async def handle_enforce_workflow(path: Optional[str] = None) -> dict:
    """Handle enforce workflow tool call.
    
    This function enforces the InTracker workflow by:
    1. Identifying the project
    2. Loading resume context
    3. Loading cursor rules
    4. Returning a workflow checklist
    """
    # Step 1: Identify project
    project_info = await handle_identify_project_by_path(path)
    
    if not project_info.get("project_id"):
        return {
            "error": "No project found",
            "message": "No project found in current directory. Create one first with mcp_create_project",
            "workflow": [
                "1. Create project: mcp_create_project(name, teamId, description?, ...)",
                "2. Call mcp_enforce_workflow() again after project creation"
            ],
            "workflow_enforced": False
        }
    
    project_id = project_info["project_id"]
    
    # Step 2: Get resume context
    resume_context = await handle_get_resume_context(project_id, None)
    
    # Step 3: Load cursor rules (try to load, but don't fail if it doesn't exist)
    cursor_rules_loaded = False
    cursor_rules_error = None
    try:
        cursor_rules_result = await handle_load_cursor_rules(project_id, path)
        cursor_rules_loaded = bool(cursor_rules_result.get("rules") or cursor_rules_result.get("content"))
    except Exception as e:
        cursor_rules_error = str(e)
        # Don't fail if cursor rules can't be loaded
    
    # Step 4: Build workflow checklist
    workflow_checklist = [
        "✅ Project identified",
        "✅ Resume context loaded",
        f"{'✅' if cursor_rules_loaded else '⚠️'} Cursor rules {'loaded' if cursor_rules_loaded else 'not found (will be generated if needed)'}",
        "📋 Next: Work on todos from resume_context.now.todos",
        "📋 Next: Update todo status with mcp_update_todo_status(todoId, 'in_progress') when starting",
        "📋 Next: Follow git workflow before committing (git status → git diff → git add → git commit → git push)",
        "📋 Next: Update todo status after commit: mcp_update_todo_status(todoId, 'tested') (only if tested!)",
        "📋 Next: Update todo status after merge: mcp_update_todo_status(todoId, 'done') (only if tested AND merged!)",
        "📋 Next: Use commit message format: {type}({scope}): {description} [feature:{featureId}]"
    ]
    
    # Extract next todos from resume context
    next_todos = []
    if isinstance(resume_context, dict):
        now = resume_context.get("now", {})
        if isinstance(now, dict):
            todos = now.get("todos", [])
            if isinstance(todos, list):
                next_todos = todos[:5]  # Get first 5 todos
    
    return {
        "workflow_enforced": True,
        "project": {
            "id": project_id,
            "name": project_info.get("name"),
            "description": project_info.get("description"),
            "status": project_info.get("status"),
        },
        "resume_context": resume_context,
        "cursor_rules_loaded": cursor_rules_loaded,
        "cursor_rules_error": cursor_rules_error,
        "workflow_checklist": workflow_checklist,
        "next_todos": next_todos,
        "active_elements": resume_context.get("now", {}).get("active_elements", []) if isinstance(resume_context, dict) else [],
        "blockers": resume_context.get("blockers", []) if isinstance(resume_context, dict) else [],
        "constraints": resume_context.get("constraints", []) if isinstance(resume_context, dict) else [],
        "reminder": """⚠️ WORKFLOW REMINDER:
        
        MANDATORY steps for this session:
        1. ✅ Project identified - DONE
        2. ✅ Resume context loaded - DONE
        3. ✅ Cursor rules loaded - DONE
        4. 📋 Work on todos from resume_context.now.todos
        5. 📋 Update todo status: in_progress → tested → done
        6. 📋 Follow git workflow: status → diff → add → commit → push
        7. 📋 Use commit format: {type}({scope}): {description} [feature:{featureId}]
        
        NEVER skip these steps!"""
    }
