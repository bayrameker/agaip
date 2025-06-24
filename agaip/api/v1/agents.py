"""
Agent management endpoints for the Agaip API.

This module provides endpoints for managing agents,
monitoring their status, and viewing performance metrics.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from agaip.api.dependencies import get_current_user, get_container_dependency
from agaip.database.models.user import User
from agaip.database.models.agent import AgentType
from agaip.services.agent_service import AgentService
from agaip.core.container import Container

router = APIRouter()


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    agent_type: str
    plugin_name: str
    status: str
    enabled: bool
    total_tasks_processed: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float
    is_healthy: bool
    last_heartbeat: Optional[str]


@router.get("/agents", response_model=List[AgentResponse], summary="List agents")
async def list_agents(
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by agent status"),
    enabled_only: bool = Query(True, description="Show only enabled agents"),
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> List[AgentResponse]:
    """List all agents with optional filtering."""
    
    agent_service = container.resolve(AgentService)
    
    agents = await agent_service.list_agents(
        agent_type=agent_type,
        status=status,
        enabled_only=enabled_only
    )
    
    return [
        AgentResponse(
            id=str(agent.id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            plugin_name=agent.plugin_name,
            status=agent.status,
            enabled=agent.enabled,
            total_tasks_processed=agent.total_tasks_processed,
            successful_tasks=agent.successful_tasks,
            failed_tasks=agent.failed_tasks,
            success_rate=agent.success_rate,
            is_healthy=agent.is_healthy,
            last_heartbeat=agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
        )
        for agent in agents
    ]


@router.get("/agents/{agent_id}", response_model=AgentResponse, summary="Get agent details")
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> AgentResponse:
    """Get detailed information about a specific agent."""
    
    agent_service = container.resolve(AgentService)
    
    agent = await agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        agent_type=agent.agent_type,
        plugin_name=agent.plugin_name,
        status=agent.status,
        enabled=agent.enabled,
        total_tasks_processed=agent.total_tasks_processed,
        successful_tasks=agent.successful_tasks,
        failed_tasks=agent.failed_tasks,
        success_rate=agent.success_rate,
        is_healthy=agent.is_healthy,
        last_heartbeat=agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
    )


@router.get("/agents/{agent_id}/status", summary="Get agent status")
async def get_agent_status(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> Dict[str, Any]:
    """Get current status of an agent."""
    
    agent_service = container.resolve(AgentService)
    
    status = await agent_service.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return status


@router.get("/agents/statistics", summary="Get agent statistics")
async def get_agent_statistics(
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> Dict[str, Any]:
    """Get overall agent performance statistics."""
    
    agent_service = container.resolve(AgentService)
    
    stats = await agent_service.get_agent_statistics()
    
    return stats


@router.get("/agents/load-distribution", summary="Get agent load distribution")
async def get_agent_load_distribution(
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> Dict[str, Any]:
    """Get current load distribution across agents."""
    
    agent_service = container.resolve(AgentService)
    
    load_data = await agent_service.get_load_distribution()
    
    return load_data
