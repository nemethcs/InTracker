# Performance Profiling and Optimization Guide

## Overview

This document outlines the performance profiling and optimization strategy for the InTracker backend.

## Performance Monitoring

### Middleware

The `PerformanceMiddleware` automatically monitors all API requests and logs:
- **Slow requests** (>1 second): Logged as warnings
- **Very slow requests** (>3 seconds): Logged as errors
- Request duration, method, path, and status code

### Metrics Endpoint

The `/health/metrics` endpoint provides:
- Database connection pool statistics
- Redis connection status and memory usage
- Cache hit/miss statistics

## Profiling Tools

### 1. cProfile (Built-in Python Profiler)

Use cProfile to identify slow functions:

```bash
# Profile a specific endpoint
python -m cProfile -o profile.stats -m uvicorn src.main:app --reload

# Analyze results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### 2. py-spy (Sampling Profiler)

py-spy can profile running processes without code changes:

```bash
# Install
pip install py-spy

# Profile running backend
py-spy record -o profile.svg --pid <backend_pid> --duration 60

# View in browser
open profile.svg
```

### 3. Database Query Profiling

Enable PostgreSQL slow query logging:

```sql
-- Enable slow query log (queries > 1 second)
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 20;
```

### 4. Redis Performance

Monitor Redis performance:

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Get stats
INFO stats
INFO memory
SLOWLOG GET 10
```

## Common Performance Issues

### 1. N+1 Query Problems

**Symptom**: Multiple database queries for related data.

**Example**:
```python
# BAD: N+1 queries
for element in elements:
    todos = db.query(Todo).filter(Todo.element_id == element.id).all()

# GOOD: Bulk query
element_ids = [e.id for e in elements]
todos = db.query(Todo).filter(Todo.element_id.in_(element_ids)).all()
todos_dict = {todo.element_id: todo for todo in todos}
```

**Solution**: Use bulk queries with `in_()` or eager loading with `joinedload()`.

### 2. Missing Database Indexes

**Symptom**: Slow queries on filtered columns.

**Check for missing indexes**:
```sql
-- Find tables without indexes on foreign keys
SELECT
    t.tablename,
    a.attname AS column_name
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
JOIN pg_attribute a ON a.attrelid = c.oid
WHERE t.schemaname = 'public'
  AND a.attnum > 0
  AND NOT a.attisdropped
  AND a.attname LIKE '%_id'
  AND NOT EXISTS (
    SELECT 1 FROM pg_indexes i
    WHERE i.tablename = t.tablename
    AND i.indexdef LIKE '%' || a.attname || '%'
  );
```

**Solution**: Add indexes on frequently queried columns:
```python
# In Alembic migration
op.create_index('ix_todos_element_id', 'todos', ['element_id'])
op.create_index('ix_todos_status', 'todos', ['status'])
```

### 3. Inefficient Caching

**Symptom**: High cache miss rate or unnecessary cache invalidation.

**Check cache performance**:
```python
# Monitor cache hit/miss ratio
redis_client.info()['keyspace_hits'] / redis_client.info()['keyspace_misses']
```

**Solution**: 
- Review cache TTLs (see `CacheTTL` in `cache_service.py`)
- Use appropriate cache keys
- Implement cache warming for frequently accessed data

### 4. Large Response Payloads

**Symptom**: Slow API responses with large JSON payloads.

**Solution**:
- Implement pagination (already done for list endpoints)
- Use `select_related` to limit joined data
- Consider response compression (gzip)
- Use field selection if needed

### 5. Connection Pool Exhaustion

**Symptom**: Database connection timeouts.

**Check pool status**:
```bash
curl http://localhost:3000/health/metrics
```

**Solution**: Adjust pool size in `database/base.py`:
```python
pool_config = {
    "pool_size": 20,  # Increase if needed
    "max_overflow": 10,
    "pool_recycle": 3600,
}
```

## Optimization Checklist

### Database
- [x] N+1 query fixes (element_service.py)
- [x] Database indexes on foreign keys
- [x] Connection pool configuration
- [ ] Query result caching for expensive queries
- [ ] Database query result pagination

### Caching
- [x] Redis caching for project lists
- [x] Redis caching for feature lists
- [x] Standardized cache TTLs
- [x] Cache invalidation on updates
- [ ] Cache warming for frequently accessed data

### API Performance
- [x] Performance middleware for monitoring
- [x] ORJSON for faster JSON serialization
- [x] Pagination on list endpoints
- [ ] Response compression (gzip)
- [ ] Request rate limiting

### Code Optimization
- [x] Bulk queries instead of loops
- [x] Eager loading for related data
- [ ] Async/await optimization where applicable
- [ ] Lazy loading for large datasets

## Performance Testing

### Load Testing with Locust

```bash
# Install Locust
pip install locust

# Create locustfile.py
# Run load test
locust -f locustfile.py --host=http://localhost:3000
```

### Benchmarking

```bash
# Benchmark specific endpoint
ab -n 1000 -c 10 http://localhost:3000/api/projects

# With authentication
ab -n 1000 -c 10 -H "Authorization: Bearer <token>" http://localhost:3000/api/projects
```

## Monitoring in Production

### Recommended Metrics

1. **Request Duration** (p50, p95, p99)
2. **Request Rate** (requests per second)
3. **Error Rate** (4xx, 5xx responses)
4. **Database Query Time** (average, max)
5. **Cache Hit Rate** (Redis)
6. **Connection Pool Usage** (database)

### Tools

- **Application Insights** (Azure)
- **Prometheus + Grafana** (self-hosted)
- **Datadog** (SaaS)
- **New Relic** (SaaS)

## Best Practices

1. **Always profile before optimizing** - Don't guess what's slow
2. **Measure after changes** - Verify improvements
3. **Use bulk operations** - Avoid loops with database queries
4. **Cache expensive operations** - But invalidate properly
5. **Index frequently queried columns** - Especially foreign keys
6. **Monitor in production** - Real-world performance matters
7. **Set performance budgets** - Define acceptable response times
8. **Document slow endpoints** - If they can't be optimized, document why

## Performance Budget

Target response times:
- **Simple queries**: < 100ms
- **Complex queries**: < 500ms
- **List endpoints**: < 1s (with pagination)
- **Bulk operations**: < 2s

If an endpoint consistently exceeds these thresholds, it should be optimized or documented with justification.
