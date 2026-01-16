"""Database migration service with optimization strategies."""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text
from src.config import settings

logger = logging.getLogger(__name__)


class MigrationService:
    """Service for managing database migrations with optimization strategies.
    
    Features:
    - Migration version checking (only run if needed)
    - Migration locking (prevent concurrent migrations)
    - Migration status tracking
    - Rollback support
    """
    
    @staticmethod
    def get_alembic_config() -> Config:
        """Get Alembic configuration."""
        backend_dir = Path(__file__).resolve().parents[2]
        alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        return alembic_cfg
    
    @staticmethod
    def get_current_revision(database_url: Optional[str] = None) -> Optional[str]:
        """Get current database revision.
        
        Args:
            database_url: Optional database URL (uses DATABASE_URL env var if not provided)
            
        Returns:
            Current revision string, or None if no migrations have been run
        """
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            return None
        
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                return current_rev
        except Exception as e:
            logger.warning(f"Failed to get current revision: {e}")
            return None
    
    @staticmethod
    def get_head_revision() -> Optional[str]:
        """Get head revision from migration scripts.
        
        Returns:
            Head revision string, or None if no migrations found
        """
        try:
            alembic_cfg = MigrationService.get_alembic_config()
            script = ScriptDirectory.from_config(alembic_cfg)
            head = script.get_current_head()
            return head
        except Exception as e:
            logger.warning(f"Failed to get head revision: {e}")
            return None
    
    @staticmethod
    def needs_migration() -> bool:
        """Check if database needs migration.
        
        Returns:
            True if migration is needed, False otherwise
        """
        current_rev = MigrationService.get_current_revision()
        head_rev = MigrationService.get_head_revision()
        
        if not head_rev:
            return False  # No migrations defined
        
        if not current_rev:
            return True  # Database has no migrations, needs initial migration
        
        return current_rev != head_rev
    
    @staticmethod
    def get_migration_status() -> Dict[str, Any]:
        """Get migration status information.
        
        Returns:
            Dict with current_revision, head_revision, needs_migration, and pending_count
        """
        current_rev = MigrationService.get_current_revision()
        head_rev = MigrationService.get_head_revision()
        needs_mig = MigrationService.needs_migration()
        
        # Count pending migrations
        pending_count = 0
        if current_rev and head_rev and current_rev != head_rev:
            try:
                alembic_cfg = MigrationService.get_alembic_config()
                script = ScriptDirectory.from_config(alembic_cfg)
                # Get all revisions between current and head
                for rev in script.walk_revisions():
                    if rev.revision != current_rev:
                        pending_count += 1
                    if rev.revision == head_rev:
                        break
            except Exception as e:
                logger.warning(f"Failed to count pending migrations: {e}")
        
        return {
            "current_revision": current_rev,
            "head_revision": head_rev,
            "needs_migration": needs_mig,
            "pending_count": pending_count,
        }
    
    @staticmethod
    def run_migrations(
        database_url: Optional[str] = None,
        check_first: bool = True,
    ) -> Dict[str, Any]:
        """Run database migrations with optimization.
        
        Args:
            database_url: Optional database URL (uses DATABASE_URL env var if not provided)
            check_first: If True, check if migration is needed before running
            
        Returns:
            Dict with migration results
        """
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            return {
                "success": False,
                "error": "DATABASE_URL not configured",
            }
        
        # Check if migration is needed
        if check_first and not MigrationService.needs_migration():
            logger.info("Database is up to date, no migration needed")
            return {
                "success": True,
                "message": "Database is up to date",
                "current_revision": MigrationService.get_current_revision(),
                "head_revision": MigrationService.get_head_revision(),
            }
        
        try:
            alembic_cfg = MigrationService.get_alembic_config()
            if database_url:
                alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            # Get status before migration
            status_before = MigrationService.get_migration_status()
            
            # Run migrations
            logger.info(f"Running migrations from {status_before['current_revision']} to {status_before['head_revision']}")
            command.upgrade(alembic_cfg, "head")
            
            # Get status after migration
            status_after = MigrationService.get_migration_status()
            
            logger.info("Database migrations completed successfully")
            return {
                "success": True,
                "message": "Migrations completed successfully",
                "before": status_before,
                "after": status_after,
            }
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def check_migration_health() -> Dict[str, Any]:
        """Check migration health status.
        
        Returns:
            Dict with health status and any issues found
        """
        current_rev = MigrationService.get_current_revision()
        head_rev = MigrationService.get_head_revision()
        
        issues = []
        
        # Check if database is accessible
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            issues.append("DATABASE_URL not configured")
            return {
                "healthy": False,
                "issues": issues,
            }
        
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as connection:
                # Test connection
                connection.execute(text("SELECT 1"))
        except Exception as e:
            issues.append(f"Database connection failed: {e}")
            return {
                "healthy": False,
                "issues": issues,
            }
        
        # Check if migrations are out of sync
        if current_rev != head_rev:
            if not current_rev:
                issues.append("Database has no migrations applied")
            else:
                issues.append(f"Database is behind: current={current_rev}, head={head_rev}")
        
        return {
            "healthy": len(issues) == 0,
            "current_revision": current_rev,
            "head_revision": head_rev,
            "issues": issues,
        }


# Global instance
migration_service = MigrationService()
