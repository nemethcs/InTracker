"""Unit tests for TodoService."""
import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.services.todo_service import TodoService
from src.database.models import Todo, ProjectElement, Feature, Project


class TestTodoService:
    """Test cases for TodoService."""
    
    def test_create_todo(self, db: Session, test_element: ProjectElement, test_feature: Feature, test_user: User):
        """Test creating a todo."""
        todo = TodoService.create_todo(
            db=db,
            element_id=test_element.id,
            title="New Todo",
            description="Test todo",
            status="new",
            feature_id=test_feature.id,
            priority="high",
            current_user_id=test_user.id,
        )
        
        assert todo is not None
        assert todo.title == "New Todo"
        assert todo.element_id == test_element.id
        assert todo.feature_id == test_feature.id
        assert todo.status == "new"
        assert todo.priority == "high"
        assert todo.version == 1
    
    def test_create_todo_with_default_element(self, db: Session, test_project: Project, test_feature: Feature, test_user: User):
        """Test creating todo with default element."""
        todo = TodoService.create_todo(
            db=db,
            element_id=None,
            title="Todo with default element",
            project_id=test_project.id,
            feature_id=test_feature.id,
            current_user_id=test_user.id,
        )
        
        assert todo is not None
        assert todo.element_id is not None  # Should use default element
    
    def test_get_todo_by_id(self, db: Session, test_todo: Todo):
        """Test getting todo by ID."""
        todo = TodoService.get_todo_by_id(db, test_todo.id)
        
        assert todo is not None
        assert todo.id == test_todo.id
        assert todo.title == test_todo.title
    
    def test_get_todo_by_id_not_found(self, db: Session):
        """Test getting non-existent todo."""
        fake_id = uuid4()
        todo = TodoService.get_todo_by_id(db, fake_id)
        
        assert todo is None
    
    def test_get_todos_by_element(self, db: Session, test_element: ProjectElement, test_todo: Todo):
        """Test getting todos by element."""
        todos, total = TodoService.get_todos_by_element(
            db=db,
            element_id=test_element.id,
        )
        
        assert total >= 1
        assert any(t.id == test_todo.id for t in todos)
    
    def test_get_todos_by_project(self, db: Session, test_project: Project, test_todo: Todo):
        """Test getting todos by project."""
        todos, total = TodoService.get_todos_by_project(
            db=db,
            project_id=test_project.id,
        )
        
        assert total >= 1
        assert any(t.id == test_todo.id for t in todos)
    
    def test_update_todo_status(self, db: Session, test_todo: Todo, test_user: User):
        """Test updating todo status."""
        updated = TodoService.update_todo_status(
            db=db,
            todo_id=test_todo.id,
            status="in_progress",
            expected_version=test_todo.version,
            current_user_id=test_user.id,
        )
        
        assert updated is not None
        assert updated.status == "in_progress"
        assert updated.version == test_todo.version + 1  # Version should increment
    
    def test_update_todo_status_optimistic_locking(self, db: Session, test_todo: Todo, test_user: User):
        """Test optimistic locking prevents concurrent updates."""
        # First update
        TodoService.update_todo_status(
            db=db,
            todo_id=test_todo.id,
            status="in_progress",
            expected_version=test_todo.version,
            current_user_id=test_user.id,
        )
        
        # Try to update with old version (should fail)
        with pytest.raises(ValueError, match="Version mismatch"):
            TodoService.update_todo_status(
                db=db,
                todo_id=test_todo.id,
                status="done",
                expected_version=test_todo.version,  # Old version
                current_user_id=test_user.id,
            )
