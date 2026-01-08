"""Session service."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Session, Project, Todo, Feature


class SessionService:
    """Service for session operations."""

    @staticmethod
    def create_session(
        db: Session,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
        goal: Optional[str] = None,
        feature_ids: Optional[List[UUID]] = None,
    ) -> Session:
        """Create a new session."""
        session = Session(
            project_id=project_id,
            user_id=user_id,
            title=title,
            goal=goal,
            feature_ids=feature_ids or [],
            todos_completed=[],
            features_completed=[],
            elements_updated=[],
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session_by_id(db: Session, session_id: UUID) -> Optional[Session]:
        """Get session by ID."""
        return db.query(Session).filter(Session.id == session_id).first()

    @staticmethod
    def get_sessions_by_project(
        db: Session,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Session], int]:
        """Get sessions for a project."""
        query = db.query(Session).filter(Session.project_id == project_id)

        if user_id:
            query = query.filter(Session.user_id == user_id)

        total = query.count()
        sessions = query.order_by(Session.started_at.desc()).offset(skip).limit(limit).all()

        return sessions, total

    @staticmethod
    def get_sessions_by_user(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Session], int]:
        """Get sessions for a user.
        
        Returns sessions for projects where the user is a team member.
        Admins see all sessions.
        """
        from src.database.models import User, TeamMember
        
        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "admin":
            # Admins see all sessions
            query = db.query(Session).filter(Session.user_id == user_id)
        else:
            # Get sessions for projects where user is a team member
            query = (
                db.query(Session)
                .join(Project, Session.project_id == Project.id)
                .join(TeamMember, Project.team_id == TeamMember.team_id)
                .filter(TeamMember.user_id == user_id)
                .filter(Session.user_id == user_id)
            )

        total = query.count()
        sessions = query.order_by(Session.started_at.desc()).offset(skip).limit(limit).all()

        return sessions, total

    @staticmethod
    def update_session(
        db: Session,
        session_id: UUID,
        title: Optional[str] = None,
        goal: Optional[str] = None,
        notes: Optional[str] = None,
        todos_completed: Optional[List[UUID]] = None,
        features_completed: Optional[List[UUID]] = None,
        elements_updated: Optional[List[UUID]] = None,
    ) -> Optional[Session]:
        """Update session."""
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return None

        if title is not None:
            session.title = title
        if goal is not None:
            session.goal = goal
        if notes is not None:
            session.notes = notes
        if todos_completed is not None:
            session.todos_completed = todos_completed
        if features_completed is not None:
            session.features_completed = features_completed
        if elements_updated is not None:
            session.elements_updated = elements_updated

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def end_session(
        db: Session,
        session_id: UUID,
        summary: Optional[str] = None,
        notes: Optional[str] = None,
        todos_completed: Optional[List[UUID]] = None,
        features_completed: Optional[List[UUID]] = None,
        elements_updated: Optional[List[UUID]] = None,
    ) -> Optional[Session]:
        """End session and generate summary if not provided."""
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return None

        if session.ended_at:
            raise ValueError("Session is already ended")

        # Update session data
        if notes is not None:
            session.notes = notes
        if todos_completed is not None:
            session.todos_completed = todos_completed
        if features_completed is not None:
            session.features_completed = features_completed
        if elements_updated is not None:
            session.elements_updated = elements_updated

        # Generate summary if not provided
        if summary:
            session.summary = summary
        else:
            session.summary = SessionService.generate_session_summary(
                db=db,
                session=session,
            )

        session.ended_at = datetime.utcnow()

        # Update project last_session_at
        project = db.query(Project).filter(Project.id == session.project_id).first()
        if project:
            project.last_session_at = session.ended_at

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def generate_session_summary(db: Session, session: Session) -> str:
        """Generate automatic session summary."""
        parts = []

        if session.goal:
            parts.append(f"Goal: {session.goal}")

        if session.todos_completed:
            todo_count = len(session.todos_completed)
            parts.append(f"Completed {todo_count} todo(s)")

        if session.features_completed:
            feature_count = len(session.features_completed)
            parts.append(f"Completed {feature_count} feature(s)")

        if session.elements_updated:
            element_count = len(session.elements_updated)
            parts.append(f"Updated {element_count} element(s)")

        if not parts:
            return "Session completed with no changes recorded."

        return " | ".join(parts)


# Global instance
session_service = SessionService()
