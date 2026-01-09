"""Project service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.database.models import Project, User, TeamMember
from src.database.base import set_current_user_id, reset_current_user_id


class ProjectService:
    """Service for project operations."""

    @staticmethod
    def create_project(
        db: Session,
        team_id: UUID,
        name: str,
        description: Optional[str] = None,
        status: str = "active",
        tags: Optional[List[str]] = None,
        technology_tags: Optional[List[str]] = None,
        cursor_instructions: Optional[str] = None,
        github_repo_url: Optional[str] = None,
        github_repo_id: Optional[str] = None,
        current_user_id: Optional[UUID] = None,
    ) -> Project:
        """Create a new project for a team."""
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
            project = Project(
                name=name,
                description=description,
                status=status,
                tags=tags or [],
                technology_tags=technology_tags or [],
                team_id=team_id,
                cursor_instructions=cursor_instructions,
                github_repo_url=github_repo_url,
                github_repo_id=github_repo_id,
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            return project
        finally:
            if token:
                reset_current_user_id(token)

    @staticmethod
    def get_project_by_id(db: Session, project_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_user_projects(
        db: Session,
        user_id: UUID,
        status: Optional[str] = None,
        team_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Project], int]:
        """Get projects accessible to a user (projects from teams where user is a member).
        
        If user is admin, returns all projects.
        Otherwise, returns projects from teams where user is a member.
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if user and user.role == "admin":
            # Admins see all projects
            query = db.query(Project)
        else:
            # Get projects from teams where user is a member
            query = (
                db.query(Project)
                .join(TeamMember, Project.team_id == TeamMember.team_id)
                .filter(TeamMember.user_id == user_id)
            )
        
        # Filter by team_id if provided
        if team_id:
            query = query.filter(Project.team_id == team_id)
        
        if status:
            query = query.filter(Project.status == status)

        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

        return projects, total

    @staticmethod
    def update_project(
        db: Session,
        project_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        technology_tags: Optional[List[str]] = None,
        cursor_instructions: Optional[str] = None,
        github_repo_url: Optional[str] = None,
        github_repo_id: Optional[str] = None,
        team_id: Optional[UUID] = None,
        current_user_id: Optional[UUID] = None,
    ) -> Optional[Project]:
        """Update project."""
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None

            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            if status is not None:
                project.status = status
            if tags is not None:
                project.tags = tags
            if technology_tags is not None:
                project.technology_tags = technology_tags
            if cursor_instructions is not None:
                project.cursor_instructions = cursor_instructions
            if github_repo_url is not None:
                project.github_repo_url = github_repo_url
            if github_repo_id is not None:
                project.github_repo_id = github_repo_id
            if team_id is not None:
                project.team_id = team_id

            db.commit()
            db.refresh(project)
            return project
        finally:
            if token:
                reset_current_user_id(token)

    @staticmethod
    def delete_project(db: Session, project_id: UUID) -> bool:
        """Delete project (cascade deletes related data)."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def check_user_access(
        db: Session,
        user_id: UUID,
        project_id: UUID,
        required_role: Optional[str] = None,
    ) -> bool:
        """Check if user has access to project.
        
        Admins have access to all projects.
        Users have access if they are members of the team that owns the project.
        Team leaders have full access to their team's projects.
        Regular members have access to their team's projects.
        """
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # Check if user is admin - admins have access to all projects
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "admin":
            return True
        
        # Check if user is a member of the team that owns the project
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == user_id,
            )
            .first()
        )
        
        if not team_member:
            return False
        
        # If required_role is specified, check role hierarchy
        # For now, team_leader has full access, members have read access
        if required_role:
            if team_member.role == "team_leader":
                return True  # Team leaders have full access
            elif required_role in ["viewer", "editor", "owner"]:
                # Members can view, but not edit
                return required_role == "viewer"
        
        return True


# Global instance
project_service = ProjectService()
