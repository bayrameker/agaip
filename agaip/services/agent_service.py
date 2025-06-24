"""
Agent service for the Agaip framework.

This module provides business logic for agent management,
health monitoring, and performance tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from agaip.core.events import AgentStartedEvent, AgentStoppedEvent, publish
from agaip.core.exceptions import AgentError
from agaip.database.models.agent import Agent, AgentStatus, AgentType
from agaip.database.repositories.agent import AgentRepository


class AgentService:
    """Service for managing agents and their lifecycle."""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    async def initialize(self) -> None:
        """Initialize the agent service."""
        # Perform any initialization tasks
        pass

    async def register_agent_from_config(self, config: Dict[str, Any]) -> Agent:
        """Register an agent from configuration."""

        agent = await self.agent_repo.create_agent(
            name=config["name"],
            plugin_name=config["plugin"],
            agent_type=AgentType(config.get("type", "custom")),
            description=config.get("description"),
            plugin_config=config.get("config", {}),
            max_concurrent_tasks=config.get("max_concurrent_tasks", 1),
            timeout_seconds=config.get("timeout_seconds", 300),
        )

        return agent

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """Get an agent by ID."""
        return await self.agent_repo.get_by_id(agent_id)

    async def list_agents(
        self,
        agent_type: Optional[AgentType] = None,
        status: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[Agent]:
        """List agents with optional filtering."""

        filters = {}

        if agent_type:
            filters["agent_type"] = agent_type

        if status:
            filters["status"] = status

        if enabled_only:
            filters["enabled"] = True

        if filters:
            return await self.agent_repo.filter(**filters)
        else:
            return await self.agent_repo.get_all()

    async def get_available_agents(
        self, agent_type: Optional[AgentType] = None
    ) -> List[Agent]:
        """Get agents available for task assignment."""
        return await self.agent_repo.get_available_agents(agent_type)

    async def activate_agent(self, agent_id: UUID) -> bool:
        """Activate an agent."""
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return False

        await agent.activate()

        # Publish event
        await publish(AgentStartedEvent(agent_id=str(agent_id)))

        return True

    async def deactivate_agent(self, agent_id: UUID) -> bool:
        """Deactivate an agent."""
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return False

        await agent.deactivate()

        # Publish event
        await publish(AgentStoppedEvent(agent_id=str(agent_id)))

        return True

    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent by name or ID."""

        # Try to find by name first, then by ID
        agent = await self.agent_repo.get_by_field("name", agent_id)
        if not agent:
            try:
                agent = await self.agent_repo.get_by_id(UUID(agent_id))
            except ValueError:
                return False

        if not agent:
            return False

        # Deactivate then activate
        await agent.deactivate()
        await agent.activate()

        return True

    async def update_agent_heartbeat(self, agent_id: UUID) -> bool:
        """Update agent heartbeat."""
        return await self.agent_repo.update_agent_heartbeat(agent_id)

    async def record_agent_error(self, agent_id: UUID, error_message: str) -> bool:
        """Record an error for an agent."""
        return await self.agent_repo.record_agent_error(agent_id, error_message)

    async def get_agent_status(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed status of an agent."""
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return None

        return {
            "id": str(agent.id),
            "name": agent.name,
            "status": agent.status,
            "is_healthy": agent.is_healthy,
            "last_heartbeat": agent.last_heartbeat.isoformat()
            if agent.last_heartbeat
            else None,
            "total_tasks": agent.total_tasks_processed,
            "success_rate": agent.success_rate,
            "last_error": agent.last_error,
            "enabled": agent.enabled,
        }

    async def get_agent_statistics(self) -> Dict[str, Any]:
        """Get overall agent performance statistics."""
        return await self.agent_repo.get_agent_performance_metrics()

    async def get_load_distribution(self) -> Dict[str, Any]:
        """Get current load distribution across agents."""
        return await self.agent_repo.get_agent_load_distribution()

    async def health_check_all_agents(self) -> Dict[str, Any]:
        """Perform health check on all agents."""

        unhealthy_agents = await self.agent_repo.get_unhealthy_agents()

        restarted_count = 0
        for agent in unhealthy_agents:
            if agent.auto_restart:
                await agent.set_error("Health check failed - auto restarting")
                await agent.activate()  # Try to reactivate
                restarted_count += 1

        return {
            "unhealthy_agents": len(unhealthy_agents),
            "restarted_agents": restarted_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_top_performing_agents(self, limit: int = 10) -> List[Agent]:
        """Get top performing agents."""
        return await self.agent_repo.get_top_performing_agents(limit)

    async def reset_agent_metrics(self, agent_id: UUID) -> bool:
        """Reset performance metrics for an agent."""
        return await self.agent_repo.reset_agent_metrics(agent_id)

    async def cleanup_inactive_agents(self, days_inactive: int = 30) -> int:
        """Clean up agents that have been inactive for a long time."""
        return await self.agent_repo.cleanup_inactive_agents(days_inactive)
