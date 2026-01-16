# Async/Await Optimization Guide

## Overview

This document outlines async/await optimization opportunities in the InTracker backend. Currently, most service methods are synchronous, while FastAPI endpoints are async. This creates a performance bottleneck where async endpoints block the event loop when calling synchronous service methods.

## Current State

### Async Endpoints
- ✅ All FastAPI endpoints are `async def`
- ✅ SignalR WebSocket handlers are async
- ✅ MCP server handlers are async

### Synchronous Services
- ❌ Most service methods are `def` (synchronous)
- ❌ Database operations use SQLAlchemy synchronous sessions
- ❌ Redis cache operations are synchronous
- ❌ GitHub API calls are synchronous (PyGithub library)

## Optimization Opportunities

### 1. Database Operations (High Impact, High Effort)

**Current**: SQLAlchemy synchronous sessions
```python
def get_project_by_id(db: Session, project_id: UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()
```

**Optimized**: SQLAlchemy async sessions
```python
async def get_project_by_id(db: AsyncSession, project_id: UUID) -> Optional[Project]:
    result = await db.execute(select(Project).filter(Project.id == project_id))
    return result.scalar_one_or_none()
```

**Impact**: High - Database operations are the most common I/O operations
**Effort**: High - Requires migrating all service methods and database setup
**Recommendation**: Consider for future major refactoring

### 2. Redis Cache Operations (Medium Impact, Low Effort)

**Current**: Synchronous Redis client
```python
def get_cache(key: str) -> Optional[Any]:
    client = get_redis_client()
    value = client.get(key)
    return json.loads(value) if value else None
```

**Optimized**: Async Redis client (redis.asyncio)
```python
async def get_cache(key: str) -> Optional[Any]:
    client = await get_async_redis_client()
    value = await client.get(key)
    return json.loads(value) if value else None
```

**Impact**: Medium - Cache operations are frequent but fast
**Effort**: Low - Minimal changes to cache service
**Recommendation**: ✅ Implement this optimization

### 3. GitHub API Calls (Medium Impact, Medium Effort)

**Current**: Synchronous PyGithub library
```python
def get_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
    repository = self.client.get_repo(f"{owner}/{repo}")
    return {...}
```

**Optimized**: Async HTTP client with GitHub API
```python
async def get_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
        return response.json()
```

**Impact**: Medium - GitHub API calls are I/O bound
**Effort**: Medium - Requires replacing PyGithub with direct API calls
**Recommendation**: Consider for future optimization

### 4. Email Sending (Low Impact, Low Effort)

**Current**: Synchronous Azure Communication Services
```python
def send_email(...) -> bool:
    email_client = EmailClient.from_connection_string(...)
    message = EmailMessage(...)
    email_client.send(message)
```

**Optimized**: Async email client
```python
async def send_email(...) -> bool:
    email_client = EmailClient.from_connection_string(...)
    message = EmailMessage(...)
    await email_client.send(message)
```

**Impact**: Low - Email sending is infrequent
**Effort**: Low - Azure SDK supports async
**Recommendation**: ✅ Implement this optimization

### 5. Background Tasks (Low Impact, Low Effort)

**Current**: Threading for async operations
```python
def run_broadcast():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(broadcast_session_start(...))
    loop.close()

thread = threading.Thread(target=run_broadcast, daemon=True)
thread.start()
```

**Optimized**: FastAPI BackgroundTasks
```python
background_tasks.add_task(broadcast_session_start, ...)
```

**Impact**: Low - Already using BackgroundTasks in most places
**Effort**: Low - Remove threading workarounds
**Recommendation**: ✅ Clean up existing code

## Implementation Priority

### Phase 1: Quick Wins (Low Effort, Medium Impact)
1. ✅ **Redis Cache Operations** - Switch to `redis.asyncio`
2. ✅ **Email Sending** - Use async Azure SDK
3. ✅ **Background Tasks** - Remove threading workarounds

### Phase 2: Medium Effort (Medium Impact)
4. **GitHub API Calls** - Replace PyGithub with async HTTP client
5. **File I/O Operations** - Use `aiofiles` for async file operations

### Phase 3: Major Refactoring (High Impact, High Effort)
6. **Database Operations** - Migrate to SQLAlchemy async sessions
   - Requires changing all service methods
   - Requires async database connection pool
   - Requires async dependency injection

## Current Limitations

### SQLAlchemy Synchronous Sessions
- FastAPI endpoints are async, but service methods are sync
- When an async endpoint calls a sync service method, it blocks the event loop
- This prevents true concurrency for database operations

### Workaround: Thread Pool
For now, we can use `asyncio.to_thread()` to run sync operations in a thread pool:

```python
@router.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    # Run sync service method in thread pool
    projects = await asyncio.to_thread(
        project_service.get_user_projects,
        db=db,
        user_id=user_id
    )
    return projects
```

**Pros**: 
- Minimal code changes
- Prevents blocking the event loop
- Allows concurrent request handling

**Cons**:
- Adds thread overhead
- Not as efficient as true async
- Still limited by GIL for CPU-bound operations

## Recommendations

### Immediate Actions
1. ✅ Document async/await optimization opportunities
2. ✅ Identify high-impact, low-effort optimizations
3. ✅ Plan migration strategy for database operations

### Short-term (1-2 months)
1. Migrate Redis cache to async (`redis.asyncio`)
2. Migrate email service to async
3. Remove threading workarounds for SignalR broadcasts

### Long-term (3-6 months)
1. Evaluate SQLAlchemy async migration
2. Consider replacing PyGithub with async HTTP client
3. Implement comprehensive async/await throughout codebase

## Testing Strategy

When implementing async optimizations:
1. **Performance Testing**: Measure request latency before/after
2. **Concurrency Testing**: Test with multiple concurrent requests
3. **Load Testing**: Use tools like Locust to test under load
4. **Monitoring**: Track event loop blocking with `asyncio` debug mode

## Migration Checklist

- [ ] Audit all service methods for async opportunities
- [ ] Identify blocking I/O operations
- [ ] Prioritize optimizations by impact/effort
- [ ] Implement async Redis cache
- [ ] Implement async email service
- [ ] Remove threading workarounds
- [ ] Test performance improvements
- [ ] Document async patterns for team
- [ ] Plan SQLAlchemy async migration (future)

## References

- [FastAPI Async Best Practices](https://fastapi.tiangolo.com/async/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Redis Async Python Client](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [Python Async/Await Guide](https://docs.python.org/3/library/asyncio.html)
