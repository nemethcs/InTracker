"""MCP Tools for document management."""
from typing import Optional
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.services.database import get_db_session
from src.services.cache import cache_service
from src.models import Document


def get_get_document_tool() -> MCPTool:
    """Get document tool definition."""
    return MCPTool(
        name="mcp_get_document",
        description="Get document content",
        inputSchema={
            "type": "object",
            "properties": {
                "documentId": {"type": "string", "description": "Document UUID"},
            },
            "required": ["documentId"],
        },
    )


async def handle_get_document(document_id: str) -> dict:
    """Handle get document tool call."""
    cache_key = f"document:{document_id}"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        document = db.query(Document).filter(Document.id == UUID(document_id)).first()
        if not document:
            return {"error": "Document not found"}

        result = {
            "id": str(document.id),
            "title": document.title,
            "type": document.type,
            "content": document.content,
            "version": document.version,
        }

        cache_service.set(cache_key, result, ttl=600)  # 10 min TTL
        return result
    finally:
        db.close()


def get_list_documents_tool() -> MCPTool:
    """Get list documents tool definition."""
    return MCPTool(
        name="mcp_list_documents",
        description="List documents for a project",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "type": {
                    "type": "string",
                    "enum": ["architecture", "adr", "domain", "constraints", "runbook", "ai_instructions"],
                    "description": "Filter by document type",
                },
            },
            "required": ["projectId"],
        },
    )


async def handle_list_documents(project_id: str, doc_type: Optional[str] = None) -> dict:
    """Handle list documents tool call."""
    cache_key = f"project:{project_id}:documents"
    if doc_type:
        cache_key += f":type:{doc_type}"
    
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    db = get_db_session()
    try:
        query = db.query(Document).filter(Document.project_id == UUID(project_id))
        if doc_type:
            query = query.filter(Document.type == doc_type)

        documents = query.order_by(Document.updated_at.desc()).all()

        result = {
            "project_id": project_id,
            "documents": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "type": d.type,
                    "version": d.version,
                }
                for d in documents
            ],
            "count": len(documents),
        }

        cache_service.set(cache_key, result, ttl=300)  # 5 min TTL
        return result
    finally:
        db.close()
