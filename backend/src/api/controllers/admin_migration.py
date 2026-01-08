"""Admin migration endpoints."""
from fastapi import APIRouter, HTTPException, status, Header, Depends
from src.api.middleware.auth import get_current_admin_user
from src.config import settings
from alembic import command
from alembic.config import Config
from pathlib import Path
import os

# Import shared router from admin_controller
from .admin_controller import router


@router.post("/migrate")
async def run_migrations(
    api_key: str = Header(..., alias="X-API-Key"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Run database migrations. Requires admin role or API key."""
    # Check API key (for MCP/admin scripts) OR admin role
    if api_key != settings.MCP_API_KEY and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or admin access required",
        )
    
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DATABASE_URL not configured",
            )
        
        # Set up Alembic
        backend_dir = Path(__file__).resolve().parents[3]
        alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        return {
            "message": "Migrations completed successfully",
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}",
        )
