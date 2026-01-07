"""MCP Resources for documents."""
from typing import Optional
from uuid import UUID
from mcp.types import Resource
from sqlalchemy.orm import Session
from src.database.base import get_db_session
from src.database.models import Document


def get_document_resources(project_id: Optional[str] = None) -> list[Resource]:
    """Get document resources."""
    db = get_db_session()
    try:
        if project_id:
            documents = db.query(Document).filter(Document.project_id == UUID(project_id)).all()
            return [
                Resource(
                    uri=f"intracker://document/{d.id}",
                    name=f"Document: {d.title}",
                    description=f"{d.type} (v{d.version})",
                    mimeType="text/markdown" if d.type in ["architecture", "adr", "runbook"] else "application/json",
                )
                for d in documents
            ]
        else:
            # List all documents
            documents = db.query(Document).all()
            return [
                Resource(
                    uri=f"intracker://document/{d.id}",
                    name=f"Document: {d.title}",
                    description=f"{d.type} (v{d.version})",
                    mimeType="text/markdown" if d.type in ["architecture", "adr", "runbook"] else "application/json",
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
    db = get_db_session()
    try:
        document = db.query(Document).filter(Document.id == UUID(document_id)).first()
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
