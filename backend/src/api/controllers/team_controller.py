"""Team controller - refactored into smaller modules.

This module provides the shared router for all team endpoints.
The actual endpoints are defined in:
- team_crud: Team CRUD operations (create, list, get, update, delete)
- team_members: Team member management (get, add, remove, update role)
- team_settings: Team settings (language, invitations)
"""
from fastapi import APIRouter

# Create shared router for all team endpoints
router = APIRouter(prefix="/teams", tags=["teams"])

# Import all team modules to register their routes
# Note: Import order matters - import after router creation to avoid circular imports
from . import team_crud  # noqa: E402
from . import team_members  # noqa: E402
from . import team_settings  # noqa: E402

__all__ = ["router"]
