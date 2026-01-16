"""Admin migration endpoints."""
from fastapi import APIRouter, HTTPException, status, Header, Depends, Query
from src.api.middleware.auth import get_current_admin_user
from src.config import settings
from src.services.migration_service import migration_service

# Import shared router from admin_controller
from .admin_controller import router


@router.post("/migrate")
async def run_migrations(
    api_key: str = Header(..., alias="X-API-Key"),
    current_user: dict = Depends(get_current_admin_user),
    check_first: bool = Query(True, description="Check if migration is needed before running"),
):
    """Run database migrations. Requires admin role or API key.
    
    Optimized to only run migrations if needed (unless check_first=False).
    """
    # Check API key (for MCP/admin scripts) OR admin role
    if api_key != settings.MCP_API_KEY and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or admin access required",
        )
    
    try:
        result = migration_service.run_migrations(check_first=check_first)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Migration failed'),
            )
        
        return {
            "message": result.get('message', 'Migrations completed successfully'),
            "status": "success",
            "migration_status": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}",
        )


@router.get("/migrate/status")
async def get_migration_status(
    api_key: str = Header(..., alias="X-API-Key"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get database migration status. Requires admin role or API key."""
    # Check API key (for MCP/admin scripts) OR admin role
    if api_key != settings.MCP_API_KEY and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or admin access required",
        )
    
    try:
        status = migration_service.get_migration_status()
        health = migration_service.check_migration_health()
        
        return {
            "migration_status": status,
            "health": health,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration status: {str(e)}",
        )
