"""MCP Resources for documents."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.services.document_service import DocumentService


def get_document_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get document resources.
    
    PERFORMANCE OPTIMIZATION: Returns empty list to speed up MCP initialization.
    Resources are accessed dynamically via read_resource() when needed.
    This prevents slow database queries during initial connection.
    """
    # Return empty list for fast initialization
    # Resources will be loaded dynamically when accessed via read_resource()
    return []


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

        # Return markdown content for markdown types, JSON for others
        if document.type in ["architecture", "adr", "runbook"]:
            return document.content
        else:
            import json
            return json.dumps({
                "id": str(document.id),
                "title": document.title,
                "type": document.type,
                "content": document.content,
                "version": document.version,
            }, indent=2)
    finally:
        db.close()
