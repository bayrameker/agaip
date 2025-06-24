"""
Celery configuration for the Agaip framework.

This module provides Celery setup for distributed task processing
with Redis as broker and result backend.
"""

from celery import Celery
from agaip.config.settings import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "agaip",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "agaip.services.tasks",
        "agaip.agents.tasks",
        "agaip.plugins.tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery.task_serializer,
    accept_content=settings.celery.accept_content,
    result_serializer=settings.celery.result_serializer,
    timezone=settings.celery.timezone,
    enable_utc=settings.celery.enable_utc,
    
    # Task routing
    task_routes={
        "agaip.services.tasks.*": {"queue": settings.celery.task_queue_default},
        "agaip.agents.tasks.*": {"queue": settings.celery.task_queue_priority},
    },
    
    # Task execution
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Result backend settings
    result_expires=3600,
    result_persistent=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)
