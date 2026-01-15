"""Branch service for GitHub branch management."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from src.database.models import GitHubBranch, Project, Feature
from src.services.github_service import github_service


class BranchService:
    """Service for branch operations."""

    @staticmethod
    def create_branch_for_feature(
        db: Session,
        project_id: UUID,
        feature_id: UUID,
        branch_name: str,
        from_branch: str = "main",
    ) -> Optional[GitHubBranch]:
        """Create a GitHub branch for a feature."""
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.github_repo_url:
            raise ValueError("Project does not have a connected GitHub repository")

        # Get feature
        feature = db.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            raise ValueError("Feature not found")

        # Parse repo owner and name from URL
        # Format: https://github.com/owner/repo
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            raise ValueError("Invalid GitHub repository URL format")

        owner, repo = repo_parts

        # Create branch via GitHub API
        branch_info = github_service.create_branch(
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            from_branch=from_branch,
        )

        if not branch_info:
            raise ValueError("Failed to create branch on GitHub")

        # Store branch in database
        github_branch = GitHubBranch(
            project_id=project_id,
            feature_id=feature_id,
            branch_name=branch_name,
            last_commit_sha=branch_info["sha"],
            status="active",
        )
        db.add(github_branch)
        db.commit()
        db.refresh(github_branch)

        return github_branch

    @staticmethod
    def get_branches_by_project(
        db: Session,
        project_id: UUID,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> tuple[List[GitHubBranch], int]:
        """Get branches for a project with pagination.
        
        Returns:
            Tuple of (branches list, total count)
        """
        query = (
            db.query(GitHubBranch)
            .filter(GitHubBranch.project_id == project_id)
        )
        
        total = query.count()
        query = query.order_by(GitHubBranch.created_at.desc())
        
        if skip > 0:
            query = query.offset(skip)
        if limit is not None and limit > 0:
            query = query.limit(limit)
        
        branches = query.all()
        return branches, total

    @staticmethod
    def get_branches_by_feature(
        db: Session,
        feature_id: UUID,
    ) -> List[GitHubBranch]:
        """Get all branches for a feature."""
        return (
            db.query(GitHubBranch)
            .filter(GitHubBranch.feature_id == feature_id)
            .order_by(GitHubBranch.created_at.desc())
            .all()
        )

    @staticmethod
    def get_branch_by_id(
        db: Session,
        branch_id: UUID,
    ) -> Optional[GitHubBranch]:
        """Get branch by ID."""
        return db.query(GitHubBranch).filter(GitHubBranch.id == branch_id).first()

    @staticmethod
    def sync_branches_from_github(
        db: Session,
        project_id: UUID,
    ) -> int:
        """Sync branches from GitHub repository."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.github_repo_url:
            raise ValueError("Project does not have a connected GitHub repository")

        # Parse repo owner and name
        repo_parts = project.github_repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            raise ValueError("Invalid GitHub repository URL format")

        owner, repo = repo_parts

        # Get branches from GitHub
        branches = github_service.list_branches(owner=owner, repo=repo)

        # Update or create branches in database
        synced_count = 0
        for branch_info in branches:
            existing = (
                db.query(GitHubBranch)
                .filter(
                    GitHubBranch.project_id == project_id,
                    GitHubBranch.branch_name == branch_info["name"],
                )
                .first()
            )

            if existing:
                existing.last_commit_sha = branch_info["sha"]
            else:
                github_branch = GitHubBranch(
                    project_id=project_id,
                    branch_name=branch_info["name"],
                    last_commit_sha=branch_info["sha"],
                    status="active",
                )
                db.add(github_branch)
            synced_count += 1

        db.commit()
        return synced_count


# Global instance
branch_service = BranchService()
