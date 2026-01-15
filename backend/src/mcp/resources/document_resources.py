"""MCP Resources for documents."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.services.document_service import DocumentService


def get_document_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get document resources."""
    db = SessionLocal()
    try:
        if project_id:
            # Use DocumentService to get documents by project
            documents, _ = DocumentService.get_documents_by_project(
                db=db,
                project_id=UUID(project_id),
                type=None,
                skip=0,
                limit=1000,  # Large limit for resources
            )
        else:
            # List all documents - need to query directly as DocumentService doesn't have list_all method
            # This is acceptable for resources as it's a simple read operation
            from src.database.models import Document
            documents = db.query(Document).all()
        
        return [
            Resource(
                uri=f"intracker://document/{d.id}",
                name=f"Document: {d.title}",
                description=f"{d.type} (v{d.version})",
                mimeType="text/markdown" if d.type in ["architecture", "adr", "notes"] else "application/json",
            )
            for d in documents
        ]
    finally:
        db.close()


async def read_document_resource(uri: str) -> str:
    """Read document resource."""
    # Convert URI to string (MCP SDK may pass AnyUrl object)
    uri_str = str(uri)
    
    # Parse URI: intracker://document/{document_id}
    if not uri_str.startswith("intracker://document/"):
        raise ValueError(f"Invalid document resource URI: {uri_str}")

    document_id = uri_str.replace("intracker://document/", "")
    db = SessionLocal()
    try:
        # Use DocumentService to get document
        document = DocumentService.get_document_by_id(db, UUID(document_id))
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Return markdown content for all document types (all are markdown now)
        return document.content
    finally:
        db.close()
