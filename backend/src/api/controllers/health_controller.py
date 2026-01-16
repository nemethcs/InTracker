"""Health check and monitoring controller."""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.base import get_db, engine
from src.services.cache_service import get_redis_client
from src.config import settings
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Comprehensive health check endpoint.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - Application status
    
    Returns:
        Health status with detailed information
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "environment": settings.NODE_ENV,
        "checks": {
            "database": {"status": "unknown", "message": ""},
            "redis": {"status": "unknown", "message": ""},
        },
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful",
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "message": "Redis not configured (graceful degradation enabled)",
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }
        # Redis failure doesn't make the app unhealthy (graceful degradation)
    
    # Determine overall status
    if health_status["checks"]["database"]["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )
    
    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """Readiness check endpoint for Kubernetes/Docker health probes.
    
    Returns 200 if the application is ready to accept traffic.
    Returns 503 if the application is not ready.
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "message": f"Database connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Liveness check endpoint for Kubernetes/Docker health probes.
    
    Returns 200 if the application is alive (process is running).
    This is a lightweight check that doesn't require database access.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get application metrics for monitoring.
    
    Returns:
        Application metrics including:
        - Database connection pool stats
        - Redis connection status
        - Application uptime (if available)
    """
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {},
        "redis": {},
    }
    
    # Database metrics
    try:
        pool = engine.pool
        metrics["database"] = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    except Exception as e:
        metrics["database"] = {
            "error": str(e),
        }
    
    # Redis metrics
    try:
        redis_client = get_redis_client()
        if redis_client:
            info = redis_client.info()
            metrics["redis"] = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        else:
            metrics["redis"] = {
                "status": "not_configured",
            }
    except Exception as e:
        metrics["redis"] = {
            "error": str(e),
        }
    
    return metrics
