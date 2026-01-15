"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from src.config import settings
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
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
    admin_controller,
    team_controller,
    mcp_key_controller,
    audit_controller,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Run database migrations
    try:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            logger.info("Running database migrations...")
            from alembic import command
            from alembic.config import Config
            
            backend_dir = Path(__file__).resolve().parents[1]
            alembic_cfg = Config(str(backend_dir / "alembic.ini"))
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
            print("✅ Database migrations completed successfully", flush=True)  # Also print for visibility
        else:
            logger.warning("DATABASE_URL not set, skipping migrations")
    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}")
        # Don't fail startup if migrations fail - might be a temporary issue
        # The app will still start, but database operations might fail
    
    yield
    
    # Shutdown: cleanup if needed
    pass


# Create FastAPI app with lifespan
app = FastAPI(
    title="InTracker API",
    description="AI-first project management system API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
# For development, always allow localhost origins
if settings.NODE_ENV == "development":
    # In development, always allow common localhost origins
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    # Also add CORS_ORIGIN if it's not "*" and not already in the list
    if settings.CORS_ORIGIN != "*" and settings.CORS_ORIGIN not in cors_origins:
        cors_origins.append(settings.CORS_ORIGIN)
else:
    # In production, use CORS_ORIGIN or allow all
    if settings.CORS_ORIGIN != "*":
        cors_origins = [settings.CORS_ORIGIN]
    else:
        cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
app.include_router(admin_controller.router)
app.include_router(team_controller.router)
app.include_router(mcp_key_controller.router)
app.include_router(audit_controller.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "auto_reload": "disabled"  # Added: Backend auto-reload is now disabled for stability
    }


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


# Import error handlers
from src.api.middleware.error_handler import (
    handle_http_exception,
    handle_validation_error,
    handle_generic_exception,
)
from fastapi.exceptions import RequestValidationError


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with standardized error format."""
    return handle_http_exception(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized format."""
    return handle_validation_error(request, exc)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions.
    
    NOTE: For ASGI apps (like MCP transport) that handle their own responses,
    we need to be careful not to send duplicate responses.
    """
    from fastapi import HTTPException
    import logging
    
    # Don't handle HTTPException - already handled by http_exception_handler
    if isinstance(exc, HTTPException):
        raise exc
    
    # Don't handle RuntimeError about response already sent - this happens with ASGI apps
    # that handle their own responses (like MCP transport)
    if isinstance(exc, RuntimeError) and "response already" in str(exc).lower():
        logging.warning(f"RuntimeError: Response already sent (likely from ASGI app): {exc}")
        # Don't try to send response - it was already sent by the ASGI app
        # Return None to indicate we handled it (but didn't send a response)
        return None
    
    # Handle all other exceptions with standardized format
    return handle_generic_exception(request, exc)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.NODE_ENV == "development",
    )
