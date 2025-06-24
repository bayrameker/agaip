"""
Task service for the Agaip framework.

This module provides business logic for task management,
execution coordination, and status tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from agaip.core.events import TaskStartedEvent, publish
from agaip.core.exceptions import TaskError
from agaip.database.models.task import Task, TaskPriority, TaskStatus
from agaip.database.repositories.agent import AgentRepository
from agaip.database.repositories.task import TaskRepository
from agaip.services.tasks import process_task_sync


class TaskService:
    """Service for managing task execution and lifecycle."""

    def __init__(self, task_repo: TaskRepository, agent_repo: AgentRepository):
        self.task_repo = task_repo
        self.agent_repo = agent_repo

    async def create_task(
        self,
        name: str,
        agent_id: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None,
        description: Optional[str] = None,
        created_by_id: Optional[UUID] = None,
    ) -> Task:
        """Create a new task and queue it for execution."""

        # Verify agent exists
        agent = await self.agent_repo.get_by_field("name", agent_id)
        if not agent:
            raise TaskError(f"Agent '{agent_id}' not found")

        if not agent.enabled:
            raise TaskError(f"Agent '{agent_id}' is disabled")

        # Create task
        task = await self.task_repo.create_task(
            name=name,
            agent_id=agent_id,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            description=description,
            created_by_id=created_by_id,
        )

        # Queue task for processing
        await self.queue_task(task.id)

        return task

    async def queue_task(self, task_id: UUID) -> bool:
        """Queue a task for background processing."""

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return False

        # Update task status to queued
        success = await self.task_repo.queue_task(task_id)
        if not success:
            return False

        # Submit to Celery for background processing
        process_task_sync.delay(
            task_id=str(task_id), agent_id=task.agent_id, payload=task.payload
        )

        return True

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get a task by ID."""
        return await self.task_repo.get_by_id(task_id)

    async def list_tasks(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Task]:
        """List tasks with optional filtering."""

        filters = {}

        if user_id:
            filters["created_by_id"] = user_id

        if status:
            filters["status"] = status

        if agent_id:
            filters["agent_id"] = agent_id

        if filters:
            tasks = await self.task_repo.filter(**filters)
        else:
            tasks = await self.task_repo.get_all(limit=limit, offset=offset)

        return tasks[:limit]  # Apply limit if not already applied

    async def cancel_task(self, task_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Cancel a task if it's not already finished."""

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return False

        # Check permissions
        if user_id and task.created_by_id != user_id:
            return False

        # Can only cancel pending, queued, or processing tasks
        if task.status not in [
            TaskStatus.PENDING,
            TaskStatus.QUEUED,
            TaskStatus.PROCESSING,
        ]:
            return False

        await task.cancel()
        return True

    async def retry_task(self, task_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Retry a failed task if retries are available."""

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return False

        # Check permissions
        if user_id and task.created_by_id != user_id:
            return False

        # Can only retry failed tasks
        if task.status != TaskStatus.FAILED:
            return False

        # Check if retries are available
        if not task.has_retries_left:
            return False

        # Queue for retry
        success = await task.queue_for_retry()
        if success:
            # Submit to Celery again
            process_task_sync.delay(
                task_id=str(task_id), agent_id=task.agent_id, payload=task.payload
            )

        return success

    async def get_task_statistics(
        self,
        user_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get task execution statistics."""

        return await self.task_repo.get_task_statistics(
            agent_id=agent_id, start_date=start_date, end_date=end_date
        )

    async def cleanup_old_tasks(self, days_old: int = 30) -> int:
        """Clean up old completed/failed tasks."""
        return await self.task_repo.cleanup_old_tasks(days_old)

    async def get_pending_tasks(
        self, agent_id: Optional[str] = None, limit: int = 10
    ) -> List[Task]:
        """Get pending tasks for processing."""
        return await self.task_repo.get_pending_tasks(agent_id, limit)

    async def get_processing_tasks(self, agent_id: Optional[str] = None) -> List[Task]:
        """Get currently processing tasks."""
        return await self.task_repo.get_processing_tasks(agent_id)

    async def handle_timeout_tasks(self) -> int:
        """Handle tasks that have timed out."""
        timed_out_tasks = await self.task_repo.get_timed_out_tasks()

        count = 0
        for task in timed_out_tasks:
            await task.fail_with_error("Task timed out", "TimeoutError")
            count += 1

        return count
