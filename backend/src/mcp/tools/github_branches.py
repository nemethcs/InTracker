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


def get_get_branch_info_tool() -> MCPTool:
    """Get branch info tool definition - consolidated tool for all branch operations.
    
    This tool consolidates multiple branch-related tools:
    - Get branches for a project or feature
    - Get branch status (ahead/behind, conflicts)
    - Get commits for branches
    
    Usage:
    - projectId only: Get all branches for project
    - projectId + featureId: Get branches for feature with status and commits
    - projectId + branchName: Get detailed info for specific branch
    - projectId + featureId + branchName: Get detailed info for feature's branch
    """
    return MCPTool(
        name="mcp_get_branch_info",
        description="Get comprehensive branch information for a project, feature, or specific branch. Consolidates branch listing, status checking, and commit retrieval into a single tool.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "featureId": {"type": "string", "description": "Optional feature UUID to filter branches"},
                "branchName": {"type": "string", "description": "Optional specific branch name for detailed info"},
                "includeStatus": {"type": "boolean", "description": "Include branch status (ahead/behind, conflicts) - default: true"},
                "includeCommits": {"type": "boolean", "description": "Include commits for branches - default: false"},
            },
            "required": ["projectId"],
        },
    )


def get_get_branches_tool() -> MCPTool:
    """Get branches tool definition (deprecated - use mcp_get_branch_info instead)."""
    return MCPTool(
        name="mcp_get_branches",
        description="Get branches for a project or feature (DEPRECATED: Use mcp_get_branch_info instead)",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "featureId": {"type": "string", "description": "Optional feature UUID"},
            },
            "required": ["projectId"],
        },
    )


async def handle_get_branch_info(
    project_id: str,
    feature_id: Optional[str] = None,
    branch_name: Optional[str] = None,
    include_status: bool = True,
    include_commits: bool = False,
) -> dict:
    """Handle get branch info tool call - consolidated branch information."""
    db = SessionLocal()
    try:
        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, project_id)
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        owner, repo = GitHubService.parse_github_url(project.github_repo_url)
        if not owner or not repo:
            return {"error": "Invalid GitHub repository URL format"}

        # Get GitHub client
        github_service = get_github_service()
        if not github_service or not github_service.client:
            return {"error": "GitHub token not configured"}
        client = github_service.client

        # Build query
        query = db.query(GitHubBranch).filter(GitHubBranch.project_id == UUID(project_id))
        if feature_id:
            query = query.filter(GitHubBranch.feature_id == UUID(feature_id))
        if branch_name:
            query = query.filter(GitHubBranch.branch_name == branch_name)

        branches = query.order_by(GitHubBranch.created_at.desc()).all()

        # If specific branch requested, get detailed info
        if branch_name and len(branches) == 1:
            branch = branches[0]
            result = {
                "project_id": project_id,
                "branch": {
                    "id": str(branch.id),
                    "name": branch.branch_name,
                    "base_branch": branch.base_branch,
                    "status": branch.status,
                    "feature_id": str(branch.feature_id) if branch.feature_id else None,
                },
            }

            # Include status if requested
            if include_status:
                try:
                    repository = client.get_repo(f"{owner}/{repo}")
                    comparison = repository.compare(branch.base_branch, branch.branch_name)
                    result["branch"]["ahead_count"] = comparison.ahead_by
                    result["branch"]["behind_count"] = comparison.behind_by
                    result["branch"]["has_conflicts"] = comparison.mergeable is False
                    
                    # Update branch record
                    branch.ahead_count = comparison.ahead_by
                    branch.behind_count = comparison.behind_by
                    branch.has_conflicts = comparison.mergeable is False
                    db.commit()
                except GithubException as e:
                    result["branch"]["status_error"] = str(e)

            # Include commits if requested
            if include_commits:
                try:
                    repository = client.get_repo(f"{owner}/{repo}")
                    commits = repository.get_commits(sha=branch.branch_name)
                    result["branch"]["commits"] = [
                        {
                            "sha": commit.sha,
                            "message": commit.commit.message,
                            "author": commit.commit.author.name if commit.commit.author else None,
                            "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None,
                        }
                        for commit in commits[:50]  # Limit to 50 commits
                    ]
                    result["branch"]["commit_count"] = len(list(commits))
                except GithubException as e:
                    result["branch"]["commits_error"] = str(e)

            return result

        # Multiple branches or list view
        branches_data = []
        for branch in branches:
            branch_data = {
                "id": str(branch.id),
                "name": branch.branch_name,
                "base_branch": branch.base_branch,
                "status": branch.status,
                "feature_id": str(branch.feature_id) if branch.feature_id else None,
            }

            # Include status if requested
            if include_status:
                branch_data["ahead_count"] = branch.ahead_count
                branch_data["behind_count"] = branch.behind_count
                branch_data["has_conflicts"] = branch.has_conflicts

            branches_data.append(branch_data)

        result = {
            "project_id": project_id,
            "feature_id": feature_id,
            "branches": branches_data,
            "count": len(branches_data),
        }

        # Include commits for all branches if requested
        if include_commits and branches:
            try:
                repository = client.get_repo(f"{owner}/{repo}")
                all_commits = []
                for branch in branches:
                    try:
                        commits = repository.get_commits(sha=branch.branch_name)
                        for commit in commits[:20]:  # Limit to 20 commits per branch
                            all_commits.append({
                                "sha": commit.sha,
                                "message": commit.commit.message,
                                "author": commit.commit.author.name if commit.commit.author else None,
                                "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None,
                                "branch": branch.branch_name,
                            })
                    except GithubException:
                        continue
                result["commits"] = all_commits[:100]  # Limit total to 100
                result["commit_count"] = len(all_commits)
            except GithubException as e:
                result["commits_error"] = str(e)

        return result
    finally:
        db.close()


