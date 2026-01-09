"""Session service."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Session, Project, Todo, Feature
from src.database.base import set_current_user_id, reset_current_user_id


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
        broadcast_start: bool = True,
        current_user_id: Optional[UUID] = None,
    ) -> Session:
        """Create a new session.
        
        If broadcast_start is True (default), broadcasts a SignalR event
        to notify clients that a user has started working on the project.
        """
        # Set current user ID for audit trail (use user_id if current_user_id not provided)
        token = None
        audit_user_id = current_user_id or user_id
        if audit_user_id:
            token = set_current_user_id(audit_user_id)
        
        try:
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
            
            # Broadcast session start event via SignalR (async, fire and forget)
            if broadcast_start and user_id:
            try:
                import asyncio
                import threading
                from src.services.signalr_hub import broadcast_session_start
                
                def run_broadcast():
                    """Run async broadcast in a new event loop."""
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(broadcast_session_start(str(project_id), str(user_id)))
                        loop.close()
                    except Exception as e:
                        print(f"Error in broadcast thread: {e}")
                
                # Run broadcast in a separate thread to avoid blocking
                thread = threading.Thread(target=run_broadcast, daemon=True)
                thread.start()
            except Exception as e:
                # Don't fail session creation if broadcast fails
                print(f"Failed to broadcast session start: {e}")
        
            return session
        finally:
            if token:
                reset_current_user_id(token)

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
        current_user_id: Optional[UUID] = None,
    ) -> Optional[Session]:
        """Update session."""
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
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
        finally:
            if token:
                reset_current_user_id(token)

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
        
        # Broadcast session end event via SignalR (async, fire and forget)
        if session.user_id:
            try:
                import asyncio
                import threading
                from src.services.signalr_hub import broadcast_session_end
                
                def run_broadcast():
                    """Run async broadcast in a new event loop."""
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(broadcast_session_end(str(session.project_id), str(session.user_id)))
                        loop.close()
                    except Exception as e:
                        print(f"Error in broadcast thread: {e}")
                
                # Run broadcast in a separate thread to avoid blocking
                thread = threading.Thread(target=run_broadcast, daemon=True)
                thread.start()
            except Exception as e:
                # Don't fail session end if broadcast fails
                print(f"Failed to broadcast session end: {e}")
        
        return session

    @staticmethod
    def generate_session_summary(db: Session, session: Session) -> str:
        """Generate automatic session summary with workflow reminders."""
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
            summary_base = "Session completed with no changes recorded."
        else:
            summary_base = " | ".join(parts)

        # Add workflow reminder for next session
        workflow_reminder = """

⚠️ WORKFLOW REMINDER FOR NEXT SESSION:

MANDATORY: Follow this workflow at the start of the next session:

1. Call `mcp_enforce_workflow()` - This automatically:
   - Identifies the project
   - Loads resume context
   - Loads cursor rules
   - Returns workflow checklist

2. Check the workflow checklist - All items must be ✅

3. Work on todos from `resume_context.now.todos`

4. ALWAYS update todo status:
   - Start work: `mcp_update_todo_status(todoId, "in_progress")`
   - After implementation: `mcp_update_todo_status(todoId, "tested")` (only if tested!)
   - After merge: `mcp_update_todo_status(todoId, "done")` (only if tested AND merged!)

5. ALWAYS follow git workflow:
   - `git status` → `git diff` → `git add -A` → `git commit -m "..."` → `git push`
   - Commit format: `{type}({scope}): {description} [feature:{featureId}]`

NEVER skip these steps!"""

        return summary_base + workflow_reminder

    @staticmethod
    def get_active_users_for_project(db: Session, project_id: UUID) -> List[dict]:
        """Get active users for a project (users with open sessions).
        
        Active user = user with open session (ended_at IS NULL) on the project.
        Returns list of user info dicts with id, name, email, avatar_url.
        """
        from src.database.models import User
        
        # Get distinct user_ids from active sessions (ended_at IS NULL)
        active_sessions = (
            db.query(Session)
            .filter(
                Session.project_id == project_id,
                Session.ended_at.is_(None),
                Session.user_id.isnot(None),
            )
            .all()
        )
        
        # Get unique user IDs
        user_ids = list(set(session.user_id for session in active_sessions if session.user_id))
        
        if not user_ids:
            return []
        
        # Get user details
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        
        # Return user info
        return [
            {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
            }
            for user in users
        ]


# Global instance
session_service = SessionService()
