"""
Admin endpoints for the Agaip API.

This module provides administrative endpoints for system management,
user administration, and advanced configuration.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agaip.api.dependencies import get_container_dependency, require_admin
from agaip.core.container import Container
from agaip.database.models.user import User
from agaip.services.agent_service import AgentService
from agaip.services.task_service import TaskService

router = APIRouter()


class SystemStatusResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    total_agents: int
    healthy_agents: int
    total_tasks: int
    active_tasks: int
    database_status: str


@router.get(
    "/admin/system/status",
    response_model=SystemStatusResponse,
    summary="Get system status",
)
async def get_system_status(
    admin_user: User = Depends(require_admin),
    container: Container = Depends(get_container_dependency),
) -> SystemStatusResponse:
    """Get comprehensive system status for admin dashboard."""

    agent_service = container.resolve(AgentService)
    task_service = container.resolve(TaskService)

    # Get agent statistics
    agent_stats = await agent_service.get_agent_statistics()

    # Get task statistics
    task_stats = await task_service.get_task_statistics()

    return SystemStatusResponse(
        status="healthy",
        version="3.0.0",
        environment="development",
        uptime_seconds=3600.0,
        total_agents=agent_stats.get("total_agents", 0),
        healthy_agents=agent_stats.get("healthy_agents", 0),
        total_tasks=task_stats.get("total_tasks", 0),
        active_tasks=task_stats.get("processing_tasks", 0),
        database_status="healthy",
    )


@router.post("/admin/system/cleanup", summary="Run system cleanup")
async def run_system_cleanup(
    admin_user: User = Depends(require_admin),
    container: Container = Depends(get_container_dependency),
) -> Dict[str, Any]:
    """Run system cleanup tasks."""

    task_service = container.resolve(TaskService)

    # Cleanup old tasks
    cleaned_tasks = await task_service.cleanup_old_tasks(days_old=30)

    return {"message": "System cleanup completed", "cleaned_tasks": cleaned_tasks}


@router.post("/admin/agents/{agent_id}/restart", summary="Restart an agent")
async def restart_agent(
    agent_id: str,
    admin_user: User = Depends(require_admin),
    container: Container = Depends(get_container_dependency),
) -> Dict[str, Any]:
    """Restart a specific agent."""

    agent_service = container.resolve(AgentService)

    success = await agent_service.restart_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Agent not found or cannot be restarted"
        )

    return {"message": f"Agent {agent_id} restarted successfully"}


@router.get("/admin/metrics", summary="Get system metrics")
async def get_system_metrics(
    admin_user: User = Depends(require_admin),
    container: Container = Depends(get_container_dependency),
) -> Dict[str, Any]:
    """Get detailed system metrics for monitoring."""

    agent_service = container.resolve(AgentService)
    task_service = container.resolve(TaskService)

    # Get comprehensive metrics
    agent_metrics = await agent_service.get_agent_statistics()
    task_metrics = await task_service.get_task_statistics()
    load_distribution = await agent_service.get_load_distribution()

    return {
        "agents": agent_metrics,
        "tasks": task_metrics,
        "load_distribution": load_distribution,
        "timestamp": "2024-01-01T00:00:00Z",
    }
