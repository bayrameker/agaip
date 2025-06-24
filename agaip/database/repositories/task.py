"""
Task repository for the Agaip framework.

This module provides specialized data access methods for Task model
including task queue operations, status filtering, and metrics.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from tortoise.queryset import QuerySet

from agaip.database.models.task import Task, TaskStatus, TaskPriority
from .base import BaseRepository


class TaskRepository(BaseRepository):
    """Repository for Task model with specialized operations."""
    
    def __init__(self):
        super().__init__(Task)
    
    async def create_task(
        self,
        name: str,
        agent_id: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None,
        parent_task_id: Optional[UUID] = None,
        created_by_id: Optional[UUID] = None,
        **kwargs
    ) -> Task:
        """Create a new task with proper initialization."""
        task_data = {
            "name": name,
            "agent_id": agent_id,
            "payload": payload,
            "priority": priority,
            "max_retries": max_retries,
            "status": TaskStatus.PENDING,
            **kwargs
        }
        
        if timeout_seconds:
            task_data["timeout_at"] = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        
        if parent_task_id:
            task_data["parent_task_id"] = parent_task_id
        
        if created_by_id:
            task_data["created_by_id"] = created_by_id
        
        return await self.create(**task_data)
    
    async def get_pending_tasks(self, agent_id: Optional[str] = None, limit: int = 10) -> List[Task]:
        """Get pending tasks, optionally filtered by agent."""
        queryset = self.model_class.filter(status=TaskStatus.PENDING)
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        return await queryset.order_by("-priority", "created_at").limit(limit)
    
    async def get_queued_tasks(self, agent_id: Optional[str] = None, limit: int = 10) -> List[Task]:
        """Get queued tasks ready for processing."""
        queryset = self.model_class.filter(status=TaskStatus.QUEUED)
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        return await queryset.order_by("-priority", "queued_at").limit(limit)
    
    async def get_processing_tasks(self, agent_id: Optional[str] = None) -> List[Task]:
        """Get currently processing tasks."""
        queryset = self.model_class.filter(status=TaskStatus.PROCESSING)
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        return await queryset.order_by("started_at")
    
    async def get_failed_tasks(
        self, 
        agent_id: Optional[str] = None,
        retryable_only: bool = False,
        limit: int = 50
    ) -> List[Task]:
        """Get failed tasks, optionally only retryable ones."""
        queryset = self.model_class.filter(status=TaskStatus.FAILED)
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        if retryable_only:
            # Only tasks that haven't exceeded max retries
            queryset = queryset.filter(retry_count__lt=models.F("max_retries"))
        
        return await queryset.order_by("-completed_at").limit(limit)
    
    async def get_timed_out_tasks(self) -> List[Task]:
        """Get tasks that have timed out."""
        now = datetime.utcnow()
        return await self.model_class.filter(
            status=TaskStatus.PROCESSING,
            timeout_at__lt=now
        )
    
    async def queue_task(self, task_id: UUID) -> bool:
        """Queue a pending task for processing."""
        task = await self.get_by_id(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.QUEUED
            task.queued_at = datetime.utcnow()
            await task.save(update_fields=['status', 'queued_at'])
            return True
        return False
    
    async def get_task_statistics(
        self, 
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get task statistics for reporting."""
        queryset = self.model_class.all()
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Count by status
        total_tasks = await queryset.count()
        completed_tasks = await queryset.filter(status=TaskStatus.COMPLETED).count()
        failed_tasks = await queryset.filter(status=TaskStatus.FAILED).count()
        processing_tasks = await queryset.filter(status=TaskStatus.PROCESSING).count()
        pending_tasks = await queryset.filter(status=TaskStatus.PENDING).count()
        queued_tasks = await queryset.filter(status=TaskStatus.QUEUED).count()
        
        # Calculate success rate
        finished_tasks = completed_tasks + failed_tasks
        success_rate = (completed_tasks / finished_tasks * 100) if finished_tasks > 0 else 0
        
        # Get average processing time for completed tasks
        completed_with_duration = await queryset.filter(
            status=TaskStatus.COMPLETED,
            duration_seconds__isnull=False
        )
        
        avg_duration = 0
        if completed_with_duration:
            durations = [task.duration_seconds for task in completed_with_duration]
            avg_duration = sum(durations) / len(durations)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "processing_tasks": processing_tasks,
            "pending_tasks": pending_tasks,
            "queued_tasks": queued_tasks,
            "success_rate": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
        }
    
    async def get_tasks_by_user(
        self, 
        user_id: UUID, 
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Task]:
        """Get tasks created by a specific user."""
        queryset = self.model_class.filter(created_by_id=user_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return await queryset.order_by("-created_at").limit(limit)
    
    async def get_subtasks(self, parent_task_id: UUID) -> List[Task]:
        """Get all subtasks of a parent task."""
        return await self.model_class.filter(parent_task_id=parent_task_id).order_by("created_at")
    
    async def cleanup_old_tasks(self, days_old: int = 30) -> int:
        """Clean up old completed/failed tasks."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_tasks = await self.model_class.filter(
            status__in=[TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
            completed_at__lt=cutoff_date
        )
        
        count = len(old_tasks)
        
        for task in old_tasks:
            await task.delete()
        
        return count
    
    async def retry_failed_tasks(self, agent_id: Optional[str] = None, limit: int = 10) -> int:
        """Retry failed tasks that have retries remaining."""
        queryset = self.model_class.filter(
            status=TaskStatus.FAILED,
            retry_count__lt=models.F("max_retries")
        )
        
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        failed_tasks = await queryset.limit(limit)
        retry_count = 0
        
        for task in failed_tasks:
            if await task.queue_for_retry():
                retry_count += 1
        
        return retry_count
