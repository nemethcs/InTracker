"""Feature service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Feature, ProjectElement, FeatureElement, Todo


class FeatureService:
    """Service for feature operations."""

    @staticmethod
    def create_feature(
        db: Session,
        project_id: UUID,
        name: str,
        description: Optional[str] = None,
        status: str = "new",
        created_by: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        element_ids: Optional[List[UUID]] = None,
    ) -> Feature:
        """Create a new feature and optionally link elements."""
        feature = Feature(
            project_id=project_id,
            name=name,
            description=description,
            status=status,
            created_by=created_by,
            assigned_to=assigned_to,
            total_todos=0,
            completed_todos=0,
            progress_percentage=0,
        )
        db.add(feature)
        db.flush()

        # Link elements if provided
        if element_ids:
            for element_id in element_ids:
                # Verify element exists and belongs to project
                element = (
                    db.query(ProjectElement)
                    .filter(
                        ProjectElement.id == element_id,
                        ProjectElement.project_id == project_id,
                    )
                    .first()
                )
                if element:
                    feature_element = FeatureElement(
                        feature_id=feature.id,
                        element_id=element_id,
                    )
                    db.add(feature_element)

        db.commit()
        db.refresh(feature)
        return feature

    @staticmethod
    def get_feature_by_id(db: Session, feature_id: UUID) -> Optional[Feature]:
        """Get feature by ID."""
        return db.query(Feature).filter(Feature.id == feature_id).first()

    @staticmethod
    def get_features_by_project(
        db: Session,
        project_id: UUID,
        status: Optional[str] = None,
        sort: Optional[str] = "updated_at_desc",
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> tuple[List[Feature], int]:
        """Get features for a project with optional filtering, sorting, and pagination.
        
        Args:
            sort: Sort order. Options: "updated_at_desc" (default), "updated_at_asc", 
                  "created_at_desc", "created_at_asc", "name_asc", "name_desc"
            skip: Number of features to skip (for pagination)
            limit: Maximum number of features to return (None for no limit)
        """
        query = db.query(Feature).filter(Feature.project_id == project_id)

        if status:
            query = query.filter(Feature.status == status)

        # Apply sorting
        if sort == "updated_at_desc" or sort is None:
            query = query.order_by(Feature.updated_at.desc())
        elif sort == "updated_at_asc":
            query = query.order_by(Feature.updated_at.asc())
        elif sort == "created_at_desc":
            query = query.order_by(Feature.created_at.desc())
        elif sort == "created_at_asc":
            query = query.order_by(Feature.created_at.asc())
        elif sort == "name_asc":
            query = query.order_by(Feature.name.asc())
        elif sort == "name_desc":
            query = query.order_by(Feature.name.desc())
        else:
            # Default to updated_at_desc
            query = query.order_by(Feature.updated_at.desc())

        total = query.count()
        
        # Apply pagination
        if skip > 0:
            query = query.offset(skip)
        if limit is not None and limit > 0:
            query = query.limit(limit)
        
        features = query.all()

        return features, total

    @staticmethod
    def update_feature(
        db: Session,
        feature_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
    ) -> Optional[Feature]:
        """Update feature."""
        feature = db.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            return None

        if name is not None:
            feature.name = name
        if description is not None:
            feature.description = description
        if status is not None:
            feature.status = status
        if assigned_to is not None:
            feature.assigned_to = assigned_to

        db.commit()
        db.refresh(feature)
        return feature

    @staticmethod
    def delete_feature(db: Session, feature_id: UUID) -> bool:
        """Delete feature (cascade deletes related data)."""
        feature = db.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            return False

        db.delete(feature)
        db.commit()
        return True

    @staticmethod
    def calculate_feature_progress(db: Session, feature_id: UUID) -> dict:
        """Calculate feature progress based on todos and auto-update feature status."""
        feature = db.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            return {"total": 0, "completed": 0, "percentage": 0}

        # Count todos
        # Completed todos are only those with 'done' status (simplified workflow)
        total = db.query(func.count(Todo.id)).filter(Todo.feature_id == feature_id).scalar()
        completed = (
            db.query(func.count(Todo.id))
            .filter(Todo.feature_id == feature_id, Todo.status == "done")
            .scalar()
        )

        percentage = int((completed / total * 100)) if total > 0 else 0

        # Update feature progress
        feature.total_todos = total
        feature.completed_todos = completed
        feature.progress_percentage = percentage
        
        # Auto-update feature status based on progress
        # Workflow: new → in_progress → done → tested → merged
        # - Todos: new → in_progress → done (simplified)
        # - Features: new → in_progress → done → tested → merged (feature-level testing and merging)
        if total > 0:
            in_progress_count = (
                db.query(func.count(Todo.id))
                .filter(Todo.feature_id == feature_id, Todo.status == "in_progress")
                .scalar()
            )
            done_count = (
                db.query(func.count(Todo.id))
                .filter(Todo.feature_id == feature_id, Todo.status == "done")
                .scalar()
            )
            
            if completed == total:
                # All todos are done - feature can be marked as done
                # Note: tested/merged status should be set manually after testing/merging
                if feature.status == "new":
                    feature.status = "done"
                # Don't auto-change from tested/merged back to done
            elif completed > 0 or in_progress_count > 0:
                # Some todos are in progress or done - feature is in progress
                if feature.status == "new":
                    feature.status = "in_progress"
            # If all todos are "new", keep feature status as "new"
        
        db.commit()

        return {"total": total, "completed": completed, "percentage": percentage}

    @staticmethod
    def link_element_to_feature(
        db: Session,
        feature_id: UUID,
        element_id: UUID,
    ) -> bool:
        """Link an element to a feature."""
        # Check if link already exists
        existing = (
            db.query(FeatureElement)
            .filter(
                FeatureElement.feature_id == feature_id,
                FeatureElement.element_id == element_id,
            )
            .first()
        )
        if existing:
            return False

        feature_element = FeatureElement(
            feature_id=feature_id,
            element_id=element_id,
        )
        db.add(feature_element)
        db.commit()
        return True

    @staticmethod
    def get_feature_elements(db: Session, feature_id: UUID) -> List[ProjectElement]:
        """Get all elements linked to a feature."""
        elements = (
            db.query(ProjectElement)
            .join(FeatureElement)
            .filter(FeatureElement.feature_id == feature_id)
            .all()
        )
        return elements

    @staticmethod
    def get_feature_todos(
        db: Session,
        feature_id: UUID,
        status: Optional[str] = None,
    ) -> List[Todo]:
        """Get all todos for a feature."""
        query = db.query(Todo).filter(Todo.feature_id == feature_id)

        if status:
            query = query.filter(Todo.status == status)

        return query.all()


# Global instance
feature_service = FeatureService()
