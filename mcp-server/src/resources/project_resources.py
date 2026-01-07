"""MCP Resources for projects."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.models import Project


def get_project_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get project resources."""
    db = get_db_session()
    try:
        if project_id:
            project = db.query(Project).filter(Project.id == UUID(project_id)).first()
            if project:
                resources = [
                    Resource(
                        uri=f"intracker://project/{project.id}",
                        name=f"Project: {project.name}",
                        description=project.description or "",
                        mimeType="application/json",
                    ),
                    Resource(
                        uri=f"intracker://project/{project.id}/cursor-rules",
                        name=f"Cursor Rules: {project.name}",
                        description="Cursor AI instructions for this project",
                        mimeType="text/markdown",
                    ),
                ]
                return resources
            return []
        else:
            # List all projects
            projects = db.query(Project).all()
            resources = []
            for p in projects:
                resources.append(
                    Resource(
                        uri=f"intracker://project/{p.id}",
                        name=f"Project: {p.name}",
                        description=p.description or "",
                        mimeType="application/json",
                    )
                )
                resources.append(
                    Resource(
                        uri=f"intracker://project/{p.id}/cursor-rules",
                        name=f"Cursor Rules: {p.name}",
                        description="Cursor AI instructions for this project",
                        mimeType="text/markdown",
                    )
                )
            return resources
    finally:
        db.close()


async def read_project_resource(uri: str) -> str:
    """Read project resource."""
    # Convert URI to string if it's not already
    uri_str = str(uri)
    
    # Parse URI: intracker://project/{project_id} or intracker://project/{project_id}/cursor-rules
    if not uri_str.startswith("intracker://project/"):
        raise ValueError(f"Invalid project resource URI: {uri_str}")

    # Check if it's cursor-rules resource
    if uri_str.endswith("/cursor-rules"):
        project_id = uri_str.replace("intracker://project/", "").replace("/cursor-rules", "")
        return await read_cursor_rules_resource(project_id)
    
    # Regular project resource
    project_id = uri_str.replace("intracker://project/", "")
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        import json
        return json.dumps({
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "tags": project.tags,
            "technology_tags": project.technology_tags,
            "cursor_instructions": project.cursor_instructions,
            "resume_context": project.resume_context,
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

        # Generate cursor rules content from project cursor_instructions
        cursor_instructions = project.cursor_instructions or ""
        
        # Build cursor rules markdown content
        rules_content = f"""---
name: intracker-project-rules
description: Cursor AI instructions for {project.name}
---

# Cursor Rules for {project.name}

{project.description or ''}

## Project Information

- **Project ID:** {project.id}
- **Status:** {project.status}
- **Tags:** {', '.join(project.tags) if project.tags else 'None'}
- **Technology Tags:** {', '.join(project.technology_tags) if project.technology_tags else 'None'}

## Cursor Instructions

{cursor_instructions}

## Development Rules

### Environment Strategy

- **MVP Phase:** All development in local Docker environment
- **Post-MVP:** Deploy to Azure (staging → production)
- **Never deploy to Azure during MVP development**

### Docker Setup

```yaml
# docker-compose.yml
services:
  postgres: postgres:16 (port 5432)
  redis: redis:7-alpine (port 6379)
  backend: Node.js API (port 3000)
  mcp-server: MCP Server (port 3001)
```

**Commands:**
- Start: `docker-compose up -d`
- Stop: `docker-compose down`
- Reset: `docker-compose down -v && docker-compose up -d`
- Logs: `docker-compose logs -f [service]`

### Development Workflow

1. Start Docker: `docker-compose up -d`
2. Work on next unchecked todo item
3. Test locally in Docker
4. Mark todo as done
5. Commit with todo reference

### Commit Message Format

```
{{type}}({{component}}): {{description}} [feature:{{featureId}}]

- [x] Todo item 1
- [x] Todo item 2
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### Coding Standards

- TypeScript strict mode
- ESLint + Prettier
- No `any` types
- Error handling everywhere
- Document complex logic

### Testing

- **Database:** Prisma Studio, SQL queries
- **Backend:** Postman/Insomnia collection
- **MCP:** Test in Cursor, verify tools/resources work
- **E2E:** Full workflow test

---

**Generated by InTracker MCP Server**
**Last updated:** {project.updated_at.isoformat() if project.updated_at else 'Unknown'}
"""

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
