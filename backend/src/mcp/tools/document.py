"""MCP Tools for document management."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.database.models import Document, Project, ProjectElement, Todo


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

    db = SessionLocal()
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

    db = SessionLocal()
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


def get_create_document_tool() -> MCPTool:
    """Get create document tool definition."""
    return MCPTool(
        name="mcp_create_document",
        description="Create a new document for a project, optionally linked to an element or todo",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "type": {
                    "type": "string",
                    "enum": ["architecture", "adr", "domain", "constraints", "runbook", "ai_instructions"],
                    "description": "Document type",
                },
                "title": {"type": "string", "description": "Document title"},
                "content": {"type": "string", "description": "Document content (Markdown)"},
                "elementId": {"type": "string", "description": "Optional element UUID to link"},
                "todoId": {"type": "string", "description": "Optional todo UUID to link (will link to todo's element)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
            },
            "required": ["projectId", "type", "title", "content"],
        },
    )


async def handle_create_document(
    project_id: str,
    type: str,
    title: str,
    content: str,
    element_id: Optional[str] = None,
    todo_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    """Handle create document tool call."""
    db = SessionLocal()
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            return {"error": "Project not found"}

        # If todo_id is provided, get the element from the todo
        if todo_id:
            todo = db.query(Todo).filter(Todo.id == UUID(todo_id)).first()
            if not todo:
                return {"error": "Todo not found"}
            # Use todo's element_id
            element_id = str(todo.element_id)
            # Verify element belongs to project
            element = db.query(ProjectElement).filter(
                ProjectElement.id == todo.element_id,
                ProjectElement.project_id == UUID(project_id)
            ).first()
            if not element:
                return {"error": "Todo's element does not belong to this project"}

        # Verify element if provided
        if element_id:
            element = db.query(ProjectElement).filter(
                ProjectElement.id == UUID(element_id),
                ProjectElement.project_id == UUID(project_id)
            ).first()
            if not element:
                return {"error": "Element not found or does not belong to this project"}

        # Create document
        document = Document(
            project_id=UUID(project_id),
            element_id=UUID(element_id) if element_id else None,
            type=type,
            title=title,
            content=content,
            tags=tags or [],
            version=1,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Invalidate cache
        cache_service.delete(f"project:{project_id}:documents")
        cache_service.delete(f"document:{document.id}")

        return {
            "id": str(document.id),
            "title": document.title,
            "type": document.type,
            "element_id": str(document.element_id) if document.element_id else None,
            "todo_id": todo_id if todo_id else None,
        }
    finally:
        db.close()
