"""
Repository pattern implementations for the Agaip framework.

This module provides repository classes for data access abstraction
and business logic separation from database operations.
"""

from .base import BaseRepository
from .task import TaskRepository
from .agent import AgentRepository
from .user import UserRepository

__all__ = [
    "BaseRepository",
    "TaskRepository",
    "AgentRepository",
    "UserRepository",
]
