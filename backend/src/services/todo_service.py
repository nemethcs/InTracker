"""Todo service."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from src.database.models import Todo, ProjectElement, Feature


class TodoService:
    """Service for todo operations."""

    @staticmethod
    def create_todo(
        db: Session,
        element_id: UUID,
        title: str,
        description: Optional[str] = None,
        status: str = "todo",
        feature_id: Optional[UUID] = None,
        position: Optional[int] = None,
        estimated_effort: Optional[int] = None,
        created_by: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
    ) -> Todo:
        """Create a new todo."""
        # Verify element exists
        element = db.query(ProjectElement).filter(ProjectElement.id == element_id).first()
        if not element:
            raise ValueError("Element not found")

        # Verify feature if provided
        if feature_id:
            feature = db.query(Feature).filter(Feature.id == feature_id).first()
            if not feature:
                raise ValueError("Feature not found")
            if feature.project_id != element.project_id:
                raise ValueError("Feature and element must belong to the same project")

        todo = Todo(
            element_id=element_id,
            feature_id=feature_id,
            title=title,
            description=description,
            status=status,
            position=position,
            estimated_effort=estimated_effort,
            created_by=created_by,
            assigned_to=assigned_to,
            version=1,
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)

        # Update feature progress if linked
        if feature_id:
            from src.services.feature_service import feature_service
            feature_service.calculate_feature_progress(db=db, feature_id=feature_id)

        return todo

    @staticmethod
    def get_todo_by_id(db: Session, todo_id: UUID) -> Optional[Todo]:
        """Get todo by ID."""
        return db.query(Todo).filter(Todo.id == todo_id).first()

    @staticmethod
    def get_todos_by_element(
        db: Session,
        element_id: UUID,
        status: Optional[str] = None,
    ) -> List[Todo]:
        """Get todos for an element."""
        query = db.query(Todo).filter(Todo.element_id == element_id)

        if status:
            query = query.filter(Todo.status == status)

        return query.order_by(Todo.position, Todo.created_at).all()

    @staticmethod
    def get_todos_by_feature(
        db: Session,
        feature_id: UUID,
        status: Optional[str] = None,
    ) -> List[Todo]:
        """Get todos for a feature."""
        query = db.query(Todo).filter(Todo.feature_id == feature_id)

        if status:
            query = query.filter(Todo.status == status)

        return query.order_by(Todo.position, Todo.created_at).all()

    @staticmethod
    def get_todos_by_user(
        db: Session,
        user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Todo], int]:
        """Get todos assigned to a user."""
        query = db.query(Todo).filter(Todo.assigned_to == user_id)

        if status:
            query = query.filter(Todo.status == status)

        total = query.count()
        todos = query.offset(skip).limit(limit).all()

        return todos, total

    @staticmethod
    def update_todo(
        db: Session,
        todo_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        position: Optional[int] = None,
        estimated_effort: Optional[int] = None,
        blocker_reason: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        expected_version: Optional[int] = None,
    ) -> Optional[Todo]:
        """Update todo with optimistic locking."""
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        if not todo:
            return None

        # Optimistic locking check
        if expected_version is not None and todo.version != expected_version:
            raise ValueError("Todo was modified by another user. Please refresh and try again.")

        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if status is not None:
            old_status = todo.status
            todo.status = status
            # Update completed_at if status changed to done
            if status == "done" and old_status != "done":
                todo.completed_at = datetime.utcnow()
            elif status != "done" and old_status == "done":
                todo.completed_at = None
        if position is not None:
            todo.position = position
        if estimated_effort is not None:
            todo.estimated_effort = estimated_effort
        if blocker_reason is not None:
            todo.blocker_reason = blocker_reason
        if assigned_to is not None:
            todo.assigned_to = assigned_to

        # Increment version for optimistic locking
        todo.version += 1

        db.commit()
        db.refresh(todo)

        # Update feature progress if linked
        if todo.feature_id:
            from src.services.feature_service import feature_service
            feature_service.calculate_feature_progress(db=db, feature_id=todo.feature_id)

        return todo

    @staticmethod
    def delete_todo(db: Session, todo_id: UUID) -> bool:
        """Delete todo."""
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        if not todo:
            return False

        feature_id = todo.feature_id
        db.delete(todo)
        db.commit()

        # Update feature progress if linked
        if feature_id:
            from src.services.feature_service import feature_service
            feature_service.calculate_feature_progress(db=db, feature_id=feature_id)

        return True

    @staticmethod
    def update_todo_status(
        db: Session,
        todo_id: UUID,
        status: str,
        expected_version: Optional[int] = None,
    ) -> Optional[Todo]:
        """Update todo status with optimistic locking."""
        return TodoService.update_todo(
            db=db,
            todo_id=todo_id,
            status=status,
            expected_version=expected_version,
        )


# Global instance
todo_service = TodoService()
