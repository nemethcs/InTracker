# Refactoring Plan: admin_controller.py (630 lines)

## Current Structure Analysis

The `admin_controller.py` file contains 24 endpoints organized into 3 logical groups:

### 1. Migration (Lines ~22-60)
- `run_migrations()` - Run database migrations

### 2. User Management (Lines ~63-499)
- `create_user()` - Create a user
- `update_user_role()` - Update user role by ID
- `update_user_role_by_email()` - Update user role by email
- `list_users()` - List all users with filters
- `get_user()` - Get user by ID
- `update_user()` - Update user details
- `delete_user_by_id()` - Delete user by ID

### 3. Invitation Management (Lines ~504-630)
- `create_admin_invitation()` - Create admin invitation code
- `list_invitations()` - List all invitations
- `get_invitation()` - Get invitation by code
- `delete_invitation()` - Delete invitation code

## Refactoring Strategy

Split into 3 separate modules:

### 1. `admin_migration.py` (~60 lines)
- Migration endpoint
- Shared router import

### 2. `admin_users.py` (~400 lines)
- All user management endpoints
- Shared router import

### 3. `admin_invitations.py` (~170 lines)
- All invitation management endpoints
- Shared router import

## Implementation Steps

1. Create a shared router in `admin_controller.py` (or separate `admin_router.py`)
2. Create new module files
3. Move functions to appropriate modules
4. Import router from shared location
5. Update main.py to import all admin routers
6. Test all functionality

## Dependencies

All modules will share:
- `APIRouter` from FastAPI
- `get_db` from `src.database.base`
- `get_current_admin_user` from `src.api.middleware.auth`
- `settings` from `src.config`
- Models: `User`, `InvitationCode`, `TeamMember`, `Team`
- Services: `AuthService`, `InvitationService`, `TeamService`
