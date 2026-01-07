"""MCP Tools for GitHub integration."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.database.models import GitHubBranch
from src.mcp.services.cache import cache_service
from src.services.github_service import GitHubService
from src.services.project_service import ProjectService
from src.services.feature_service import FeatureService
from src.services.element_service import ElementService
from src.services.todo_service import TodoService
from github import Github
from github.GithubException import GithubException


# GitHub service instance
_github_service: Optional[GitHubService] = None


def get_github_service() -> Optional[GitHubService]:
    """Get GitHub service instance."""
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service


def get_get_branches_tool() -> MCPTool:
    """Get branches tool definition."""
    return MCPTool(
        name="mcp_get_branches",
        description="Get branches for a project or feature",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "featureId": {"type": "string", "description": "Optional feature UUID"},
            },
            "required": ["projectId"],
        },
    )


async def handle_get_branches(project_id: str, feature_id: Optional[str] = None) -> dict:
    """Handle get branches tool call."""
    db = SessionLocal()
    try:
        query = db.query(GitHubBranch).filter(GitHubBranch.project_id == UUID(project_id))
        if feature_id:
            query = query.filter(GitHubBranch.feature_id == UUID(feature_id))

        branches = query.order_by(GitHubBranch.created_at.desc()).all()

        return {
            "project_id": project_id,
            "branches": [
                {
                    "id": str(b.id),
                    "name": b.branch_name,
                    "status": b.status,
                    "feature_id": str(b.feature_id) if b.feature_id else None,
                }
                for b in branches
            ],
            "count": len(branches),
        }
    finally:
        db.close()


def get_connect_github_repo_tool() -> MCPTool:
    """Get connect GitHub repo tool definition."""
    return MCPTool(
        name="mcp_connect_github_repo",
        description="Connect a GitHub repository to a project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "owner": {"type": "string", "description": "GitHub repository owner"},
                "repo": {"type": "string", "description": "GitHub repository name"},
            },
            "required": ["projectId", "owner", "repo"],
        },
    )


async def handle_connect_github_repo(project_id: str, owner: str, repo: str) -> dict:
    """Handle connect GitHub repo tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}

        # Use GitHubService to validate and get repo info
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        if not github_service.validate_repo_access(owner, repo):
            return {"error": "Cannot access GitHub repository"}

        repo_info = github_service.get_repo_info(owner, repo)
        if not repo_info:
            return {"error": "Failed to get repository information"}

        # Use ProjectService to update project
        updated_project = ProjectService.update_project(
            db=db,
            project_id=UUID(project_id),
            github_repo_url=repo_info["url"],
            github_repo_id=str(repo_info["id"]),
        )
        
        if not updated_project:
            return {"error": "Failed to update project"}
        
        project = updated_project

        # Invalidate cache
        cache_service.delete(f"project:{project_id}:*")

        return {
            "project_id": project_id,
            "github_repo_url": project.github_repo_url,
            "github_repo_id": project.github_repo_id,
            "repo_info": repo_info,
        }
    finally:
        db.close()


def get_get_repo_info_tool() -> MCPTool:
    """Get repo info tool definition."""
    return MCPTool(
        name="mcp_get_repo_info",
        description="Get GitHub repository information for a project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
            },
            "required": ["projectId"],
        },
    )


