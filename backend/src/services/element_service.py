"""Element service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models import ProjectElement, ElementDependency, Todo


class ElementService:
    """Service for element operations."""

    @staticmethod
    def create_element(
        db: Session,
        project_id: UUID,
        type: str,
        title: str,
        description: Optional[str] = None,
        status: str = "todo",
        parent_id: Optional[UUID] = None,
        position: Optional[int] = None,
        definition_of_done: Optional[str] = None,
    ) -> ProjectElement:
        """Create a new element."""
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
        """Build hierarchical element tree."""
        elements = ElementService.get_project_elements_tree(db, project_id, parent_id)
        result = []

        for element in elements:
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
    ) -> Optional[ProjectElement]:
        """Update element."""
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
