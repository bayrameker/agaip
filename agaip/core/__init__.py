"""
Agaip Core Module

This module contains the core framework components including:
- Application factory and lifecycle management
- Dependency injection container
- Event system and bus
- Custom exceptions and middleware
"""

__version__ = "3.0.0"
__author__ = "Bayram Eker"
__email__ = "eker600@gmail.com"

from .application import AgaipApplication, create_application, get_application
from .container import Container
from .events import Event, EventBus
from .exceptions import AgaipException, ConfigurationError, PluginError

__all__ = [
    "AgaipApplication",
    "get_application",
    "create_application",
    "Container",
    "EventBus",
    "Event",
    "AgaipException",
    "ConfigurationError",
    "PluginError",
]
