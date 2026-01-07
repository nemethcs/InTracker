"""MCP Tools for project import and structure generation."""
from typing import Optional, List, Dict
from uuid import UUID
from pathlib import Path
import os
import json
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.services.cache import cache_service
from src.models import Project, ProjectElement, Todo, Feature, FeatureElement
from sqlalchemy import func


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
    
    db = get_db_session()
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}
        
        # Check if project already has elements
        existing_elements = db.query(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id)
        ).count()
        
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
            
            element = ProjectElement(
                project_id=UUID(project_id),
                parent_id=parent_element_id,
                type=element_type,
                title=element_title,
                description=description,
                status="new",
                position=None,
            )
            db.add(element)
            db.commit()
            db.refresh(element)
            
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


def get_import_github_issues_tool() -> MCPTool:
    """Get import GitHub issues tool definition."""
    return MCPTool(
        name="mcp_import_github_issues",
        description="Import GitHub issues as todos for a project. Creates todos from open GitHub issues and optionally links them to project elements. Useful for migrating existing projects to InTracker.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Only import issues with these labels",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Issue state to import (default: open)",
                    "default": "open",
                },
                "createElements": {
                    "type": "boolean",
                    "description": "Create project elements for issues without matching elements (default: true)",
                    "default": True,
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_import_github_issues(
    project_id: str,
    labels: Optional[List[str]] = None,
    state: str = "open",
    create_elements: bool = True,
) -> dict:
    """Handle import GitHub issues tool call."""
    from src.tools.github import get_github_client
    from github import Github
    from github.GithubException import GithubException
    
    db = get_db_session()
    try:
        # Verify project exists and has GitHub repo
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}
        
        if not project.github_repo_url:
            return {"error": "Project does not have a GitHub repository connected"}
        
        # Parse GitHub URL
        github_url = project.github_repo_url
        if "github.com/" in github_url:
            parts = github_url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) < 2:
                return {"error": "Invalid GitHub repository URL"}
            owner, repo = parts[0], parts[1]
        else:
            return {"error": "Invalid GitHub repository URL format"}
        
        # Get GitHub client
        client = get_github_client()
        if not client:
            return {"error": "GitHub token not configured"}
        
        # Get repository
        try:
            github_repo = client.get_repo(f"{owner}/{repo}")
        except Exception as e:
            return {"error": f"Failed to access GitHub repository: {str(e)}"}
        
        # Get issues
        issues = []
        try:
            if state == "all":
                github_issues = github_repo.get_issues(state="all")
            else:
                github_issues = github_repo.get_issues(state=state)
            
            for issue in github_issues:
                # Skip pull requests
                if issue.pull_request:
                    continue
                
                # Filter by labels if provided
                if labels:
                    issue_labels = [label.name for label in issue.labels]
                    if not any(label in issue_labels for label in labels):
                        continue
                
                issues.append(issue)
        except Exception as e:
            return {"error": f"Failed to fetch GitHub issues: {str(e)}"}
        
        # Import issues as todos
        todos_created = []
        elements_created = []
        
        # Get or create root element for issues without specific element
        root_elements = db.query(ProjectElement).filter(
            ProjectElement.project_id == UUID(project_id),
            ProjectElement.parent_id.is_(None),
            ProjectElement.type == "module",
        ).first()
        
        if not root_elements and create_elements:
            root_elements = ProjectElement(
                project_id=UUID(project_id),
                type="module",
                title="GitHub Issues",
                description="Imported from GitHub issues",
                status="new",
                parent_id=None,
            )
            db.add(root_elements)
            db.commit()
            db.refresh(root_elements)
            elements_created.append({
                "id": str(root_elements.id),
                "title": "GitHub Issues",
            })
        
        for issue in issues:
            # Determine element (try to match by title or create new)
            element_id = root_elements.id if root_elements else None
            
            # Create todo from issue
            todo = Todo(
                element_id=element_id,
                feature_id=None,
                title=issue.title,
                description=issue.body or f"GitHub Issue #{issue.number}",
                status="new" if issue.state == "open" else "done",
                priority="high" if any(label.name.lower() in ["bug", "critical", "urgent"] for label in issue.labels) else "medium",
                github_issue_number=issue.number,
                github_issue_url=issue.html_url,
                version=1,
            )
            db.add(todo)
            db.commit()
            db.refresh(todo)
            
            todos_created.append({
                "id": str(todo.id),
                "title": todo.title,
                "github_issue_number": issue.number,
                "github_issue_url": issue.html_url,
            })
        
        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        
        return {
            "success": True,
            "project_id": project_id,
            "todos_created": len(todos_created),
            "elements_created": len(elements_created),
            "todos": todos_created,
            "elements": elements_created,
            "message": f"Imported {len(todos_created)} GitHub issues as todos",
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        db.close()


def get_import_github_milestones_tool() -> MCPTool:
    """Get import GitHub milestones tool definition."""
    return MCPTool(
        name="mcp_import_github_milestones",
        description="Import GitHub milestones as features for a project. Creates features from GitHub milestones and links related issues as todos. Useful for migrating existing projects to InTracker.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Milestone state to import (default: open)",
                    "default": "open",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_import_github_milestones(
    project_id: str,
    state: str = "open",
) -> dict:
    """Handle import GitHub milestones tool call."""
    from src.tools.github import get_github_client
    from github import Github
    from github.GithubException import GithubException
    
    db = get_db_session()
    try:
        # Verify project exists and has GitHub repo
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}
        
        if not project.github_repo_url:
            return {"error": "Project does not have a GitHub repository connected"}
        
        # Parse GitHub URL
        github_url = project.github_repo_url
        if "github.com/" in github_url:
            parts = github_url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) < 2:
                return {"error": "Invalid GitHub repository URL"}
            owner, repo = parts[0], parts[1]
        else:
            return {"error": "Invalid GitHub repository URL format"}
        
        # Get GitHub client
        client = get_github_client()
        if not client:
            return {"error": "GitHub token not configured"}
        
        # Get repository
        try:
            github_repo = client.get_repo(f"{owner}/{repo}")
        except Exception as e:
            return {"error": f"Failed to access GitHub repository: {str(e)}"}
        
        # Get milestones
        milestones = []
        try:
            if state == "all":
                github_milestones = github_repo.get_milestones(state="all")
            else:
                github_milestones = github_repo.get_milestones(state=state)
            
            for milestone in github_milestones:
                milestones.append(milestone)
        except Exception as e:
            return {"error": f"Failed to fetch GitHub milestones: {str(e)}"}
        
        # Import milestones as features
        features_created = []
        
        for milestone in milestones:
            # Create feature from milestone
            feature = Feature(
                project_id=UUID(project_id),
                name=milestone.title,
                description=milestone.description or f"GitHub Milestone: {milestone.title}",
                status="new" if milestone.state == "open" else "done",
                total_todos=0,
                completed_todos=0,
                progress_percentage=0,
            )
            db.add(feature)
            db.flush()
            
            # Get issues for this milestone and create todos
            todos_count = 0
            try:
                issues = github_repo.get_issues(milestone=milestone, state="all")
                for issue in issues:
                    if issue.pull_request:
                        continue
                    
                    # Find or create element for this todo
                    root_elements = db.query(ProjectElement).filter(
                        ProjectElement.project_id == UUID(project_id),
                        ProjectElement.parent_id.is_(None),
                    ).first()
                    
                    if root_elements:
                        todo = Todo(
                            element_id=root_elements.id,
                            feature_id=feature.id,
                            title=issue.title,
                            description=issue.body or f"GitHub Issue #{issue.number}",
                            status="new" if issue.state == "open" else "done",
                            priority="high" if any(label.name.lower() in ["bug", "critical", "urgent"] for label in issue.labels) else "medium",
                            github_issue_number=issue.number,
                            github_issue_url=issue.html_url,
                            version=1,
                        )
                        db.add(todo)
                        db.commit()
                        db.refresh(todo)
                        todos_count += 1
                        
                        # Update feature progress
                        total = db.query(func.count(Todo.id)).filter(Todo.feature_id == feature.id).scalar()
                        completed = db.query(func.count(Todo.id)).filter(Todo.feature_id == feature.id, Todo.status == "done").scalar()
                        percentage = int((completed / total * 100)) if total > 0 else 0
                        feature.total_todos = total
                        feature.completed_todos = completed
                        feature.progress_percentage = percentage
                        db.commit()
            except Exception as e:
                print(f"Warning: Failed to import issues for milestone {milestone.title}: {e}")
            
            features_created.append({
                "id": str(feature.id),
                "name": feature.name,
                "todos_created": todos_count,
            })
        
        # Invalidate cache
        cache_service.clear_pattern(f"project:{project_id}:*")
        
        return {
            "success": True,
            "project_id": project_id,
            "features_created": len(features_created),
            "features": features_created,
            "message": f"Imported {len(features_created)} GitHub milestones as features",
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        db.close()


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
    
    db = get_db_session()
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
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
