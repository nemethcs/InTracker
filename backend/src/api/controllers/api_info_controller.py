"""API information and versioning controller."""
from fastapi import APIRouter
from src.api.versioning import DEFAULT_API_VERSION, LATEST_API_VERSION, APIVersion

router = APIRouter(tags=["api"])


@router.get("/api")
async def api_info():
    """Get API information including versioning details."""
    return {
        "message": "InTracker API",
        "version": "0.1.0",
        "api_versioning": {
            "default_version": DEFAULT_API_VERSION.value,
            "latest_version": LATEST_API_VERSION.value,
            "supported_versions": [v.value for v in APIVersion],
            "versioning_strategy": "url_path",
            "version_format": "/api/v{version}/{endpoint}",
        },
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "docs": "/docs",
            "v1": {
                "base_url": "/v1",
                "description": "API version 1 (current)",
                "endpoints": {
                    "auth": "/v1/auth",
                    "projects": "/v1/projects",
                    "features": "/v1/features",
                    "todos": "/v1/todos",
                    "elements": "/v1/elements",
                    "sessions": "/v1/sessions",
                    "documents": "/v1/documents",
                    "github": "/v1/github",
                    "ideas": "/v1/ideas",
                    "teams": "/v1/teams",
                    "admin": "/v1/admin",
                    "tasks": "/v1/tasks",
                },
            },
            "legacy": {
                "base_url": "/",
                "description": "Legacy endpoints without version prefix (deprecated)",
                "deprecation_warning": "Legacy endpoints will be removed in a future version. Please migrate to /v1 endpoints.",
            },
        },
    }


@router.get("/api/versions")
async def list_api_versions():
    """List all supported API versions."""
    return {
        "versions": [
            {
                "version": v.value,
                "is_default": v == DEFAULT_API_VERSION,
                "is_latest": v == LATEST_API_VERSION,
                "status": "stable" if v == APIVersion.V1 else "deprecated",
            }
            for v in APIVersion
        ],
        "default_version": DEFAULT_API_VERSION.value,
        "latest_version": LATEST_API_VERSION.value,
    }
