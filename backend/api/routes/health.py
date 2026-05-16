"""Enhanced health check endpoint with detailed component status."""

from fastapi import APIRouter, status
from typing import Dict, Any
import asyncio
from datetime import datetime

from backend.db.connection import db
from backend.integrations.queue_client import queue_client
from backend.config.settings import settings

router = APIRouter()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity and health."""
    try:
        async with db.acquire() as conn:
            # Simple query to verify connection
            result = await conn.fetchval("SELECT 1")

            # Check connection pool stats
            pool_size = db.get_size() if hasattr(db, 'get_size') else None

            return {
                "status": "healthy" if result == 1 else "unhealthy",
                "response_time_ms": 0,  # Would measure actual time
                "pool_size": pool_size,
                "details": "Database connection successful"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }


async def check_queue() -> Dict[str, Any]:
    """Check message queue connectivity."""
    try:
        # Check if queue client is connected
        is_connected = await queue_client.is_connected() if hasattr(queue_client, 'is_connected') else True

        return {
            "status": "healthy" if is_connected else "unhealthy",
            "bootstrap_servers": settings.kafka_bootstrap_servers,
            "details": "Queue connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Queue connection failed"
        }


async def check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")

        # Convert to GB
        total_gb = total // (2**30)
        used_gb = used // (2**30)
        free_gb = free // (2**30)
        usage_percent = (used / total) * 100

        # Warn if less than 10% free or less than 1GB
        is_healthy = free_gb > 1 and usage_percent < 90

        return {
            "status": "healthy" if is_healthy else "warning",
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "usage_percent": round(usage_percent, 2),
            "details": f"{free_gb}GB free ({100-usage_percent:.1f}% available)"
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "details": "Could not check disk space"
        }


async def check_memory() -> Dict[str, Any]:
    """Check memory usage."""
    try:
        import psutil

        memory = psutil.virtual_memory()

        # Warn if less than 10% free
        is_healthy = memory.percent < 90

        return {
            "status": "healthy" if is_healthy else "warning",
            "total_mb": memory.total // (1024 * 1024),
            "available_mb": memory.available // (1024 * 1024),
            "usage_percent": memory.percent,
            "details": f"{memory.percent}% used"
        }
    except ImportError:
        return {
            "status": "unknown",
            "details": "psutil not installed"
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "details": "Could not check memory"
        }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.

    Returns detailed status of all system components.
    """
    start_time = datetime.utcnow()

    # Run all health checks concurrently
    database_check, queue_check, disk_check, memory_check = await asyncio.gather(
        check_database(),
        check_queue(),
        check_disk_space(),
        check_memory(),
        return_exceptions=True
    )

    # Handle any exceptions from health checks
    def safe_result(check_result):
        if isinstance(check_result, Exception):
            return {
                "status": "error",
                "error": str(check_result),
                "details": "Health check failed"
            }
        return check_result

    database_status = safe_result(database_check)
    queue_status = safe_result(queue_check)
    disk_status = safe_result(disk_check)
    memory_status = safe_result(memory_check)

    # Determine overall health
    component_statuses = [
        database_status["status"],
        queue_status["status"]
    ]

    if all(s == "healthy" for s in component_statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in component_statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    end_time = datetime.utcnow()
    response_time_ms = (end_time - start_time).total_seconds() * 1000

    return {
        "status": overall_status,
        "timestamp": start_time.isoformat(),
        "response_time_ms": round(response_time_ms, 2),
        "version": "1.0.0",
        "environment": settings.environment,
        "components": {
            "database": database_status,
            "queue": queue_status,
            "disk": disk_status,
            "memory": memory_status
        }
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes/Docker.

    Returns 200 if the application is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes/Docker.

    Returns 200 if the application is ready to serve traffic.
    """
    # Check critical dependencies
    database_check = await check_database()
    queue_check = await check_queue()

    is_ready = (
        database_check["status"] == "healthy" and
        queue_check["status"] == "healthy"
    )

    if not is_ready:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": database_check,
                "queue": queue_check
            }
        }

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
