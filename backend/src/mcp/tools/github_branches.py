"""MCP Tools for GitHub branches."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.database.models import GitHubBranch, Feature, Project
from src.mcp.services.cache import cache_service
from src.services.github_service import GitHubService
from src.services.project_service import ProjectService
from src.services.feature_service import FeatureService
from github.GithubException import GithubException
from .github_repository import get_github_service
from src.mcp.utils.project_access import validate_project_access


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
        # Use FeatureService to get feature
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            return {"error": "Feature not found"}

        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, feature.project_id)
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
        # Use FeatureService to get feature
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
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

        # Get GitHub client (fix: use get_github_service().client)
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}
        client = github_service.client

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
        # Use FeatureService to get feature
        feature = FeatureService.get_feature_by_id(db, UUID(feature_id))
        if not feature:
            return {"error": "Feature not found"}

        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, feature.project_id)
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

        # Get GitHub client (fix: use get_github_service().client)
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}
        client = github_service.client

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
