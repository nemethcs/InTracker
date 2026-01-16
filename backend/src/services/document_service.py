"""Document service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from src.database.models import Document
from src.database.base import set_current_user_id, reset_current_user_id


class DocumentService:
    """Service for document operations."""

    @staticmethod
    def create_document(
        db: Session,
        project_id: UUID,
        type: str,
        title: str,
        content: str,
        element_id: Optional[UUID] = None,
        feature_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        current_user_id: Optional[UUID] = None,
    ) -> Document:
        """Create a new document.
        
        If feature_id is provided, the document will be automatically linked to that feature.
        If element_id is also provided, it will be linked as well.
        """
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
            # If feature_id is provided, verify it belongs to the project
            if feature_id:
                from src.database.models import Feature
                feature = db.query(Feature).filter(
                    Feature.id == feature_id,
                    Feature.project_id == project_id
                ).first()
                if not feature:
                    raise ValueError("Feature not found or does not belong to project")
            
            document = Document(
                project_id=project_id,
                element_id=element_id,
                feature_id=feature_id,
                type=type,
                title=title,
                content=content,
                tags=tags or [],
                version=1,
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        finally:
            if token:
                reset_current_user_id(token)

    @staticmethod
    def get_document_by_id(db: Session, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def get_documents_by_project(
        db: Session,
        project_id: UUID,
        type: Optional[str] = None,
        element_id: Optional[UUID] = None,
        feature_id: Optional[UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Document], int]:
        """Get documents for a project with filtering."""
        query = db.query(Document).filter(Document.project_id == project_id)

        if type:
            query = query.filter(Document.type == type)

        if element_id:
            query = query.filter(Document.element_id == element_id)

        if feature_id:
            query = query.filter(Document.feature_id == feature_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Document.title.ilike(search_pattern),
                    Document.content.ilike(search_pattern),
                )
            )

        total = query.count()
        documents = query.order_by(Document.updated_at.desc()).offset(skip).limit(limit).all()

        return documents, total

    @staticmethod
    def update_document(
        db: Session,
        document_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        current_user_id: Optional[UUID] = None,
    ) -> Optional[Document]:
        """Update document and increment version."""
        # Set current user ID for audit trail
        token = None
        if current_user_id:
            token = set_current_user_id(current_user_id)
        
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None

            if title is not None:
                document.title = title
            if content is not None:
                document.content = content
            if tags is not None:
                document.tags = tags

            # Increment version on content change
            if content is not None:
                document.version += 1

            db.commit()
            db.refresh(document)
            return document
        finally:
            if token:
                reset_current_user_id(token)

    @staticmethod
    def delete_document(db: Session, document_id: UUID) -> bool:
        """Delete document."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False

        db.delete(document)
        db.commit()
        return True


# Global instance
document_service = DocumentService()
