"""Project service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.database.models import Project, UserProject


class ProjectService:
    """Service for project operations."""

    @staticmethod
    def create_project(
        db: Session,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        status: str = "active",
        tags: Optional[List[str]] = None,
        technology_tags: Optional[List[str]] = None,
        cursor_instructions: Optional[str] = None,
        github_repo_url: Optional[str] = None,
        github_repo_id: Optional[str] = None,
    ) -> Project:
        """Create a new project and assign owner role to user."""
        project = Project(
            name=name,
            description=description,
            status=status,
            tags=tags or [],
            technology_tags=technology_tags or [],
            cursor_instructions=cursor_instructions,
            github_repo_url=github_repo_url,
            github_repo_id=github_repo_id,
        )
        db.add(project)
        db.flush()

        # Assign owner role
        user_project = UserProject(
            user_id=user_id,
            project_id=project.id,
            role="owner",
        )
        db.add(user_project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project_by_id(db: Session, project_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_user_projects(
        db: Session,
        user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Project], int]:
        """Get projects for a user with optional filtering."""
        query = (
            db.query(Project)
            .join(UserProject)
            .filter(UserProject.user_id == user_id)
        )

        if status:
            query = query.filter(Project.status == status)

        total = query.count()
        projects = query.offset(skip).limit(limit).all()

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
    ) -> Optional[Project]:
        """Update project."""
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

        db.commit()
        db.refresh(project)
        return project

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
        """Check if user has access to project."""
        user_project = (
            db.query(UserProject)
            .filter(
                UserProject.user_id == user_id,
                UserProject.project_id == project_id,
            )
            .first()
        )

        if not user_project:
            return False

        if required_role:
            role_hierarchy = {"viewer": 1, "editor": 2, "owner": 3}
            user_role_level = role_hierarchy.get(user_project.role, 0)
            required_role_level = role_hierarchy.get(required_role, 0)
            return user_role_level >= required_role_level

        return True


# Global instance
project_service = ProjectService()
