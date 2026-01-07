"""Project resources for MCP server."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from src.database.base import get_db_session
from src.database.models import Project
from src.services.rules_generator import rules_generator


def get_project_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get project resources."""
    resources = []
    
    if project_id:
        # Project-specific resources
        resources.append(
            Resource(
                uri=f"intracker://project/{project_id}",
                name=f"Project: {project_id}",
                mimeType="application/json",
                description=f"Project information for {project_id}",
            )
        )
        resources.append(
            Resource(
                uri=f"intracker://project/{project_id}/cursor-rules",
                name=f"Cursor Rules: {project_id}",
                mimeType="text/markdown",
                description=f"Cursor rules for project {project_id}",
            )
        )
    else:
        # List all projects
        db = get_db_session()
        try:
            projects = db.query(Project).all()
            for project in projects:
                resources.append(
                    Resource(
                        uri=f"intracker://project/{project.id}",
                        name=f"Project: {project.name}",
                        mimeType="application/json",
                        description=f"Project information for {project.name}",
                    )
                )
                resources.append(
                    Resource(
                        uri=f"intracker://project/{project.id}/cursor-rules",
                        name=f"Cursor Rules: {project.name}",
                        mimeType="text/markdown",
                        description=f"Cursor rules for project {project.name}",
                    )
                )
        finally:
            db.close()
    
    return resources


async def read_project_resource(uri: str) -> str:
    """Read project resource."""
    import json
    
    # Parse URI: intracker://project/{project_id}
    if not uri.startswith("intracker://project/"):
        raise ValueError(f"Invalid resource URI: {uri}")
    
    uri_parts = uri.replace("intracker://project/", "").split("/")
    project_id = uri_parts[0]
    
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        return json.dumps({
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "cursor_instructions": project.cursor_instructions,
            "github_repo_url": project.github_repo_url,
        }, indent=2)
    finally:
        db.close()


async def read_cursor_rules_resource(project_id: str) -> str:
    """Read cursor rules resource and generate .cursor/rules/intracker-project-rules.mdc file."""
    import os
    from pathlib import Path
    
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Generate cursor rules using the rules generator service
        rules_content = rules_generator.generate_rules(project)
        
        # Try to write to .cursor/rules/intracker-project-rules.mdc in project directory
        # First, try to find project directory by checking for .intracker/config.json
        project_dir = None
        
        # Check common locations
        possible_paths = [
            Path.cwd(),  # Current working directory (most likely)
            Path("/Users/ncs/Desktop/projects") / project.name,
            Path("/app"),  # Docker container working directory
        ]
        
        # Also check if github_repo_url gives us a hint
        if project.github_repo_url:
            # Try to extract repo name and check common locations
            repo_name = project.github_repo_url.split("/")[-1].replace(".git", "")
            possible_paths.insert(1, Path("/Users/ncs/Desktop/projects") / repo_name)
            possible_paths.insert(2, Path("/app") / repo_name)
        
        # Also check environment variable for project root
        import os
        project_root = os.getenv("PROJECT_ROOT")
        if project_root:
            possible_paths.insert(0, Path(project_root))
        
        for path in possible_paths:
            config_file = path / ".intracker" / "config.json"
            if config_file.exists():
                # Verify it's the right project
                try:
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        if config.get("project_id") == str(project.id):
                            project_dir = path
                            break
                except Exception:
                    continue
        
        # If found, write the rules file
        if project_dir:
            rules_dir = project_dir / ".cursor" / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            rules_file = rules_dir / "intracker-project-rules.mdc"
            
            try:
                rules_file.write_text(rules_content, encoding="utf-8")
                # Add note to content that file was written
                rules_content += f"\n\n> **Note:** This file has been automatically written to: `{rules_file}`\n"
            except Exception as e:
                # If file write fails, just continue with content
                rules_content += f"\n\n> **Warning:** Could not write to file: {e}\n"
        else:
            # If project directory not found, add note
            rules_content += "\n\n> **Note:** Project directory not found. Rules file not written automatically.\n"
            rules_content += "> To enable automatic file generation, create `.intracker/config.json` in your project root.\n"

        return rules_content
    finally:
        db.close()
