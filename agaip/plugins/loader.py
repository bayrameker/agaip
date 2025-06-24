"""
Plugin loader for the Agaip framework.

This module provides functionality to dynamically load, register,
and manage plugins at runtime.
"""

import importlib
import inspect
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

from agaip.plugins.base import BasePlugin
from agaip.core.exceptions import PluginError


class PluginRegistry:
    """Registry for managing loaded plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
        self._instances: Dict[str, BasePlugin] = {}
    
    def register(self, plugin_name: str, plugin_class: Type[BasePlugin]) -> None:
        """Register a plugin class."""
        if not issubclass(plugin_class, BasePlugin):
            raise PluginError(f"Plugin {plugin_name} must inherit from BasePlugin")
        
        self._plugins[plugin_name] = plugin_class
    
    def unregister(self, plugin_name: str) -> bool:
        """Unregister a plugin."""
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            
            # Also remove instance if exists
            if plugin_name in self._instances:
                del self._instances[plugin_name]
            
            return True
        return False
    
    def get_plugin_class(self, plugin_name: str) -> Optional[Type[BasePlugin]]:
        """Get a plugin class by name."""
        return self._plugins.get(plugin_name)
    
    def get_plugin_instance(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BasePlugin]:
        """Get or create a plugin instance."""
        if plugin_name in self._instances:
            return self._instances[plugin_name]
        
        plugin_class = self.get_plugin_class(plugin_name)
        if plugin_class:
            instance = plugin_class(config)
            self._instances[plugin_name] = instance
            return instance
        
        return None
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())
    
    def is_registered(self, plugin_name: str) -> bool:
        """Check if a plugin is registered."""
        return plugin_name in self._plugins
    
    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()
        self._instances.clear()


# Global plugin registry
_plugin_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    return _plugin_registry


def load_plugin(plugin_name: str, plugin_path: Optional[str] = None) -> Type[BasePlugin]:
    """
    Load a plugin by name.
    
    Args:
        plugin_name: Name of the plugin to load
        plugin_path: Optional path to the plugin module
        
    Returns:
        The plugin class
        
    Raises:
        PluginError: If plugin cannot be loaded
    """
    registry = get_plugin_registry()
    
    # Check if already loaded
    if registry.is_registered(plugin_name):
        return registry.get_plugin_class(plugin_name)
    
    try:
        # Try to load from built-in plugins first
        module_name = f"agaip.plugins.builtin.{plugin_name}"
        
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            if plugin_path:
                # Load from custom path
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                raise PluginError(f"Plugin {plugin_name} not found in built-in plugins")
        
        # Find the plugin class in the module
        plugin_class = None
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, BasePlugin) and 
                obj != BasePlugin and 
                obj.__module__ == module.__name__):
                plugin_class = obj
                break
        
        if not plugin_class:
            raise PluginError(f"No valid plugin class found in module {module_name}")
        
        # Register the plugin
        registry.register(plugin_name, plugin_class)
        
        return plugin_class
        
    except Exception as e:
        raise PluginError(f"Failed to load plugin {plugin_name}: {e}")


def create_plugin_instance(plugin_name: str, config: Optional[Dict[str, Any]] = None) -> BasePlugin:
    """
    Create a plugin instance.
    
    Args:
        plugin_name: Name of the plugin
        config: Plugin configuration
        
    Returns:
        Plugin instance
        
    Raises:
        PluginError: If plugin cannot be created
    """
    registry = get_plugin_registry()
    
    # Load plugin if not already loaded
    if not registry.is_registered(plugin_name):
        load_plugin(plugin_name)
    
    instance = registry.get_plugin_instance(plugin_name, config)
    if not instance:
        raise PluginError(f"Failed to create instance of plugin {plugin_name}")
    
    return instance


def discover_plugins(plugin_directory: str) -> List[str]:
    """
    Discover plugins in a directory.
    
    Args:
        plugin_directory: Directory to search for plugins
        
    Returns:
        List of discovered plugin names
    """
    plugin_dir = Path(plugin_directory)
    if not plugin_dir.exists():
        return []
    
    discovered = []
    
    for item in plugin_dir.iterdir():
        if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            # Single file plugin
            plugin_name = item.stem
            try:
                load_plugin(plugin_name, str(item))
                discovered.append(plugin_name)
            except Exception:
                pass  # Skip invalid plugins
        
        elif item.is_dir() and (item / '__init__.py').exists():
            # Package plugin
            plugin_name = item.name
            try:
                load_plugin(plugin_name, str(item / '__init__.py'))
                discovered.append(plugin_name)
            except Exception:
                pass  # Skip invalid plugins
    
    return discovered


def unload_plugin(plugin_name: str) -> bool:
    """
    Unload a plugin.
    
    Args:
        plugin_name: Name of the plugin to unload
        
    Returns:
        True if plugin was unloaded, False if not found
    """
    registry = get_plugin_registry()
    return registry.unregister(plugin_name)


def list_loaded_plugins() -> List[str]:
    """List all loaded plugin names."""
    registry = get_plugin_registry()
    return registry.list_plugins()


def is_plugin_loaded(plugin_name: str) -> bool:
    """Check if a plugin is loaded."""
    registry = get_plugin_registry()
    return registry.is_registered(plugin_name)
