"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config import settings
from src.api.controllers import (
    auth_controller,
    project_controller,
    feature_controller,
    todo_controller,
    element_controller,
    session_controller,
    document_controller,
    github_controller,
    idea_controller,
    signalr_controller,
    mcp_controller,
)

# Create FastAPI app
app = FastAPI(
    title="InTracker API",
    description="AI-first project management system API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN] if settings.CORS_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_controller.router)
app.include_router(project_controller.router)
app.include_router(feature_controller.router)
app.include_router(todo_controller.router)
app.include_router(element_controller.router)
app.include_router(session_controller.router)
app.include_router(document_controller.router)
app.include_router(github_controller.router)
app.include_router(idea_controller.router)
app.include_router(signalr_controller.router)
app.include_router(mcp_controller.router)

# Register MCP ASGI routes
mcp_controller.register_mcp_routes(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "InTracker API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "docs": "/docs",
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "refresh": "POST /auth/refresh",
                "me": "GET /auth/me",
            },
            "projects": {
                "list": "GET /projects",
                "create": "POST /projects",
                "get": "GET /projects/{id}",
                "update": "PUT /projects/{id}",
                "delete": "DELETE /projects/{id}",
            },
            "features": {
                "list": "GET /features/project/{project_id}",
                "create": "POST /features",
                "get": "GET /features/{id}",
                "update": "PUT /features/{id}",
                "delete": "DELETE /features/{id}",
                "todos": "GET /features/{id}/todos",
                "elements": "GET /features/{id}/elements",
                "link_element": "POST /features/{id}/elements/{element_id}",
                "calculate_progress": "POST /features/{id}/calculate-progress",
            },
            "todos": {
                "list": "GET /todos",
                "create": "POST /todos",
                "get": "GET /todos/{id}",
                "update": "PUT /todos/{id}",
                "delete": "DELETE /todos/{id}",
                "update_status": "PUT /todos/{id}/status",
                "assign": "POST /todos/{id}/assign",
            },
            "elements": {
                "create": "POST /elements",
                "get": "GET /elements/{id}",
                "update": "PUT /elements/{id}",
                "delete": "DELETE /elements/{id}",
                "tree": "GET /elements/project/{project_id}/tree",
                "dependencies": "GET /elements/{id}/dependencies",
                "add_dependency": "POST /elements/{id}/dependencies",
                "remove_dependency": "DELETE /elements/{id}/dependencies/{depends_on_id}",
            },
            "sessions": {
                "create": "POST /sessions",
                "list": "GET /sessions/project/{project_id}",
                "get": "GET /sessions/{id}",
                "update": "PUT /sessions/{id}",
                "end": "POST /sessions/{id}/end",
            },
            "documents": {
                "create": "POST /documents",
                "list": "GET /documents/project/{project_id}",
                "get": "GET /documents/{id}",
                "content": "GET /documents/{id}/content",
                "update": "PUT /documents/{id}",
                "delete": "DELETE /documents/{id}",
            },
            "github": {
                "connect": "POST /github/projects/{project_id}/connect",
                "get_repo": "GET /github/projects/{project_id}/repo",
                "list_branches": "GET /github/projects/{project_id}/branches",
                "create_branch": "POST /github/branches",
                "get_branch": "GET /github/branches/{id}",
                "feature_branches": "GET /github/features/{feature_id}/branches",
                "webhook": "POST /github/webhook",
            },
            "ideas": {
                "list": "GET /ideas",
                "create": "POST /ideas",
                "get": "GET /ideas/{id}",
                "update": "PUT /ideas/{id}",
                "delete": "DELETE /ideas/{id}",
                "convert": "POST /ideas/{id}/convert",
            },
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.NODE_ENV == "development" else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.NODE_ENV == "development",
    )
