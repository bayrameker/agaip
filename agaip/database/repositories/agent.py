"""
Agent repository for the Agaip framework.

This module provides specialized data access methods for Agent model
including health monitoring, performance metrics, and status management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from agaip.database.models.agent import Agent, AgentStatus, AgentType

from .base import BaseRepository


class AgentRepository(BaseRepository):
    """Repository for Agent model with specialized operations."""

    def __init__(self):
        super().__init__(Agent)

    async def create_agent(
        self,
        name: str,
        plugin_name: str,
        agent_type: AgentType = AgentType.CUSTOM,
        description: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None,
        max_concurrent_tasks: int = 1,
        timeout_seconds: int = 300,
        **kwargs,
    ) -> Agent:
        """Create a new agent with proper initialization."""
        agent_data = {
            "name": name,
            "plugin_name": plugin_name,
            "agent_type": agent_type,
            "description": description,
            "plugin_config": plugin_config or {},
            "max_concurrent_tasks": max_concurrent_tasks,
            "timeout_seconds": timeout_seconds,
            "status": AgentStatus.INACTIVE,
            **kwargs,
        }

        return await self.create(**agent_data)

    async def get_active_agents(self) -> List[Agent]:
        """Get all active agents."""
        return await self.model_class.filter(
            status=AgentStatus.ACTIVE, enabled=True
        ).order_by("-priority", "name")

    async def get_available_agents(
        self, agent_type: Optional[AgentType] = None
    ) -> List[Agent]:
        """Get agents available for task assignment."""
        queryset = self.model_class.filter(
            status__in=[AgentStatus.ACTIVE, AgentStatus.BUSY], enabled=True
        )

        if agent_type:
            queryset = queryset.filter(agent_type=agent_type)

        return await queryset.order_by("-priority", "name")

    async def get_unhealthy_agents(
        self, heartbeat_timeout_minutes: int = 5
    ) -> List[Agent]:
        """Get agents that haven't sent heartbeat recently."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=heartbeat_timeout_minutes)

        return await self.model_class.filter(
            status__in=[AgentStatus.ACTIVE, AgentStatus.BUSY],
            last_heartbeat__lt=cutoff_time,
        )

    async def get_agents_by_plugin(self, plugin_name: str) -> List[Agent]:
        """Get all agents using a specific plugin."""
        return await self.model_class.filter(plugin_name=plugin_name)

    async def get_agents_with_tag(self, tag: str) -> List[Agent]:
        """Get agents that have a specific tag."""
        return await self.model_class.filter(tags__contains=[tag])

    async def update_agent_heartbeat(self, agent_id: UUID) -> bool:
        """Update agent heartbeat timestamp."""
        agent = await self.get_by_id(agent_id)
        if agent:
            await agent.heartbeat()
            return True
        return False

    async def set_agent_status(self, agent_id: UUID, status: AgentStatus) -> bool:
        """Set agent status."""
        agent = await self.get_by_id(agent_id)
        if agent:
            agent.status = status
            await agent.save(update_fields=["status"])
            return True
        return False

    async def record_agent_error(self, agent_id: UUID, error_message: str) -> bool:
        """Record an error for an agent."""
        agent = await self.get_by_id(agent_id)
        if agent:
            await agent.set_error(error_message)
            return True
        return False

    async def get_agent_performance_metrics(
        self,
        agent_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for agents."""
        queryset = self.model_class.all()

        if agent_id:
            queryset = queryset.filter(id=agent_id)

        agents = await queryset

        if not agents:
            return {}

        total_tasks = sum(agent.total_tasks_processed for agent in agents)
        successful_tasks = sum(agent.successful_tasks for agent in agents)
        failed_tasks = sum(agent.failed_tasks for agent in agents)

        # Calculate overall success rate
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate average processing time
        processing_times = [
            agent.average_processing_time
            for agent in agents
            if agent.average_processing_time is not None
        ]
        avg_processing_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0
        )

        # Agent health status
        healthy_agents = sum(1 for agent in agents if agent.is_healthy)
        total_agents = len(agents)

        metrics = {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": total_agents - healthy_agents,
            "total_tasks_processed": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "overall_success_rate": round(success_rate, 2),
            "average_processing_time": round(avg_processing_time, 2),
        }

        # If single agent, include detailed metrics
        if agent_id and agents:
            agent = agents[0]
            metrics.update(
                {
                    "agent_name": agent.name,
                    "agent_status": agent.status,
                    "agent_type": agent.agent_type,
                    "last_heartbeat": agent.last_heartbeat.isoformat()
                    if agent.last_heartbeat
                    else None,
                    "error_count": agent.error_count,
                    "last_error": agent.last_error,
                }
            )

        return metrics

    async def get_top_performing_agents(self, limit: int = 10) -> List[Agent]:
        """Get top performing agents by success rate and task count."""
        agents = (
            await self.model_class.filter(total_tasks_processed__gt=0)
            .order_by("-successful_tasks", "-total_tasks_processed")
            .limit(limit)
        )

        return agents

    async def cleanup_inactive_agents(self, days_inactive: int = 30) -> int:
        """Clean up agents that have been inactive for a long time."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)

        inactive_agents = await self.model_class.filter(
            status=AgentStatus.INACTIVE, last_heartbeat__lt=cutoff_date
        )

        count = len(inactive_agents)

        for agent in inactive_agents:
            await agent.soft_delete()

        return count

    async def reset_agent_metrics(self, agent_id: UUID) -> bool:
        """Reset performance metrics for an agent."""
        agent = await self.get_by_id(agent_id)
        if agent:
            await agent.reset_metrics()
            return True
        return False

    async def bulk_update_agent_status(
        self, agent_ids: List[UUID], status: AgentStatus
    ) -> int:
        """Bulk update status for multiple agents."""
        agents = await self.model_class.filter(id__in=agent_ids)

        for agent in agents:
            agent.status = status

        await self.model_class.bulk_update(agents, ["status"])
        return len(agents)

    async def get_agent_load_distribution(self) -> Dict[str, Any]:
        """Get current load distribution across agents."""
        from agaip.database.models.task import Task, TaskStatus

        # Get active agents
        active_agents = await self.get_active_agents()

        load_data = []
        for agent in active_agents:
            # Count current processing tasks
            processing_tasks = await Task.filter(
                agent_id=agent.name, status=TaskStatus.PROCESSING
            ).count()

            # Count queued tasks
            queued_tasks = await Task.filter(
                agent_id=agent.name, status=TaskStatus.QUEUED
            ).count()

            load_percentage = (
                (processing_tasks / agent.max_concurrent_tasks * 100)
                if agent.max_concurrent_tasks > 0
                else 0
            )

            load_data.append(
                {
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "processing_tasks": processing_tasks,
                    "queued_tasks": queued_tasks,
                    "max_concurrent_tasks": agent.max_concurrent_tasks,
                    "load_percentage": round(load_percentage, 2),
                    "status": agent.status,
                }
            )

        return {
            "agents": load_data,
            "total_agents": len(active_agents),
            "average_load": round(
                sum(agent["load_percentage"] for agent in load_data) / len(load_data), 2
            )
            if load_data
            else 0,
        }
