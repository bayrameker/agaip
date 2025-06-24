"""
Database layer for the Agaip framework.

This module provides database abstraction, connection management,
migrations, and repository patterns for data access.
"""

from .connection import DatabaseManager, get_database_manager
from .models.base import BaseModel
from .repositories.base import BaseRepository

__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "BaseModel",
    "BaseRepository",
]
