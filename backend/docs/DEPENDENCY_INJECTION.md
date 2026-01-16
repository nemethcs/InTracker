# Dependency Injection Pattern in InTracker

This document describes the current dependency injection (DI) pattern used in the InTracker backend and provides guidance for future improvements.

## Current Implementation

### FastAPI Dependency Injection

FastAPI uses Python's `Depends()` for dependency injection. The current implementation follows these patterns:

#### 1. Database Session Injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database.base import get_db

@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    # Use db session
    pass
```

#### 2. Authentication Dependency

```python
from src.api.middleware.auth import get_current_user

@router.post("/items")
async def create_item(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = UUID(current_user["user_id"])
    # Use user_id and db
    pass
```

#### 3. Service Usage

Currently, services are used in two ways:

**Pattern A: Global Instance (Most Common)**
```python
from src.services.project_service import project_service

@router.post("/projects")
async def create_project(
    db: Session = Depends(get_db),
):
    project = project_service.create_project(db=db, ...)
    return project
```

**Pattern B: Class Methods (Some Services)**
```python
from src.services.team_service import TeamService

@router.post("/teams")
async def create_team(
    db: Session = Depends(get_db),
):
    team = TeamService.create_team(db=db, ...)
    return team
```

## Recommended Improvements

### 1. Centralized Service Dependencies

A `backend/src/api/dependencies.py` file has been created to centralize service dependencies:

```python
from src.api.dependencies import (
    ProjectServiceDep,
    FeatureServiceDep,
    DatabaseDep,
    CurrentUserDep,
)

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
):
    project = project_service.create_project(db=db, ...)
    return project
```

**Benefits:**
- Explicit service dependencies in function signatures
- Easier testing (can override dependencies)
- Better IDE support and type checking
- Consistent pattern across all controllers

### 2. Service Instance Consistency

**Current State:**
- Some services use global instances: `project_service`, `element_service`, `feature_service`
- Some services use class methods: `TeamService.get_team_by_id()`, `IdeaService()`

**Recommendation:**
- Standardize on global instances for stateless services
- Use dependency injection for services that need configuration or state

### 3. Testing with Dependency Override

FastAPI allows dependency override for testing:

```python
from fastapi.testclient import TestClient
from src.api.dependencies import get_project_service

def get_test_project_service():
    # Return mock service
    return MockProjectService()

app.dependency_overrides[get_project_service] = get_test_project_service
```

## Migration Strategy

### Phase 1: New Code (Current)
- Use centralized dependencies from `dependencies.py` for new endpoints
- Gradually migrate existing endpoints

### Phase 2: Refactoring (Future)
- Update all controllers to use `ProjectServiceDep`, `FeatureServiceDep`, etc.
- Remove direct service imports from controllers
- Add dependency override support for testing

### Phase 3: Advanced DI (Optional)
- Consider using a DI container library (e.g., `dependency-injector`)
- Implement service factories for complex dependencies
- Add lifecycle management for services

## Best Practices

1. **Always inject dependencies** - Don't import services directly in controllers
2. **Use type hints** - Leverage `Annotated` types for better IDE support
3. **Keep services stateless** - Services should not maintain state between requests
4. **Test with mocks** - Use dependency override for unit testing
5. **Document dependencies** - Clear function signatures show what's needed

## Example: Migrated Controller

**Before:**
```python
from src.services.project_service import project_service

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = project_service.create_project(db=db, ...)
    return project
```

**After:**
```python
from src.api.dependencies import (
    ProjectServiceDep,
    DatabaseDep,
    CurrentUserDep,
)

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
):
    project = project_service.create_project(db=db, ...)
    return project
```

## Benefits of Improved DI

1. **Testability** - Easy to mock services in tests
2. **Maintainability** - Clear dependencies, easier to refactor
3. **Type Safety** - Better IDE support and type checking
4. **Consistency** - Uniform pattern across all controllers
5. **Flexibility** - Easy to swap implementations (e.g., for testing)
