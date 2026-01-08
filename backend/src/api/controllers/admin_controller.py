"""Admin controller - refactored into smaller modules.

This module provides the shared router for all admin endpoints.
The actual endpoints are defined in:
- admin_migration: Migration endpoints
- admin_users: User management endpoints
- admin_invitations: Invitation management endpoints
"""
from fastapi import APIRouter

# Create shared router for all admin endpoints
router = APIRouter(prefix="/admin", tags=["admin"])

# Import all admin modules to register their routes
from . import admin_migration, admin_users, admin_invitations

__all__ = ["router"]