async def handle_get_branches(project_id: str, feature_id: Optional[str] = None) -> dict:
    """Handle get branches tool call."""
    db = SessionLocal()
    try:
        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, project_id)
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
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
    """Get create branch for feature tool definition.
    
    NOTE: In the Cursor + InTracker workflow, branches are typically created locally using git commands.
    This tool creates a branch on GitHub and links it to a feature. Use this if you need to create
    the branch on GitHub first, otherwise prefer creating the branch locally and using 
    mcp_link_branch_to_feature to link it.
    
    Recommended workflow:
    1. Create branch locally: git checkout -b feature/feature-name develop
    2. Push to GitHub: git push -u origin feature/feature-name
    3. Link to feature: mcp_link_branch_to_feature(featureId, "feature/feature-name")
    """
    return MCPTool(
        name="mcp_create_branch_for_feature",
        description="Create a GitHub branch for a feature. NOTE: In Cursor + InTracker workflow, branches are typically created locally using git commands. This tool creates the branch on GitHub and links it. For optimal workflow, create branch locally first, then use mcp_link_branch_to_feature to link it.",
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

        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, str(feature.project_id))
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, feature.project_id)
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        owner, repo = GitHubService.parse_github_url(project.github_repo_url)
        if not owner or not repo:
            return {"error": "Invalid GitHub repository URL format"}

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
    """Get link branch to feature tool definition.
    
    RECOMMENDED: Use this tool after creating a branch locally with git commands.
    This is the preferred workflow in Cursor + InTracker integration.
    
    Workflow:
    1. Create branch locally: git checkout -b feature/feature-name develop
    2. Push to GitHub: git push -u origin feature/feature-name
    3. Link to feature: mcp_link_branch_to_feature(featureId, "feature/feature-name")
    """
    return MCPTool(
        name="mcp_link_branch_to_feature",
        description="Link a GitHub branch to a feature. RECOMMENDED: Use this after creating a branch locally with git commands. This is the preferred workflow in Cursor + InTracker integration.",
        inputSchema={
            "type": "object",
            "properties": {
                "featureId": {"type": "string", "description": "Feature UUID"},
                "branchName": {"type": "string", "description": "Branch name (e.g., 'feature/feature-name')"},
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

        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, str(feature.project_id))
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
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

        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, str(feature.project_id))
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
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
        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, project_id)
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
        # Use ProjectService to get project
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project or not project.github_repo_url:
            return {"error": "Project does not have a connected GitHub repository"}

        # Parse repo owner and name
        owner, repo = GitHubService.parse_github_url(project.github_repo_url)
        if not owner or not repo:
            return {"error": "Invalid GitHub repository URL format"}

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
    """Get commits for feature tool definition.
    
    NOTE: In Cursor + InTracker workflow, commits are made locally using git commands.
    This tool retrieves commits from GitHub for a feature's branches. Useful for:
    - Tracking commit history
    - Statistics and reporting
    - Validating commit messages
    
    Commits are typically made locally, but this tool provides visibility into GitHub commit history.
    """
    return MCPTool(
        name="mcp_get_commits_for_feature",
        description="Get commits for a feature from GitHub. NOTE: In Cursor + InTracker workflow, commits are made locally using git commands. This tool retrieves commits from GitHub for tracking history, statistics, and validation.",
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

        # Validate project access using user's GitHub OAuth token
        has_access, error_dict = validate_project_access(db, str(feature.project_id))
        if not has_access:
            return error_dict or {"error": "Cannot access project"}
        
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
        owner, repo = GitHubService.parse_github_url(project.github_repo_url)
        if not owner or not repo:
            return {"error": "Invalid GitHub repository URL format"}

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
