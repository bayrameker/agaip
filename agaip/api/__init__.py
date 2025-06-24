"""
API layer for the Agaip framework.

This module provides the FastAPI application with versioned endpoints,
middleware, dependencies, and schema definitions.
"""

from .app import create_app, get_app
from .dependencies import get_current_user, get_database, get_settings

__all__ = [
    "create_app",
    "get_app",
    "get_current_user",
    "get_database", 
    "get_settings",
]
