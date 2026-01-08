"""Idea service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from src.database.models import Idea, Project, TeamMember, User


class IdeaService:
    """Service for idea operations."""

    @staticmethod
    def create_idea(
        db: Session,
        team_id: UUID,
        title: str,
        description: Optional[str] = None,
        status: str = "draft",
        tags: Optional[List[str]] = None,
    ) -> Idea:
        """Create a new idea for a team."""
        idea = Idea(
            team_id=team_id,
            title=title,
            description=description,
            status=status,
            tags=tags or [],
        )
        db.add(idea)
        db.commit()
        db.refresh(idea)
        return idea

    @staticmethod
    def get_idea_by_id(db: Session, idea_id: UUID) -> Optional[Idea]:
        """Get idea by ID."""
        return db.query(Idea).filter(Idea.id == idea_id).first()

    @staticmethod
    def get_ideas(
        db: Session,
        user_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Idea], int]:
        """Get ideas with optional filtering.
        
        If user_id is provided, returns ideas from teams where user is a member.
        If user is admin, returns all ideas.
        If team_id is provided, filters by team.
        """
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            
            if user and user.role == "admin":
                # Admins see all ideas
                query = db.query(Idea)
            else:
                # Get ideas from teams where user is a member
                query = (
                    db.query(Idea)
                    .join(TeamMember, Idea.team_id == TeamMember.team_id)
                    .filter(TeamMember.user_id == user_id)
                )
        else:
            query = db.query(Idea)
        
        # Filter by team_id if provided
        if team_id:
            query = query.filter(Idea.team_id == team_id)

        if status:
            query = query.filter(Idea.status == status)

        total = query.count()
        ideas = query.order_by(Idea.created_at.desc()).offset(skip).limit(limit).all()

        return ideas, total

    @staticmethod
    def update_idea(
        db: Session,
        idea_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Idea]:
        """Update idea."""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if not idea:
            return None

        if title is not None:
            idea.title = title
        if description is not None:
            idea.description = description
        if status is not None:
            idea.status = status
        if tags is not None:
            idea.tags = tags

        db.commit()
        db.refresh(idea)
        return idea

    @staticmethod
    def delete_idea(db: Session, idea_id: UUID) -> bool:
        """Delete idea."""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if not idea:
            return False

        db.delete(idea)
        db.commit()
        return True

    @staticmethod
    def convert_idea_to_project(
        db: Session,
        idea_id: UUID,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        project_status: str = "active",
        project_tags: Optional[List[str]] = None,
        technology_tags: Optional[List[str]] = None,
    ) -> Optional[Project]:
        """Convert idea to project. The project will belong to the same team as the idea."""
        from src.services.project_service import ProjectService

        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if not idea:
            return None

        if idea.converted_to_project_id:
            # Already converted
            return db.query(Project).filter(Project.id == idea.converted_to_project_id).first()

        # Create project from idea (same team as idea)
        project = ProjectService.create_project(
            db=db,
            team_id=idea.team_id,
            name=project_name or idea.title,
            description=project_description or idea.description,
            status=project_status,
            tags=project_tags or idea.tags,
            technology_tags=technology_tags or [],
        )

        # Link idea to project
        idea.converted_to_project_id = project.id
        db.commit()
        db.refresh(idea)

        return project
