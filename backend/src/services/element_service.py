"""Element service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from src.database.models import ProjectElement, ElementDependency, Todo
from src.database.base import set_current_user_id, reset_current_user_id


class ElementService:
    """Service for element operations."""

    @staticmethod
    def create_element(
        db: Session,
        project_id: UUID,
        type: str,
        title: str,
        description: Optional[str] = None,
        status: str = "new",
        parent_id: Optional[UUID] = None,
        position: Optional[int] = None,
        definition_of_done: Optional[str] = None,
        current_user_id: Optional[UUID] = None,
    ) -> ProjectElement:
        """Create a new element."""
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
            # Verify parent exists and belongs to same project if provided
            if parent_id:
                parent = (
                    db.query(ProjectElement)
                    .filter(
                        ProjectElement.id == parent_id,
                        ProjectElement.project_id == project_id,
                    )
                    .first()
                )
                if not parent:
                    raise ValueError("Parent element not found or doesn't belong to project")

            element = ProjectElement(
                project_id=project_id,
                parent_id=parent_id,
                type=type,
                title=title,
                description=description,
                status=status,
                position=position,
                definition_of_done=definition_of_done,
            )
            db.add(element)
            db.commit()
            db.refresh(element)
            return element
        finally:
            if token:
                reset_current_user_id(token)

    @staticmethod
    def get_element_by_id(db: Session, element_id: UUID) -> Optional[ProjectElement]:
        """Get element by ID."""
        return db.query(ProjectElement).filter(ProjectElement.id == element_id).first()

    @staticmethod
    def get_project_elements_tree(
        db: Session,
        project_id: UUID,
        parent_id: Optional[UUID] = None,
    ) -> List[ProjectElement]:
        """Get project elements as a tree structure."""
        query = db.query(ProjectElement).filter(ProjectElement.project_id == project_id)

        if parent_id is None:
            query = query.filter(ProjectElement.parent_id.is_(None))
        else:
            query = query.filter(ProjectElement.parent_id == parent_id)

        return query.order_by(ProjectElement.position, ProjectElement.created_at).all()

    @staticmethod
    def build_element_tree(
        db: Session,
        project_id: UUID,
        parent_id: Optional[UUID] = None,
    ) -> List[dict]:
        """Build hierarchical element tree with statistics."""
        from src.database.models import Todo, FeatureElement
        from sqlalchemy import func

        elements = ElementService.get_project_elements_tree(db, project_id, parent_id)
        result = []

        for element in elements:
            # Count todos for this element
            todos_count = db.query(func.count(Todo.id)).filter(
                Todo.element_id == element.id
            ).scalar() or 0
            
            todos_done_count = db.query(func.count(Todo.id)).filter(
                Todo.element_id == element.id,
                Todo.status == "done"
            ).scalar() or 0

            # Count features linked to this element
            features_count = db.query(func.count(FeatureElement.feature_id)).filter(
                FeatureElement.element_id == element.id
            ).scalar() or 0

            # Get linked feature names
            from src.database.models import Feature
            linked_features = (
                db.query(Feature)
                .join(FeatureElement)
                .filter(FeatureElement.element_id == element.id)
                .all()
            )
            linked_feature_names = [f.name for f in linked_features]

            element_dict = {
                "id": str(element.id),
                "project_id": str(element.project_id),
                "parent_id": str(element.parent_id) if element.parent_id else None,
                "type": element.type,
                "title": element.title,
                "description": element.description,
                "status": element.status,
                "position": element.position,
                "created_at": element.created_at.isoformat(),
                "updated_at": element.updated_at.isoformat(),
                "todos_count": todos_count,
                "todos_done_count": todos_done_count,
                "features_count": features_count,
                "linked_features": linked_feature_names,
                "children": ElementService.build_element_tree(db, project_id, element.id),
            }
            result.append(element_dict)

        return result

    @staticmethod
    def get_element_with_todos(
        db: Session,
        element_id: UUID,
    ) -> Optional[dict]:
        """Get element with todos and dependencies."""
        element = db.query(ProjectElement).filter(ProjectElement.id == element_id).first()
        if not element:
            return None

        # Get todos
        todos = db.query(Todo).filter(Todo.element_id == element_id).all()

        # Get dependencies
        dependencies = (
            db.query(ElementDependency)
            .filter(ElementDependency.element_id == element_id)
            .all()
        )

        return {
            "element": element,
            "todos": todos,
            "dependencies": dependencies,
        }

    @staticmethod
    def update_element(
        db: Session,
        element_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        position: Optional[int] = None,
        definition_of_done: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        current_user_id: Optional[UUID] = None,
    ) -> Optional[ProjectElement]:
        """Update element."""
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
            element = db.query(ProjectElement).filter(ProjectElement.id == element_id).first()
            if not element:
                return None

            if title is not None:
                element.title = title
            if description is not None:
                element.description = description
            if status is not None:
                element.status = status
            if position is not None:
                element.position = position
            if definition_of_done is not None:
                element.definition_of_done = definition_of_done
            if parent_id is not None:
                # Verify parent exists and belongs to same project
                if parent_id:
                    parent = (
                        db.query(ProjectElement)
                        .filter(
                            ProjectElement.id == parent_id,
                            ProjectElement.project_id == element.project_id,
                        )
                        .first()
                    )
                    if not parent:
                        raise ValueError("Parent element not found or doesn't belong to project")
                element.parent_id = parent_id

            db.commit()
            db.refresh(element)
            return element
        finally:
            if token:
                reset_current_user_id(token)

    @staticmethod
    def update_element_status_by_todos(db: Session, element_id: UUID) -> Optional[ProjectElement]:
        """Update element status based on todo completion."""
        element = db.query(ProjectElement).filter(ProjectElement.id == element_id).first()
        if not element:
            return None

        # Count todos
        total = db.query(func.count(Todo.id)).filter(
            Todo.element_id == element_id
        ).scalar() or 0

        if total == 0:
            # No todos - keep current status
            return element

        done = db.query(func.count(Todo.id)).filter(
            Todo.element_id == element_id,
            Todo.status == "done"
        ).scalar() or 0

        in_progress = db.query(func.count(Todo.id)).filter(
            Todo.element_id == element_id,
            Todo.status == "in_progress"
        ).scalar() or 0

        # Determine new status
        if done == total:
            new_status = "done"
        elif done > 0 or in_progress > 0:
            new_status = "in_progress"
        else:
            new_status = "new"

        # Update if different
        if element.status != new_status:
            element.status = new_status
            db.commit()
            db.refresh(element)

        return element

    @staticmethod
    def update_parent_statuses(db: Session, element_id: UUID) -> None:
        """Recursively update parent element statuses based on children."""
        element = db.query(ProjectElement).filter(ProjectElement.id == element_id).first()
        if not element or not element.parent_id:
            return

        # Get parent
        parent = db.query(ProjectElement).filter(ProjectElement.id == element.parent_id).first()
        if not parent:
            return

        # Get all children
        children = db.query(ProjectElement).filter(
            ProjectElement.parent_id == parent.id
        ).all()

        if not children:
            return

        # Count children by status
        done_count = sum(1 for c in children if c.status == "done")
        in_progress_count = sum(1 for c in children if c.status == "in_progress")
        total = len(children)

        # Determine parent status
        if done_count == total:
            new_status = "done"
        elif done_count > 0 or in_progress_count > 0:
            new_status = "in_progress"
        else:
            new_status = "new"

        # Update if different
        if parent.status != new_status:
            parent.status = new_status
            db.commit()
            db.refresh(parent)

            # Recursively update parent's parent
            ElementService.update_parent_statuses(db, parent.id)

    @staticmethod
    def delete_element(db: Session, element_id: UUID) -> bool:
        """Delete element (cascade deletes children and todos)."""
        element = db.query(ProjectElement).filter(ProjectElement.id == element_id).first()
        if not element:
            return False

        db.delete(element)
        db.commit()
        return True

    @staticmethod
    def add_dependency(
        db: Session,
        element_id: UUID,
        depends_on_element_id: UUID,
        dependency_type: str,
    ) -> ElementDependency:
        """Add dependency between elements."""
        # Check for circular dependency
        if element_id == depends_on_element_id:
            raise ValueError("Element cannot depend on itself")

        # Check if reverse dependency exists (would create cycle)
        reverse = (
            db.query(ElementDependency)
            .filter(
                ElementDependency.element_id == depends_on_element_id,
                ElementDependency.depends_on_element_id == element_id,
            )
            .first()
        )
        if reverse:
            raise ValueError("Circular dependency detected")

        # Check if dependency already exists
        existing = (
            db.query(ElementDependency)
            .filter(
                ElementDependency.element_id == element_id,
                ElementDependency.depends_on_element_id == depends_on_element_id,
            )
            .first()
        )
        if existing:
            raise ValueError("Dependency already exists")

        dependency = ElementDependency(
            element_id=element_id,
            depends_on_element_id=depends_on_element_id,
            dependency_type=dependency_type,
        )
        db.add(dependency)
        db.commit()
        db.refresh(dependency)
        return dependency

    @staticmethod
    def get_element_dependencies(
        db: Session,
        element_id: UUID,
    ) -> List[ElementDependency]:
        """Get all dependencies for an element."""
        return (
            db.query(ElementDependency)
            .filter(ElementDependency.element_id == element_id)
            .all()
        )

    @staticmethod
    def remove_dependency(
        db: Session,
        element_id: UUID,
        depends_on_element_id: UUID,
    ) -> bool:
        """Remove dependency."""
        dependency = (
            db.query(ElementDependency)
            .filter(
                ElementDependency.element_id == element_id,
                ElementDependency.depends_on_element_id == depends_on_element_id,
            )
            .first()
        )
        if not dependency:
            return False

        db.delete(dependency)
        db.commit()
        return True


# Global instance
element_service = ElementService()
