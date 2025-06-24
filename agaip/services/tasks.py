"""
Celery tasks for the Agaip framework.

This module defines background tasks that can be executed
asynchronously using Celery workers.
"""

import asyncio
from typing import Any, Dict, Optional
from uuid import UUID

from agaip.core.celery import celery_app
from agaip.core.events import (
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
    publish,
)
from agaip.database.repositories.agent import AgentRepository
from agaip.database.repositories.task import TaskRepository


@celery_app.task(bind=True, name="agaip.process_task")
def process_task_sync(self, task_id: str, agent_id: str, payload: Dict[str, Any]):
    """
    Synchronous wrapper for async task processing.
    This is needed because Celery doesn't natively support async tasks.
    """
    return asyncio.run(process_task_async(self, task_id, agent_id, payload))


async def process_task_async(
    celery_task, task_id: str, agent_id: str, payload: Dict[str, Any]
):
    """Process a task asynchronously."""
    task_repo = TaskRepository()
    agent_repo = AgentRepository()

    try:
        # Get task and agent
        task = await task_repo.get_by_id(UUID(task_id))
        agent = await agent_repo.get_by_field("name", agent_id)

        if not task or not agent:
            raise Exception(f"Task {task_id} or Agent {agent_id} not found")

        # Start processing
        await task.start_processing()
        await publish(TaskStartedEvent(task_id=task_id, agent_id=agent_id))

        # Load and execute plugin
        from agaip.plugins.loader import load_plugin

        plugin_class = load_plugin(agent.plugin_name)
        plugin_instance = plugin_class()

        if hasattr(plugin_instance, "load_model"):
            await plugin_instance.load_model()

        # Execute task
        result = await plugin_instance.predict(payload)

        # Complete task
        await task.complete_successfully(result)
        await agent.record_task_completion(True, task.duration_seconds or 0)

        await publish(
            TaskCompletedEvent(
                task_id=task_id,
                agent_id=agent_id,
                result=result,
                duration=task.duration_seconds or 0,
            )
        )

        return result

    except Exception as e:
        # Handle failure
        if task:
            await task.fail_with_error(str(e), type(e).__name__)

        if agent:
            await agent.record_task_completion(False, 0)
            await agent.set_error(str(e))

        await publish(
            TaskFailedEvent(
                task_id=task_id,
                agent_id=agent_id,
                error=str(e),
                error_type=type(e).__name__,
            )
        )

        # Retry logic
        if celery_task.request.retries < celery_task.max_retries:
            raise celery_task.retry(countdown=60, exc=e)

        raise e


@celery_app.task(name="agaip.cleanup_old_tasks")
def cleanup_old_tasks():
    """Clean up old completed tasks."""
    return asyncio.run(cleanup_old_tasks_async())


async def cleanup_old_tasks_async():
    """Async cleanup of old tasks."""
    task_repo = TaskRepository()
    count = await task_repo.cleanup_old_tasks(days_old=30)
    return f"Cleaned up {count} old tasks"


@celery_app.task(name="agaip.health_check_agents")
def health_check_agents():
    """Check agent health and restart if needed."""
    return asyncio.run(health_check_agents_async())


async def health_check_agents_async():
    """Async agent health check."""
    agent_repo = AgentRepository()
    unhealthy_agents = await agent_repo.get_unhealthy_agents()

    restarted_count = 0
    for agent in unhealthy_agents:
        if agent.auto_restart:
            await agent.set_error("Health check failed - restarting")
            restarted_count += 1

    return (
        f"Checked {len(unhealthy_agents)} unhealthy agents, restarted {restarted_count}"
    )


@celery_app.task(name="agaip.retry_failed_tasks")
def retry_failed_tasks():
    """Retry failed tasks that have retries remaining."""
    return asyncio.run(retry_failed_tasks_async())


async def retry_failed_tasks_async():
    """Async retry of failed tasks."""
    task_repo = TaskRepository()
    retry_count = await task_repo.retry_failed_tasks(limit=50)
    return f"Retried {retry_count} failed tasks"


# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "agaip.cleanup_old_tasks",
        "schedule": 3600.0,  # Every hour
    },
    "health-check-agents": {
        "task": "agaip.health_check_agents",
        "schedule": 300.0,  # Every 5 minutes
    },
    "retry-failed-tasks": {
        "task": "agaip.retry_failed_tasks",
        "schedule": 600.0,  # Every 10 minutes
    },
}
