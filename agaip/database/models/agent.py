"""
Agent model for the Agaip framework.

This module defines the Agent model for storing and managing
agent configurations, status, and performance metrics.
"""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime

from tortoise import fields
from tortoise.exceptions import ValidationError

from .base import BaseModel


class AgentStatus(str, Enum):
    """Agent status."""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"
    MAINTENANCE = "maintenance"


class AgentType(str, Enum):
    """Agent types."""
    AI_MODEL = "ai_model"
    WORKFLOW = "workflow"
    CUSTOM = "custom"
    SYSTEM = "system"


class Agent(BaseModel):
    """Agent model for storing agent configurations and status."""
    
    # Basic agent information
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True)
    agent_type = fields.CharEnumField(AgentType, default=AgentType.CUSTOM)
    
    # Plugin information
    plugin_name = fields.CharField(max_length=100)
    plugin_version = fields.CharField(max_length=50, null=True)
    plugin_config = fields.JSONField(default=dict)
    
    # Status and health
    status = fields.CharEnumField(AgentStatus, default=AgentStatus.INACTIVE)
    last_heartbeat = fields.DatetimeField(null=True)
    last_error = fields.TextField(null=True)
    error_count = fields.IntField(default=0)
    
    # Performance metrics
    total_tasks_processed = fields.IntField(default=0)
    successful_tasks = fields.IntField(default=0)
    failed_tasks = fields.IntField(default=0)
    average_processing_time = fields.FloatField(null=True)
    
    # Configuration
    max_concurrent_tasks = fields.IntField(default=1)
    timeout_seconds = fields.IntField(default=300)
    auto_restart = fields.BooleanField(default=True)
    
    # Resource limits
    memory_limit_mb = fields.IntField(null=True)
    cpu_limit_percent = fields.FloatField(null=True)
    
    # Scheduling
    enabled = fields.BooleanField(default=True)
    priority = fields.IntField(default=0)  # Higher number = higher priority
    
    # Tags for categorization
    tags = fields.JSONField(default=list)
    
    class Meta:
        table = "agents"
        indexes = [
            ["status", "enabled"],
            ["agent_type", "status"],
            ["priority", "status"],
        ]
    
    async def activate(self) -> None:
        """Activate the agent."""
        if not self.enabled:
            raise ValidationError("Cannot activate disabled agent")
        
        self.status = AgentStatus.ACTIVE
        self.last_heartbeat = datetime.utcnow()
        await self.save(update_fields=['status', 'last_heartbeat'])
    
    async def deactivate(self) -> None:
        """Deactivate the agent."""
        self.status = AgentStatus.INACTIVE
        await self.save(update_fields=['status'])
    
    async def set_busy(self) -> None:
        """Mark agent as busy."""
        if self.status != AgentStatus.ACTIVE:
            raise ValidationError("Agent must be active to become busy")
        
        self.status = AgentStatus.BUSY
        await self.save(update_fields=['status'])
    
    async def set_error(self, error_message: str) -> None:
        """Mark agent as in error state."""
        self.status = AgentStatus.ERROR
        self.last_error = error_message
        self.error_count += 1
        await self.save(update_fields=['status', 'last_error', 'error_count'])
    
    async def heartbeat(self) -> None:
        """Update agent heartbeat."""
        self.last_heartbeat = datetime.utcnow()
        
        # If agent was in error state and heartbeat is received, reactivate
        if self.status == AgentStatus.ERROR and self.auto_restart:
            self.status = AgentStatus.ACTIVE
            await self.save(update_fields=['last_heartbeat', 'status'])
        else:
            await self.save(update_fields=['last_heartbeat'])
    
    async def record_task_completion(self, success: bool, processing_time: float) -> None:
        """Record task completion metrics."""
        self.total_tasks_processed += 1
        
        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1
        
        # Update average processing time
        if self.average_processing_time is None:
            self.average_processing_time = processing_time
        else:
            # Simple moving average
            total_time = self.average_processing_time * (self.total_tasks_processed - 1)
            self.average_processing_time = (total_time + processing_time) / self.total_tasks_processed
        
        await self.save(update_fields=[
            'total_tasks_processed', 'successful_tasks', 'failed_tasks', 'average_processing_time'
        ])
    
    async def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.total_tasks_processed = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.average_processing_time = None
        self.error_count = 0
        await self.save(update_fields=[
            'total_tasks_processed', 'successful_tasks', 'failed_tasks', 
            'average_processing_time', 'error_count'
        ])
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the agent."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the agent."""
        if self.tags is None:
            return False
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if agent has a specific tag."""
        return self.tags is not None and tag in self.tags
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        if not self.enabled:
            return False
        
        if self.status in [AgentStatus.ERROR, AgentStatus.STOPPING]:
            return False
        
        # Check heartbeat (consider unhealthy if no heartbeat in last 5 minutes)
        if self.last_heartbeat:
            time_since_heartbeat = (datetime.utcnow() - self.last_heartbeat).total_seconds()
            return time_since_heartbeat < 300  # 5 minutes
        
        return self.status == AgentStatus.ACTIVE
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        if self.total_tasks_processed == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks_processed
    
    @property
    def failure_rate(self) -> float:
        """Calculate task failure rate."""
        if self.total_tasks_processed == 0:
            return 0.0
        return self.failed_tasks / self.total_tasks_processed
    
    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """Convert agent to dictionary with additional computed fields."""
        data = super().to_dict(exclude_fields)
        
        # Add computed fields
        data['is_healthy'] = self.is_healthy
        data['success_rate'] = self.success_rate
        data['failure_rate'] = self.failure_rate
        
        return data
