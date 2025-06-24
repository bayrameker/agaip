"""
Base plugin class for the Agaip framework.

This module provides the abstract base class that all plugins must inherit from,
defining the standard interface and lifecycle methods.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BasePlugin(ABC):
    """Abstract base class for all Agaip plugins."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin with configuration.

        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config or {}
        self.is_loaded = False
        self.name = self.__class__.__name__

    @abstractmethod
    async def load_model(self) -> None:
        """
        Load the model or initialize resources.

        This method should be implemented by each plugin to perform
        any necessary initialization, model loading, or resource setup.
        """
        pass

    @abstractmethod
    async def predict(self, data: Dict[str, Any]) -> Any:
        """
        Make a prediction or process data.

        Args:
            data: Input data for processing

        Returns:
            Processed result or prediction
        """
        pass

    async def unload_model(self) -> None:
        """
        Unload the model and clean up resources.

        This method can be overridden by plugins that need to perform
        cleanup operations when the plugin is unloaded.
        """
        self.is_loaded = False

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the plugin.

        Returns:
            Dictionary containing health status information
        """
        return {
            "status": "healthy" if self.is_loaded else "not_loaded",
            "plugin_name": self.name,
            "is_loaded": self.is_loaded,
        }

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information.

        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "name": self.name,
            "version": getattr(self, "version", "1.0.0"),
            "description": getattr(self, "description", "No description available"),
            "author": getattr(self, "author", "Unknown"),
            "is_loaded": self.is_loaded,
            "config": self.config,
        }

    def validate_config(self) -> bool:
        """
        Validate plugin configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Default implementation - can be overridden by plugins
        return True

    async def initialize(self) -> None:
        """
        Initialize the plugin.

        This method is called when the plugin is first loaded.
        It should call load_model() and perform any other setup.
        """
        if not self.validate_config():
            raise ValueError(f"Invalid configuration for plugin {self.name}")

        await self.load_model()
        self.is_loaded = True

    async def shutdown(self) -> None:
        """
        Shutdown the plugin gracefully.

        This method is called when the plugin is being unloaded.
        """
        await self.unload_model()
        self.is_loaded = False

    def __str__(self) -> str:
        """String representation of the plugin."""
        return f"{self.name}(loaded={self.is_loaded})"

    def __repr__(self) -> str:
        """Detailed string representation of the plugin."""
        return f"{self.__class__.__name__}(name='{self.name}', loaded={self.is_loaded})"
