# API Versioning Strategy

## Overview

The InTracker API uses URL path-based versioning to manage API changes while maintaining backward compatibility.

## Versioning Strategy

### URL Path Versioning

All versioned endpoints are prefixed with `/v{version}/`:

- **v1 endpoints**: `/v1/{endpoint}`
  - Example: `/v1/projects`, `/v1/auth/register`
  
- **Legacy endpoints**: `/{endpoint}` (deprecated)
  - Example: `/projects`, `/auth/register`
  - These will be removed in a future version

### Version Format

```
/api/v{version}/{endpoint}
```

Examples:
- `/v1/projects` - Projects endpoint in v1
- `/v1/auth/register` - Auth register endpoint in v1
- `/v1/teams` - Teams endpoint in v1

## Current Versions

### v1 (Current)

- **Status**: Stable
- **Default**: Yes
- **Latest**: Yes
- **Base URL**: `/v1`

All current endpoints are available under `/v1/` prefix.

## Version Detection

### URL Path (Primary)

The version is determined by the URL path:

```bash
# v1 endpoint
GET /v1/projects

# Legacy endpoint (deprecated)
GET /projects
```

### Header (Optional)

Clients can also specify version using `X-API-Version` header:

```bash
GET /projects
X-API-Version: v1
```

**Note**: Header versioning is optional and primarily for documentation. URL path versioning is the primary method.

## Migration Guide

### For API Clients

**Before (Legacy):**
```bash
GET /projects
POST /auth/register
```

**After (v1):**
```bash
GET /v1/projects
POST /v1/auth/register
```

### For Frontend

Update all API calls to use `/v1/` prefix:

```typescript
// Before
const response = await fetch('/api/projects');

// After
const response = await fetch('/api/v1/projects');
```

## Version Lifecycle

### Adding New Versions

When introducing breaking changes:

1. **Create new version router** (`src/api/routes/v2/__init__.py`)
2. **Update version enum** (`src/api/versioning.py`)
3. **Update default version** (after migration period)
4. **Deprecate old version** (with deprecation notice)
5. **Remove old version** (after deprecation period)

### Deprecation Process

1. **Announcement**: Document deprecation in API docs
2. **Deprecation Period**: Maintain old version for 6-12 months
3. **Removal**: Remove deprecated version after migration period

## Version Information Endpoints

### Get API Info

```bash
GET /api
```

Returns:
```json
{
  "message": "InTracker API",
  "version": "0.1.0",
  "api_versioning": {
    "default_version": "v1",
    "latest_version": "v1",
    "supported_versions": ["v1"],
    "versioning_strategy": "url_path",
    "version_format": "/api/v{version}/{endpoint}"
  }
}
```

### List API Versions

```bash
GET /api/versions
```

Returns:
```json
{
  "versions": [
    {
      "version": "v1",
      "is_default": true,
      "is_latest": true,
      "status": "stable"
    }
  ],
  "default_version": "v1",
  "latest_version": "v1"
}
```

## Best Practices

### For API Developers

1. **Always use versioned routes** for new endpoints
2. **Document breaking changes** in version release notes
3. **Maintain backward compatibility** when possible
4. **Use deprecation warnings** for old endpoints
5. **Test all versions** before deployment

### For API Clients

1. **Always use versioned endpoints** (`/v1/...`)
2. **Monitor deprecation notices** in API responses
3. **Plan migrations** before version removal
4. **Test new versions** in staging before production

## Breaking Changes Policy

### What Requires a New Version?

- **Removing endpoints**
- **Changing request/response schemas**
- **Changing authentication requirements**
- **Changing error response formats**
- **Removing required fields**

### What Doesn't Require a New Version?

- **Adding new endpoints**
- **Adding optional fields**
- **Adding new response fields**
- **Performance improvements**
- **Bug fixes**

## Implementation Details

### Version Router Structure

```
src/api/routes/
  v1/
    __init__.py  # v1 router with all controllers
  v2/
    __init__.py  # v2 router (future)
```

### Version Utilities

```python
from src.api.versioning import APIVersion, DEFAULT_API_VERSION

# Get default version
version = DEFAULT_API_VERSION  # APIVersion.V1

# Validate version
from src.api.versioning import validate_api_version
is_valid = validate_api_version("v1")  # True
```

## Future Versions

### v2 (Planned)

When v2 is introduced:
- New endpoints will be added to `/v2/`
- v1 will remain stable
- Migration guide will be provided
- Deprecation timeline will be announced

## Deprecation Timeline

### Legacy Endpoints (No Prefix)

- **Status**: Deprecated
- **Removal**: TBD (after v1 migration period)
- **Action**: Migrate to `/v1/` endpoints

## Examples

### Versioned Endpoints

```bash
# Authentication
POST /v1/auth/register
POST /v1/auth/login
GET  /v1/auth/me

# Projects
GET    /v1/projects
POST   /v1/projects
GET    /v1/projects/{id}
PUT    /v1/projects/{id}
DELETE /v1/projects/{id}

# Features
GET    /v1/features/project/{project_id}
POST   /v1/features
GET    /v1/features/{id}
PUT    /v1/features/{id}
DELETE /v1/features/{id}
```

### Legacy Endpoints (Deprecated)

```bash
# These will be removed in a future version
POST /auth/register
GET  /projects
POST /features
```

## Testing

### Test Versioned Endpoints

```bash
# Test v1 endpoint
curl http://localhost:3000/v1/projects

# Test legacy endpoint (should still work)
curl http://localhost:3000/projects
```

## Migration Checklist

- [ ] Update frontend to use `/v1/` prefix
- [ ] Update API documentation
- [ ] Update integration tests
- [ ] Monitor legacy endpoint usage
- [ ] Plan legacy endpoint removal
