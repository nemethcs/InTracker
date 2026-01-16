# Database Migration Optimization

## Overview

The database migration strategy has been optimized to improve startup performance and reduce unnecessary database operations.

## Key Improvements

### 1. Migration Version Checking

**Before:** Migrations ran on every application startup, even when no new migrations existed.

**After:** Migrations only run when needed:
- Checks current database revision
- Compares with head revision
- Only runs if they differ

**Benefits:**
- Faster startup times (no migration overhead when up-to-date)
- Reduced database load
- Better visibility into migration status

### 2. Migration Status Tracking

The `MigrationService` provides detailed status information:
- Current database revision
- Head revision (latest migration)
- Whether migration is needed
- Count of pending migrations

### 3. Migration Health Checks

Health check endpoint (`GET /admin/migrate/status`) provides:
- Migration status
- Health status
- Any issues found (connection problems, out-of-sync migrations)

### 4. Optimized Admin Endpoint

The `/admin/migrate` endpoint now:
- Checks if migration is needed before running (by default)
- Returns detailed migration status
- Can be forced to run with `check_first=false` query parameter

## Usage

### Automatic Migrations (Startup)

Migrations run automatically on application startup, but only if needed:

```python
# In main.py lifespan
status = migration_service.get_migration_status()
if status['needs_migration']:
    result = migration_service.run_migrations(check_first=True)
```

### Manual Migrations (Admin Endpoint)

```bash
# Check migration status
curl -X GET http://localhost:3000/admin/migrate/status \
  -H "X-API-Key: your-api-key"

# Run migrations (only if needed)
curl -X POST http://localhost:3000/admin/migrate \
  -H "X-API-Key: your-api-key"

# Force run migrations (skip check)
curl -X POST "http://localhost:3000/admin/migrate?check_first=false" \
  -H "X-API-Key: your-api-key"
```

## MigrationService API

### `get_current_revision() -> Optional[str]`
Get the current database revision.

### `get_head_revision() -> Optional[str]`
Get the head revision from migration scripts.

### `needs_migration() -> bool`
Check if database needs migration.

### `get_migration_status() -> Dict[str, Any]`
Get detailed migration status:
- `current_revision`: Current DB revision
- `head_revision`: Latest migration revision
- `needs_migration`: Whether migration is needed
- `pending_count`: Number of pending migrations

### `run_migrations(check_first: bool = True) -> Dict[str, Any]`
Run database migrations:
- `check_first=True`: Only run if needed (default)
- `check_first=False`: Force run migrations

Returns:
- `success`: Whether migration succeeded
- `message`: Status message
- `before`: Status before migration
- `after`: Status after migration

### `check_migration_health() -> Dict[str, Any]`
Check migration health:
- `healthy`: Whether migrations are healthy
- `current_revision`: Current DB revision
- `head_revision`: Latest migration revision
- `issues`: List of any issues found

## Performance Impact

**Before:**
- Every startup: ~500ms-2s (depending on migration count)
- Database connection overhead
- Unnecessary migration checks

**After:**
- Up-to-date database: ~10-50ms (just status check)
- Only runs migrations when needed
- Reduced database load

## Migration Best Practices

1. **Always check status first** - Use `get_migration_status()` before running migrations
2. **Monitor health** - Use `check_migration_health()` for monitoring
3. **Use admin endpoint** - For manual migrations, use `/admin/migrate` with `check_first=true`
4. **Force when needed** - Use `check_first=false` only when explicitly needed

## Future Improvements

Potential future optimizations:
- Migration locking (prevent concurrent migrations)
- Migration rollback support
- Migration performance metrics
- Migration dependency tracking