async def handle_get_repo_info(project_id: str) -> dict:
    """Handle get repo info tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Use GitHubService to get repo info
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        repo_info = github_service.get_repo_info(owner, repo)
        if not repo_info:
            return {"error": "Failed to fetch repository information"}

        return {
            "project_id": project_id,
            "repo_info": repo_info,
        }
    finally:
        db.close()


def get_link_element_to_issue_tool() -> MCPTool:
    """Get link element to issue tool definition."""
    return MCPTool(
        name="mcp_link_element_to_issue",
        description="Link a project element to a GitHub issue",
        inputSchema={
            "type": "object",
            "properties": {
                "elementId": {"type": "string", "description": "Element UUID"},
                "issueNumber": {"type": "integer", "description": "GitHub issue number"},
            },
            "required": ["elementId", "issueNumber"],
        },
    )


async def handle_link_element_to_issue(element_id: str, issue_number: int) -> dict:
    """Handle link element to issue tool call."""
    db = SessionLocal()
    try:
        # Use ElementService to get element
        element = ElementService.get_element_by_id(db, UUID(element_id))
        if not element:
            return {"error": "Element not found"}

        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, element.project_id)
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get issue from GitHub to validate
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            issue = repository.get_issue(issue_number)
            issue_url = issue.html_url
        except GithubException as e:
            return {"error": f"GitHub issue not found: {e}"}

        # Update element directly (ElementService doesn't have update method for GitHub fields)
        from src.database.models import ProjectElement
        element = db.query(ProjectElement).filter(ProjectElement.id == UUID(element_id)).first()
        element.github_issue_number = issue_number
        element.github_issue_url = issue_url
        db.commit()
        db.refresh(element)

        # Invalidate cache
        cache_service.delete(f"project:{project.id}:*")

        return {
            "element_id": element_id,
            "issue_number": issue_number,
            "issue_url": issue_url,
        }
    finally:
        db.close()


def get_get_github_issue_tool() -> MCPTool:
    """Get GitHub issue tool definition."""
    return MCPTool(
        name="mcp_get_github_issue",
        description="Get GitHub issue information",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "issueNumber": {"type": "integer", "description": "GitHub issue number"},
            },
            "required": ["projectId", "issueNumber"],
        },
    )


async def handle_get_github_issue(project_id: str, issue_number: int) -> dict:
    """Handle get GitHub issue tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get issue from GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            issue = repository.get_issue(issue_number)
            return {
                "project_id": project_id,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "url": issue.html_url,
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "assignees": [assignee.login for assignee in issue.assignees],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                },
            }
        except GithubException as e:
            return {"error": f"GitHub issue not found: {e}"}
    finally:
        db.close()


def get_create_github_issue_tool() -> MCPTool:
    """Get create GitHub issue tool definition."""
    return MCPTool(
        name="mcp_create_github_issue",
        description="Create a GitHub issue",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body/description"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional labels"},
                "elementId": {"type": "string", "description": "Optional element ID to link"},
            },
            "required": ["projectId", "title"],
        },
    )


async def handle_create_github_issue(
    project_id: str,
    title: str,
    body: Optional[str] = None,
    labels: Optional[List[str]] = None,
    element_id: Optional[str] = None,
) -> dict:
    """Handle create GitHub issue tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Create issue on GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            issue = repository.create_issue(
                title=title,
                body=body or "",
                labels=labels or [],
            )

            # Link to element if provided
            if element_id:
                element = ElementService.get_element_by_id(db, UUID(element_id))
                if element and element.project_id == project.id:
                    # Update element directly (ElementService doesn't have update method for GitHub fields)
                    from src.database.models import ProjectElement
                    element = db.query(ProjectElement).filter(ProjectElement.id == UUID(element_id)).first()
                    element.github_issue_number = issue.number
                    element.github_issue_url = issue.html_url
                    db.commit()

            # Invalidate cache
            cache_service.delete(f"project:{project_id}:*")

            return {
                "project_id": project_id,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "state": issue.state,
                },
                "element_id": element_id if element_id else None,
            }
        except GithubException as e:
            return {"error": f"Failed to create GitHub issue: {e}"}
    finally:
        db.close()


def get_link_todo_to_pr_tool() -> MCPTool:
    """Get link todo to PR tool definition."""
    return MCPTool(
        name="mcp_link_todo_to_pr",
        description="Link a todo to a GitHub pull request",
        inputSchema={
            "type": "object",
            "properties": {
                "todoId": {"type": "string", "description": "Todo UUID"},
                "prNumber": {"type": "integer", "description": "GitHub PR number"},
            },
            "required": ["todoId", "prNumber"],
        },
    )


async def handle_link_todo_to_pr(todo_id: str, pr_number: int) -> dict:
    """Handle link todo to PR tool call."""
    db = SessionLocal()
    try:
        # Use TodoService to get todo
        todo = TodoService.get_todo_by_id(db, UUID(todo_id))
        if not todo:
            return {"error": "Todo not found"}

        # Use ElementService to get element
        element = ElementService.get_element_by_id(db, todo.element_id)
        if not element:
            return {"error": "Element not found"}

        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, element.project_id)
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get PR from GitHub to validate
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            pr_url = pr.html_url
        except GithubException as e:
            return {"error": f"GitHub PR not found: {e}"}

        # Update todo directly (TodoService doesn't have update method for GitHub fields)
        from src.database.models import Todo
        todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
        todo.github_pr_number = pr_number
        todo.github_pr_url = pr_url
        db.commit()
        db.refresh(todo)

        # Invalidate cache
        cache_service.delete(f"project:{project.id}:*")

        return {
            "todo_id": todo_id,
            "pr_number": pr_number,
            "pr_url": pr_url,
        }
    finally:
        db.close()


def get_get_github_pr_tool() -> MCPTool:
    """Get GitHub PR tool definition."""
    return MCPTool(
        name="mcp_get_github_pr",
        description="Get GitHub pull request information",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "prNumber": {"type": "integer", "description": "GitHub PR number"},
            },
            "required": ["projectId", "prNumber"],
        },
    )


async def handle_get_github_pr(project_id: str, pr_number: int) -> dict:
    """Handle get GitHub PR tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get PR from GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            return {
                "project_id": project_id,
                "pr": {
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "url": pr.html_url,
                    "state": pr.state,
                    "merged": pr.merged,
                    "mergeable": pr.mergeable,
                    "head": {
                        "ref": pr.head.ref,
                        "sha": pr.head.sha,
                    },
                    "base": {
                        "ref": pr.base.ref,
                        "sha": pr.base.sha,
                    },
                    "labels": [label.name for label in pr.labels],
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                },
            }
        except GithubException as e:
            return {"error": f"GitHub PR not found: {e}"}
    finally:
        db.close()


