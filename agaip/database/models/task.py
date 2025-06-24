"""
Task model for the Agaip framework.

This module defines the Task model for storing and managing
task execution data, results, and status tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from tortoise import fields
from tortoise.exceptions import ValidationError

from .base import BaseModel


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """Task model for storing task execution data."""

    # Basic task information
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    # Task execution
    agent_id = fields.CharField(max_length=100)
    plugin_name = fields.CharField(max_length=100, null=True)

    # Task data
    payload = fields.JSONField(default=dict)
    result = fields.JSONField(null=True)
    error_message = fields.TextField(null=True)
    error_type = fields.CharField(max_length=100, null=True)

    # Status and timing
    status = fields.CharEnumField(TaskStatus, default=TaskStatus.PENDING)
    priority = fields.CharEnumField(TaskPriority, default=TaskPriority.NORMAL)

    # Timing information
    queued_at = fields.DatetimeField(null=True)
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    timeout_at = fields.DatetimeField(null=True)

    # Execution details
    duration_seconds = fields.FloatField(null=True)
    retry_count = fields.IntField(default=0)
    max_retries = fields.IntField(default=3)

    # Parent/child task relationships
    parent_task = fields.ForeignKeyField(
        "models.Task", related_name="subtasks", null=True, on_delete=fields.CASCADE
    )

    # User who created the task
    created_by = fields.ForeignKeyField(
        "models.User", related_name="tasks", null=True, on_delete=fields.SET_NULL
    )

    class Meta:
        table = "tasks"
        indexes = [
            ["agent_id", "status"],
            ["status", "priority", "created_at"],
            ["created_by", "status"],
        ]

    async def start_processing(self) -> None:
        """Mark task as started."""
        if self.status != TaskStatus.QUEUED:
            raise ValidationError("Task must be queued to start processing")

        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()
        await self.save(update_fields=["status", "started_at"])

    async def complete_successfully(self, result: Any = None) -> None:
        """Mark task as completed successfully."""
        if self.status != TaskStatus.PROCESSING:
            raise ValidationError("Task must be processing to complete")

        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

        if self.started_at:
            self.duration_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()

        await self.save(
            update_fields=["status", "completed_at", "result", "duration_seconds"]
        )

    async def fail_with_error(self, error_message: str, error_type: str = None) -> None:
        """Mark task as failed with error."""
        if self.status not in [TaskStatus.PROCESSING, TaskStatus.QUEUED]:
            raise ValidationError("Task must be processing or queued to fail")

        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_type = error_type

        if self.started_at:
            self.duration_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()

        await self.save(
            update_fields=[
                "status",
                "completed_at",
                "error_message",
                "error_type",
                "duration_seconds",
            ]
        )

    async def cancel(self) -> None:
        """Cancel the task."""
        if self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            raise ValidationError("Cannot cancel a finished task")

        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()

        if self.started_at:
            self.duration_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()

        await self.save(update_fields=["status", "completed_at", "duration_seconds"])

    async def queue_for_retry(self) -> bool:
        """Queue task for retry if retries are available."""
        if self.retry_count >= self.max_retries:
            return False

        if self.status != TaskStatus.FAILED:
            raise ValidationError("Only failed tasks can be retried")

        self.status = TaskStatus.QUEUED
        self.retry_count += 1
        self.queued_at = datetime.utcnow()
        self.error_message = None
        self.error_type = None

        await self.save(
            update_fields=[
                "status",
                "retry_count",
                "queued_at",
                "error_message",
                "error_type",
            ]
        )
        return True

    @property
    def is_finished(self) -> bool:
        """Check if task is in a finished state."""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        ]

    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED

    @property
    def has_retries_left(self) -> bool:
        """Check if task has retries remaining."""
        return self.retry_count < self.max_retries

    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """Convert task to dictionary with additional computed fields."""
        data = super().to_dict(exclude_fields)

        # Add computed fields
        data["is_finished"] = self.is_finished
        data["is_successful"] = self.is_successful
        data["has_retries_left"] = self.has_retries_left

        return data
