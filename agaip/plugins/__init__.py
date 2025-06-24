"""
Plugin system for the Agaip framework.

This module provides the plugin architecture including base classes,
interfaces, loading mechanisms, and built-in plugins.
"""

from .base import BasePlugin
from .loader import load_plugin, get_plugin_registry

__all__ = [
    "BasePlugin",
    "load_plugin",
    "get_plugin_registry",
]