def get_create_github_pr_tool() -> MCPTool:
    """Get create GitHub PR tool definition."""
    return MCPTool(
        name="mcp_create_github_pr",
        description="Create a GitHub pull request",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "title": {"type": "string", "description": "PR title"},
                "body": {"type": "string", "description": "PR body/description"},
                "head": {"type": "string", "description": "Head branch name"},
                "base": {"type": "string", "description": "Base branch name (default: main)"},
                "todoId": {"type": "string", "description": "Optional todo ID to link"},
            },
            "required": ["projectId", "title", "head"],
        },
    )


async def handle_create_github_pr(
    project_id: str,
    title: str,
    head: str,
    body: Optional[str] = None,
    base: str = "main",
    todo_id: Optional[str] = None,
) -> dict:
    """Handle create GitHub PR tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Create PR on GitHub
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            repository = github_service.client.get_repo(f"{owner}/{repo}")
            pr = repository.create_pull(
                title=title,
                body=body or "",
                head=head,
                base=base,
            )

            # Link to todo if provided
            if todo_id:
                todo = TodoService.get_todo_by_id(db, UUID(todo_id))
                if todo:
                    element = ElementService.get_element_by_id(db, todo.element_id)
                    if element and element.project_id == project.id:
                        # Update todo directly (TodoService doesn't have update method for GitHub fields)
                        from src.database.models import Todo
                        todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
                        todo.github_pr_number = pr.number
                        todo.github_pr_url = pr.html_url
                        db.commit()

            # Invalidate cache
            cache_service.delete(f"project:{project_id}:*")

            return {
                "project_id": project_id,
                "pr": {
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url,
                    "state": pr.state,
                },
                "todo_id": todo_id if todo_id else None,
            }
        except GithubException as e:
            return {"error": f"Failed to create GitHub PR: {e}"}
    finally:
        db.close()


def get_create_branch_for_feature_tool() -> MCPTool:
    """Get create branch for feature tool definition."""
    return MCPTool(
        name="mcp_create_branch_for_feature",
        description="Create a GitHub branch for a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
                "baseBranch": {"type": "string", "description": "Base branch name (default: main)"},
            },
            "required": ["featureId"],
        },
    )


async def handle_create_branch_for_feature(feature_id: str, base_branch: str = "main") -> dict:
    """Handle create branch for feature tool call."""
    db = SessionLocal()
    try:
        # Use FeatureService to get feature
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            return {"error": "Feature not found"}

        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, feature.project_id)
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Generate branch name from feature name
        branch_name = f"feature/{feature.name.lower().replace(' ', '-').replace('_', '-')[:50]}"

        # Use GitHubService to create branch
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}

        try:
            branch_result = github_service.create_branch(owner, repo, branch_name, base_branch)
            if not branch_result:
                return {"error": "Failed to create GitHub branch"}

            # Create GitHubBranch record
            github_branch = GitHubBranch(
                project_id=project.id,
                feature_id=feature.id,
                branch_name=branch_name,
                base_branch=base_branch,
                status="active",
            )
            db.add(github_branch)
            db.commit()
            db.refresh(github_branch)

            # Invalidate cache
            cache_service.delete(f"project:{project.id}:*")

            return {
                "feature_id": feature_id,
                "branch": {
                    "id": str(github_branch.id),
                    "name": branch_name,
                    "base_branch": base_branch,
                    "status": "active",
                },
            }
        except GithubException as e:
            return {"error": f"Failed to create GitHub branch: {e}"}
    finally:
        db.close()


def get_get_active_branch_tool() -> MCPTool:
    """Get active branch tool definition."""
    return MCPTool(
        name="mcp_get_active_branch",
        description="Get the active branch from working directory or project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
            },
            "required": ["projectId"],
        },
    )


async def handle_get_active_branch(project_id: str) -> dict:
    """Handle get active branch tool call."""
    import subprocess
    import os
    
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Try to get current branch from git
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                
                # Check if branch is linked to a feature
                from src.database.models import GitHubBranch
                github_branch = db.query(GitHubBranch).filter(
                    GitHubBranch.project_id == UUID(project_id),
                    GitHubBranch.branch_name == current_branch,
                ).first()

                return {
                    "project_id": project_id,
                    "branch": {
                        "name": current_branch,
                        "feature_id": str(github_branch.feature_id) if github_branch and github_branch.feature_id else None,
                        "status": github_branch.status if github_branch else None,
                    },
                }
        except Exception:
            pass

        return {"error": "Could not determine active branch"}
    finally:
        db.close()


def get_link_branch_to_feature_tool() -> MCPTool:
    """Get link branch to feature tool definition."""
    return MCPTool(
        name="mcp_link_branch_to_feature",
        description="Link a GitHub branch to a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
                "branchName": {"type": "string", "description": "Branch name"},
            },
            "required": ["featureId", "branchName"],
        },
    )


async def handle_link_branch_to_feature(feature_id: str, branch_name: str) -> dict:
    """Handle link branch to feature tool call."""
    db = SessionLocal()
    try:
        feature = db.query(Feature).filter(Feature.id == UUID(feature_id)).first()
        if not feature:
            return {"error": "Feature not found"}

        project = db.query(Project).filter(Project.id == feature.project_id).first()
        if not project:
            return {"error": "Project not found"}

        # Check if branch already exists
        existing_branch = db.query(GitHubBranch).filter(
            GitHubBranch.project_id == project.id,
            GitHubBranch.branch_name == branch_name,
        ).first()

        if existing_branch:
            # Update existing branch
            existing_branch.feature_id = feature.id
            db.commit()
            db.refresh(existing_branch)
            return {
                "feature_id": feature_id,
                "branch": {
                    "id": str(existing_branch.id),
                    "name": branch_name,
                    "status": existing_branch.status,
                },
            }
        else:
            # Create new branch record
            github_branch = GitHubBranch(
                project_id=project.id,
                feature_id=feature.id,
                branch_name=branch_name,
                base_branch="main",
                status="active",
            )
            db.add(github_branch)
            db.commit()
            db.refresh(github_branch)

            # Invalidate cache
            cache_service.delete(f"project:{project.id}:*")

            return {
                "feature_id": feature_id,
                "branch": {
                    "id": str(github_branch.id),
                    "name": branch_name,
                    "status": "active",
                },
            }
    finally:
        db.close()


def get_get_feature_branches_tool() -> MCPTool:
    """Get feature branches tool definition."""
    return MCPTool(
        name="mcp_get_feature_branches",
        description="Get branches for a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
            },
            "required": ["featureId"],
        },
    )


async def handle_get_feature_branches(feature_id: str) -> dict:
    """Handle get feature branches tool call."""
    db = SessionLocal()
    try:
        feature = db.query(Feature).filter(Feature.id == UUID(feature_id)).first()
        if not feature:
            return {"error": "Feature not found"}

        branches = db.query(GitHubBranch).filter(
            GitHubBranch.feature_id == UUID(feature_id),
        ).order_by(GitHubBranch.created_at.desc()).all()

        return {
            "feature_id": feature_id,
            "branches": [
                {
                    "id": str(b.id),
                    "name": b.branch_name,
                    "base_branch": b.base_branch,
                    "status": b.status,
                    "ahead_count": b.ahead_count,
                    "behind_count": b.behind_count,
                    "has_conflicts": b.has_conflicts,
                }
                for b in branches
            ],
            "count": len(branches),
        }
    finally:
        db.close()


def get_get_branch_status_tool() -> MCPTool:
    """Get branch status tool definition."""
    return MCPTool(
        name="mcp_get_branch_status",
        description="Get branch status (ahead/behind, conflicts)",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "branchName": {"type": "string", "description": "Branch name"},
            },
            "required": ["projectId", "branchName"],
        },
    )


async def handle_get_branch_status(project_id: str, branch_name: str) -> dict:
    """Handle get branch status tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get branch from database
        github_branch = db.query(GitHubBranch).filter(
            GitHubBranch.project_id == UUID(project_id),
            GitHubBranch.branch_name == branch_name,
        ).first()

        # Get GitHub client
        client = get_github_client()
        if not client:
            return {"error": "GitHub token not configured"}

        try:
            repository = client.get_repo(f"{owner}/{repo}")
            
            # Compare branches
            base_branch = github_branch.base_branch if github_branch else "main"
            comparison = repository.compare(base_branch, branch_name)
            
            ahead_count = comparison.ahead_by
            behind_count = comparison.behind_by
            has_conflicts = comparison.mergeable is False

            # Update branch record if exists
            if github_branch:
                github_branch.ahead_count = ahead_count
                github_branch.behind_count = behind_count
                github_branch.has_conflicts = has_conflicts
                db.commit()

            return {
                "project_id": project_id,
                "branch": {
                    "name": branch_name,
                    "base_branch": base_branch,
                    "ahead_count": ahead_count,
                    "behind_count": behind_count,
                    "has_conflicts": has_conflicts,
                    "status": github_branch.status if github_branch else None,
                },
            }
        except GithubException as e:
            return {"error": f"Failed to get branch status: {e}"}
    finally:
        db.close()


