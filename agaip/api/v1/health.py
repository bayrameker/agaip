"""
Health check endpoints for the Agaip API.

This module provides endpoints for monitoring application health,
database connectivity, and system status.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from agaip.api.dependencies import get_database, get_settings_dependency
from agaip.config.settings import Settings
from agaip.database.connection import DatabaseManager

router = APIRouter()


@router.get("/health", summary="Basic health check")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "3.0.0",
    }


@router.get("/health/detailed", summary="Detailed health check")
async def detailed_health_check(
    db_manager: DatabaseManager = Depends(get_database),
    settings: Settings = Depends(get_settings_dependency),
) -> Dict[str, Any]:
    """Detailed health check with component status."""

    # Check database health
    db_health = await db_manager.health_check()

    # Overall health status
    overall_healthy = db_health.get("healthy", False)

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": settings.app_version,
        "environment": settings.environment,
        "components": {
            "database": db_health,
            "api": {"status": "healthy", "healthy": True},
        },
    }


@router.get("/ready", summary="Readiness probe")
async def readiness_check(
    db_manager: DatabaseManager = Depends(get_database),
) -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""

    # Check if database is ready
    if not db_manager.is_initialized:
        return {"status": "not_ready", "reason": "database_not_initialized"}

    db_health = await db_manager.health_check()
    if not db_health.get("healthy", False):
        return {"status": "not_ready", "reason": "database_unhealthy"}

    return {"status": "ready"}


@router.get("/live", summary="Liveness probe")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}
