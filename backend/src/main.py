"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.responses import Response
from src.config import settings
import orjson
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
    task_queue_controller,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Run database migrations (optimized - only if needed)
    try:
        from src.services.migration_service import migration_service
        
        # Check migration status
        status = migration_service.get_migration_status()
        logger.info(f"Migration status: current={status['current_revision']}, head={status['head_revision']}, needs_migration={status['needs_migration']}")
        
        if status['needs_migration']:
            logger.info(f"Running {status['pending_count']} pending migration(s)...")
            result = migration_service.run_migrations(check_first=True)
            if result['success']:
                logger.info("Database migrations completed successfully")
                print("✅ Database migrations completed successfully", flush=True)
            else:
                logger.error(f"Migration failed: {result.get('error')}")
                # Don't fail startup - app will still start but DB operations might fail
        else:
            logger.info("Database is up to date, no migration needed")
    except Exception as e:
        logger.error(f"Failed to check/run database migrations: {e}", exc_info=True)
        # Don't fail startup if migrations fail - might be a temporary issue
        # The app will still start, but database operations might fail
    
    # Startup: Start SignalR connection cleanup task
    cleanup_task = None
    try:
        from src.services.signalr.connection_manager import connection_manager
        import asyncio
        
        async def cleanup_dead_connections():
            """Periodically clean up dead SignalR connections."""
            while True:
                try:
                    await asyncio.sleep(60)  # Run every 60 seconds
                    await connection_manager.cleanup_dead_connections(timeout_seconds=120.0)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in SignalR cleanup task: {e}", exc_info=True)
        
        cleanup_task = asyncio.create_task(cleanup_dead_connections())
        logger.info("SignalR connection cleanup task started")
    except Exception as e:
        logger.warning(f"Failed to start SignalR cleanup task: {e}")
    
    # Startup: Start background task worker
    worker_task = None
    try:
        from src.services.task_worker import TaskWorker, task_worker
        from src.services.task_queue import task_queue
        import asyncio
        
        # Create and start worker
        global task_worker
        task_worker = TaskWorker(task_queue)
        worker_task = asyncio.create_task(task_worker.run(poll_interval=1.0))
        logger.info("Background task worker started")
    except Exception as e:
        logger.warning(f"Failed to start background task worker: {e}")
    
    yield
    
    # Shutdown: Stop task worker
    if worker_task:
        if task_worker:
            task_worker.stop()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        logger.info("Background task worker stopped")
    
    # Shutdown: Cancel cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("SignalR connection cleanup task stopped")


# Create FastAPI app with lifespan and optimized JSON serialization
app = FastAPI(
    title="InTracker API",
    description="""
    InTracker is an AI-first project management system API.
    
    ## Features
    
    * **Project Management**: Create and manage projects with features, todos, and elements
    * **Team Collaboration**: Team-based access control and member management
    * **GitHub Integration**: Connect GitHub repositories, manage branches, issues, and PRs
    * **Session Tracking**: Track development sessions with goals and progress
    * **Documentation**: Store and manage project documentation
    * **MCP Integration**: Model Context Protocol server for AI agent integration
    
    ## Authentication
    
    Most endpoints require JWT authentication. Include the access token in the Authorization header:
    
    ```
    Authorization: Bearer <access_token>
    ```
    
    Get your access token by:
    1. Registering with an invitation code: `POST /auth/register`
    2. Logging in: `POST /auth/login`
    3. Using the refresh token: `POST /auth/refresh`
    
    ## Rate Limiting
    
    API rate limiting is not currently implemented. Please use the API responsibly.
    
    ## Support
    
    For issues and questions, please contact the development team.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication endpoints for user registration, login, and token management.",
        },
        {
            "name": "projects",
            "description": "Project management endpoints for creating, updating, and managing projects.",
        },
        {
            "name": "features",
            "description": "Feature management endpoints for organizing work into features.",
        },
        {
            "name": "todos",
            "description": "Todo management endpoints for tracking individual tasks.",
        },
        {
            "name": "elements",
            "description": "Element management endpoints for organizing project structure.",
        },
        {
            "name": "sessions",
            "description": "Session tracking endpoints for development sessions.",
        },
        {
            "name": "documents",
            "description": "Document management endpoints for project documentation.",
        },
        {
            "name": "github",
            "description": "GitHub integration endpoints for repository and branch management.",
        },
        {
            "name": "ideas",
            "description": "Idea management endpoints for capturing and converting ideas to projects.",
        },
        {
            "name": "teams",
            "description": "Team management endpoints for team creation, member management, and invitations.",
        },
        {
            "name": "admin",
            "description": "Admin endpoints for user management, migrations, and system administration.",
        },
        {
            "name": "mcp",
            "description": "MCP (Model Context Protocol) server endpoints for AI agent integration.",
        },
        {
            "name": "mcp-keys",
            "description": "MCP API key management endpoints for generating and managing API keys.",
        },
        {
            "name": "audit",
            "description": "Audit trail endpoints for tracking changes to entities.",
        },
        {
            "name": "tasks",
            "description": "Task queue endpoints for monitoring and managing background tasks.",
        },
    ],
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
    # In production, NEVER allow all origins for security
    if settings.CORS_ORIGIN == "*":
        logger.warning(
            "⚠️  SECURITY WARNING: CORS_ORIGIN is set to '*' in production. "
            "This is insecure and should be changed to specific origins."
        )
        # Still allow all for now, but log warning
        cors_origins = ["*"]
    else:
        # Use explicit origin list (comma-separated)
        cors_origins = [origin.strip() for origin in settings.CORS_ORIGIN.split(",")]

# Security headers middleware (add before CORS)
from src.api.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# Performance monitoring middleware (add early to measure all requests)
from src.api.middleware.performance import PerformanceMiddleware
app.add_middleware(PerformanceMiddleware)

# CORS middleware
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
app.include_router(task_queue_controller.router)


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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler. Skips HTTPException as FastAPI handles those.
    
    NOTE: For ASGI apps (like MCP transport) that handle their own responses,
    we need to be careful not to send duplicate responses.
    """
    from fastapi import HTTPException
    import logging
    
    # Don't handle HTTPException - FastAPI already handles those
    if isinstance(exc, HTTPException):
        raise exc
    
    # Don't handle RuntimeError about response already sent - this happens with ASGI apps
    # that handle their own responses (like MCP transport)
    if isinstance(exc, RuntimeError) and "response already" in str(exc).lower():
        logging.warning(f"RuntimeError: Response already sent (likely from ASGI app): {exc}")
        # Don't try to send response - it was already sent by the ASGI app
        # Return None to indicate we handled it (but didn't send a response)
        return None
    
    # Handle all other exceptions
    # Always log the error for debugging
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    
    from src.api.utils.json_response import OptimizedJSONResponse
    
    return OptimizedJSONResponse(
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