def get_get_commits_for_feature_tool() -> MCPTool:
    """Get commits for feature tool definition."""
    return MCPTool(
        name="mcp_get_commits_for_feature",
        description="Get commits for a feature",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
            },
            "required": ["featureId"],
        },
    )


async def handle_get_commits_for_feature(feature_id: str) -> dict:
    """Handle get commits for feature tool call."""
    db = SessionLocal()
    try:
        feature = db.query(Feature).filter(Feature.id == UUID(feature_id)).first()
        if not feature:
            return {"error": "Feature not found"}

        project = db.query(Project).filter(Project.id == feature.project_id).first()
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Get branches for feature
        branches = db.query(GitHubBranch).filter(
            GitHubBranch.feature_id == UUID(feature_id),
        ).all()

        if not branches:
            return {
                "feature_id": feature_id,
                "commits": [],
                "count": 0,
            }

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            return {"error": "Invalid GitHub repository URL format"}

        owner, repo = repo_parts

        # Get GitHub client
        client = get_github_client()
        if not client:
            return {"error": "GitHub token not configured"}

        try:
            repository = client.get_repo(f"{owner}/{repo}")
            all_commits = []

            # Get commits from all branches
            for branch in branches:
                try:
                    commits = repository.get_commits(sha=branch.branch_name)
                    for commit in commits[:50]:  # Limit to 50 commits per branch
                        # Parse commit message for feature ID
                        commit_data = {
                            "sha": commit.sha,
                            "message": commit.commit.message,
                            "author": commit.commit.author.name if commit.commit.author else None,
                            "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None,
                            "branch": branch.branch_name,
                        }
                        all_commits.append(commit_data)
                except GithubException:
                    continue

            return {
                "feature_id": feature_id,
                "commits": all_commits[:100],  # Limit total to 100
                "count": len(all_commits),
            }
        except GithubException as e:
            return {"error": f"Failed to get commits: {e}"}
    finally:
        db.close()


def get_parse_commit_message_tool() -> MCPTool:
    """Get parse commit message tool definition."""
    return MCPTool(
        name="mcp_parse_commit_message",
        description="Parse commit message for metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "commitMessage": {"type": "string", "description": "Commit message"},
            },
            "required": ["commitMessage"],
        },
    )


async def handle_parse_commit_message(commit_message: str) -> dict:
    """Handle parse commit message tool call."""
    import re
    
    # Parse conventional commit format: "type(scope): description [feature:id]"
    pattern = r"^(\w+)(?:\(([^)]+)\))?:\s*(.+?)(?:\s*\[feature:([^\]]+)\])?$"
    match = re.match(pattern, commit_message.split("\n")[0])
    
    if match:
        commit_type, scope, description, feature_id = match.groups()
        return {
            "type": commit_type,
            "scope": scope,
            "description": description.strip(),
            "feature_id": feature_id,
            "format": "conventional",
        }
    
    # Fallback: simple parsing
    return {
        "type": None,
        "scope": None,
        "description": commit_message.split("\n")[0],
        "feature_id": None,
        "format": "simple",
    }
