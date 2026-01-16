"""Unit tests for FeatureService."""
import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.services.feature_service import FeatureService
from src.database.models import Feature, Project, Todo


class TestFeatureService:
    """Test cases for FeatureService."""
    
    def test_create_feature(self, db: Session, test_project: Project, test_user: User):
        """Test creating a feature."""
        feature = FeatureService.create_feature(
            db=db,
            project_id=test_project.id,
            name="New Feature",
            description="Test feature",
            status="new",
            current_user_id=test_user.id,
        )
        
        assert feature is not None
        assert feature.name == "New Feature"
        assert feature.project_id == test_project.id
        assert feature.status == "new"
        assert feature.total_todos == 0
        assert feature.completed_todos == 0
        assert feature.progress_percentage == 0
    
    def test_get_feature_by_id(self, db: Session, test_feature: Feature):
        """Test getting feature by ID."""
        feature = FeatureService.get_feature_by_id(db, test_feature.id)
        
        assert feature is not None
        assert feature.id == test_feature.id
        assert feature.name == test_feature.name
    
    def test_get_feature_by_id_not_found(self, db: Session):
        """Test getting non-existent feature."""
        fake_id = uuid4()
        feature = FeatureService.get_feature_by_id(db, fake_id)
        
        assert feature is None
    
    def test_get_features_by_project(self, db: Session, test_project: Project, test_feature: Feature):
        """Test getting features by project."""
        features, total = FeatureService.get_features_by_project(
            db=db,
            project_id=test_project.id,
        )
        
        assert total >= 1
        assert any(f.id == test_feature.id for f in features)
    
    def test_update_feature(self, db: Session, test_feature: Feature, test_user: User):
        """Test updating a feature."""
        updated = FeatureService.update_feature(
            db=db,
            feature_id=test_feature.id,
            name="Updated Feature",
            status="in_progress",
            current_user_id=test_user.id,
        )
        
        assert updated is not None
        assert updated.name == "Updated Feature"
        assert updated.status == "in_progress"
    
    def test_calculate_feature_progress(self, db: Session, test_feature: Feature, test_element: ProjectElement):
        """Test calculating feature progress."""
        # Create todos for the feature
        todo1 = Todo(
            element_id=test_element.id,
            feature_id=test_feature.id,
            title="Todo 1",
            status="new",
            priority="medium",
            version=1,
        )
        todo2 = Todo(
            element_id=test_element.id,
            feature_id=test_feature.id,
            title="Todo 2",
            status="done",
            priority="medium",
            version=1,
        )
        db.add(todo1)
        db.add(todo2)
        db.commit()
        
        progress = FeatureService.calculate_feature_progress(db, test_feature.id)
        
        assert progress["total"] == 2
        assert progress["completed"] == 1
        assert progress["percentage"] == 50
        
        # Verify feature was updated
        db.refresh(test_feature)
        assert test_feature.total_todos == 2
        assert test_feature.completed_todos == 1
        assert test_feature.progress_percentage == 50
    
    def test_delete_feature(self, db: Session, test_feature: Feature):
        """Test deleting a feature."""
        feature_id = test_feature.id
        result = FeatureService.delete_feature(db, feature_id)
        
        assert result is True
        
        # Verify feature is deleted
        deleted = FeatureService.get_feature_by_id(db, feature_id)
        assert deleted is None
