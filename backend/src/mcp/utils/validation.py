"""Validation utilities for MCP tools."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Feature, Todo


class ValidationError(Exception):
    """Raised when a validation rule is violated."""
    pass


def validate_all_todos_done(db: Session, feature_id: UUID) -> tuple[bool, int, int]:
    """Check if all todos for a feature are done.
    
    Args:
        db: Database session
        feature_id: Feature UUID
        
    Returns:
        Tuple of (all_done: bool, total_todos: int, done_todos: int)
    """
    total = db.query(func.count(Todo.id)).filter(Todo.feature_id == feature_id).scalar()
    done = (
        db.query(func.count(Todo.id))
        .filter(Todo.feature_id == feature_id, Todo.status == "done")
        .scalar()
    )
    
    return (total == done and total > 0, total, done)


def validate_feature_status_transition(
    db: Session,
    feature_id: UUID,
    new_status: str,
    require_all_todos_done: bool = False,
) -> None:
    """Validate if a feature status transition is allowed.
    
    Args:
        db: Database session
        feature_id: Feature UUID
        new_status: The new status to transition to
        require_all_todos_done: If True, require all todos to be done for certain statuses
        
    Raises:
        ValidationError: If the transition is not allowed
    """
    feature = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feature:
        raise ValidationError(f"Feature {feature_id} not found")
    
    # Statuses that require all todos to be done
    statuses_requiring_all_todos_done = ["tested", "merged"]
    
    if new_status in statuses_requiring_all_todos_done:
        all_done, total, done = validate_all_todos_done(db, feature_id)
        
        if not all_done:
            raise ValidationError(
                f"Cannot set feature to '{new_status}' status: "
                f"not all todos are done ({done}/{total} todos completed). "
                f"All todos must have status 'done' before a feature can be marked as '{new_status}'."
            )
    
    # Additional validation: cannot skip statuses in the workflow
    # Workflow: new → in_progress → done → tested → merged
    status_order = {
        "new": 0,
        "in_progress": 1,
        "done": 2,
        "tested": 3,
        "merged": 4,
    }
    
    current_order = status_order.get(feature.status, -1)
    new_order = status_order.get(new_status, -1)
    
    # Allow backward transitions (e.g., from done back to in_progress)
    # But prevent skipping forward (e.g., from new directly to tested)
    if new_order > current_order + 1:
        # Check if we're skipping required intermediate status
        skipped_statuses = [
            status
            for status, order in status_order.items()
            if current_order < order < new_order
        ]
        
        # Allow skipping if going to 'done' from 'in_progress' (normal flow)
        # But prevent skipping to 'tested' or 'merged' without being 'done' first
        if new_status in ["tested", "merged"] and feature.status != "done":
            raise ValidationError(
                f"Cannot set feature to '{new_status}' status: "
                f"feature must be 'done' first (current status: '{feature.status}'). "
                f"Workflow: new → in_progress → done → tested → merged"
            )


def validate_todo_status_transition(
    db: Session,
    todo_id: UUID,
    new_status: str,
) -> None:
    """Validate if a todo status transition is allowed.
    
    Args:
        db: Database session
        todo_id: Todo UUID
        new_status: The new status to transition to
        
    Raises:
        ValidationError: If the transition is not allowed
    """
    from src.database.models import Todo as TodoModel
    
    todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if not todo:
        raise ValidationError(f"Todo {todo_id} not found")
    
    # Todo workflow: new → in_progress → done
    status_order = {
        "new": 0,
        "in_progress": 1,
        "done": 2,
    }
    
    current_order = status_order.get(todo.status, -1)
    new_order = status_order.get(new_status, -1)
    
    # Allow backward transitions (e.g., from done back to in_progress)
    # But prevent skipping forward (e.g., from new directly to done)
    if new_order > current_order + 1:
        raise ValidationError(
            f"Cannot set todo to '{new_status}' status: "
            f"cannot skip status in workflow. "
            f"Current: '{todo.status}', trying to set: '{new_status}'. "
            f"Workflow: new → in_progress → done"
        )
