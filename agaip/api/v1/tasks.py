"""
Task management endpoints for the Agaip API.

This module provides endpoints for creating, managing,
and monitoring task execution.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from agaip.api.dependencies import get_current_user, get_container_dependency
from agaip.database.models.user import User
from agaip.database.models.task import TaskPriority
from agaip.services.task_service import TaskService
from agaip.core.container import Container

router = APIRouter()


class TaskCreateRequest(BaseModel):
    name: str
    agent_id: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    description: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    agent_id: str
    status: str
    priority: str
    created_at: str
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@router.post("/tasks", response_model=TaskResponse, summary="Create a new task")
async def create_task(
    task_request: TaskCreateRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> TaskResponse:
    """Create a new task for execution."""
    
    task_service = container.resolve(TaskService)
    
    task = await task_service.create_task(
        name=task_request.name,
        agent_id=task_request.agent_id,
        payload=task_request.payload,
        priority=task_request.priority,
        max_retries=task_request.max_retries,
        timeout_seconds=task_request.timeout_seconds,
        description=task_request.description,
        created_by_id=current_user.id
    )
    
    return TaskResponse(
        id=str(task.id),
        name=task.name,
        agent_id=task.agent_id,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at.isoformat(),
        payload=task.payload,
        result=task.result,
        error_message=task.error_message
    )


@router.get("/tasks", response_model=List[TaskResponse], summary="List tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> List[TaskResponse]:
    """List tasks with optional filtering."""
    
    task_service = container.resolve(TaskService)
    
    tasks = await task_service.list_tasks(
        user_id=current_user.id if not current_user.is_admin else None,
        status=status,
        agent_id=agent_id,
        limit=limit,
        offset=offset
    )
    
    return [
        TaskResponse(
            id=str(task.id),
            name=task.name,
            agent_id=task.agent_id,
            status=task.status,
            priority=task.priority,
            created_at=task.created_at.isoformat(),
            payload=task.payload,
            result=task.result,
            error_message=task.error_message
        )
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get task details")
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> TaskResponse:
    """Get detailed information about a specific task."""
    
    task_service = container.resolve(TaskService)
    
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions
    if not current_user.is_admin and task.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return TaskResponse(
        id=str(task.id),
        name=task.name,
        agent_id=task.agent_id,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at.isoformat(),
        payload=task.payload,
        result=task.result,
        error_message=task.error_message
    )


@router.post("/tasks/{task_id}/cancel", summary="Cancel a task")
async def cancel_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> Dict[str, Any]:
    """Cancel a pending or processing task."""
    
    task_service = container.resolve(TaskService)
    
    success = await task_service.cancel_task(task_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")
    
    return {"message": "Task cancelled successfully"}


@router.post("/tasks/{task_id}/retry", summary="Retry a failed task")
async def retry_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> Dict[str, Any]:
    """Retry a failed task if retries are available."""
    
    task_service = container.resolve(TaskService)
    
    success = await task_service.retry_task(task_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Task cannot be retried")
    
    return {"message": "Task queued for retry"}


@router.get("/tasks/statistics", summary="Get task statistics")
async def get_task_statistics(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container_dependency)
) -> Dict[str, Any]:
    """Get task execution statistics."""
    
    task_service = container.resolve(TaskService)
    
    stats = await task_service.get_task_statistics(
        user_id=current_user.id if not current_user.is_admin else None,
        agent_id=agent_id
    )
    
    return stats
