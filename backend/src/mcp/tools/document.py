"""MCP Tools for document management."""
from typing import Optional, List
from uuid import UUID
from mcp.types import Tool as MCPTool
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.mcp.services.cache import cache_service
from src.services.document_service import DocumentService
from src.services.project_service import ProjectService
from src.services.todo_service import TodoService
from src.services.element_service import ElementService
from src.services.signalr_hub import broadcast_project_update


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
        # Use DocumentService to get document
        document = DocumentService.get_document_by_id(db, UUID(document_id))
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
                    "enum": ["architecture", "adr", "notes"],
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
        # Use DocumentService to get documents by project
        documents, _ = DocumentService.get_documents_by_project(
            db=db,
            project_id=UUID(project_id),
            type=doc_type,
            skip=0,
            limit=1000,  # Large limit for MCP tools
        )

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
        description="Create a new document for a project. Documents are automatically linked to features. Optionally can be linked to an element or todo.",
        inputSchema={
            "type": "object",
            "properties": {
                "projectId": {"type": "string", "description": "Project UUID"},
                "type": {
                    "type": "string",
                    "enum": ["architecture", "adr", "notes"],
                    "description": "Document type",
                },
                "title": {"type": "string", "description": "Document title"},
                "content": {"type": "string", "description": "Document content (Markdown)"},
                "featureId": {"type": "string", "description": "Optional feature UUID to link. If not provided and todoId is provided, will use todo's feature."},
                "elementId": {"type": "string", "description": "Optional element UUID to link"},
                "todoId": {"type": "string", "description": "Optional todo UUID to link (will link to todo's element and feature if featureId not provided)"},
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
    feature_id: Optional[str] = None,
    element_id: Optional[str] = None,
    todo_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    """Handle create document tool call."""
    db = SessionLocal()
    try:
        # Use ProjectService to verify project exists
        project = ProjectService.get_project_by_id(db, UUID(project_id))
        if not project:
            return {"error": "Project not found"}

        # If todo_id is provided, get the element and feature from the todo
        final_element_id = None
        final_feature_id = None
        if todo_id:
            # Use TodoService to get todo
            todo = TodoService.get_todo_by_id(db, UUID(todo_id))
            if not todo:
                return {"error": "Todo not found"}
            # Use todo's element_id
            final_element_id = todo.element_id
            # Use todo's feature_id if feature_id not explicitly provided
            if not feature_id and todo.feature_id:
                final_feature_id = todo.feature_id
            # Verify element belongs to project using ElementService
            if final_element_id:
                element = ElementService.get_element_by_id(db, final_element_id)
                if not element or element.project_id != UUID(project_id):
                    return {"error": "Todo's element does not belong to this project"}
        elif element_id:
            final_element_id = UUID(element_id)
            # Verify element if provided using ElementService
            element = ElementService.get_element_by_id(db, final_element_id)
            if not element or element.project_id != UUID(project_id):
                return {"error": "Element not found or does not belong to this project"}
        
        # Use provided feature_id if available
        if feature_id:
            final_feature_id = UUID(feature_id)

        # Use DocumentService to create document
        document = DocumentService.create_document(
            db=db,
            project_id=UUID(project_id),
            type=type,
            title=title,
            content=content,
            element_id=final_element_id,
            feature_id=final_feature_id,
            tags=tags,
        )

        # Invalidate cache
        cache_service.delete(f"project:{project_id}:documents")
        cache_service.delete(f"document:{document.id}")

        # Broadcast SignalR update (fire and forget)
        import asyncio
        asyncio.create_task(
            broadcast_project_update(
                project_id,
                {
                    "action": "document_created",
                    "document_id": str(document.id),
                    "document_type": document.type,
                    "document_title": document.title,
                    "element_id": str(document.element_id) if document.element_id else None
                }
            )
        )

        return {
            "id": str(document.id),
            "title": document.title,
            "type": document.type,
            "element_id": str(document.element_id) if document.element_id else None,
            "feature_id": str(document.feature_id) if document.feature_id else None,
            "todo_id": todo_id if todo_id else None,
        }
    finally:
        db.close()
