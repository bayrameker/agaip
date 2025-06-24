"""
Plugin service for the Agaip framework.

This module provides business logic for plugin management,
discovery, loading, and lifecycle operations.
"""

import os
import importlib
from typing import Any, Dict, List, Optional
from pathlib import Path

from agaip.core.exceptions import PluginError
from agaip.core.events import publish, PluginLoadedEvent, PluginUnloadedEvent


class PluginService:
    """Service for managing plugins and their lifecycle."""
    
    def __init__(self):
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize the plugin service."""
        # Load built-in plugins
        await self._load_builtin_plugins()
    
    async def discover_plugins(self, plugin_directory: str = "./plugins") -> List[str]:
        """Discover available plugins in the plugin directory."""
        
        plugin_dir = Path(plugin_directory)
        if not plugin_dir.exists():
            return []
        
        discovered_plugins = []
        
        for plugin_path in plugin_dir.iterdir():
            if plugin_path.is_dir() and (plugin_path / "__init__.py").exists():
                plugin_name = plugin_path.name
                discovered_plugins.append(plugin_name)
                
                # Try to load the plugin
                try:
                    await self.load_plugin(plugin_name, str(plugin_path))
                except Exception as e:
                    print(f"Failed to load plugin {plugin_name}: {e}")
        
        return discovered_plugins
    
    async def load_plugin(self, plugin_name: str, plugin_path: Optional[str] = None) -> Any:
        """Load a plugin by name."""
        
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]
        
        try:
            # Import the plugin module
            if plugin_path:
                # Load from custom path
                spec = importlib.util.spec_from_file_location(
                    plugin_name, 
                    os.path.join(plugin_path, "__init__.py")
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Load from built-in plugins
                module = importlib.import_module(f"agaip.plugins.builtin.{plugin_name}")
            
            # Get the plugin class
            plugin_class = getattr(module, f"{plugin_name.title()}Plugin", None)
            if not plugin_class:
                # Try alternative naming conventions
                plugin_class = getattr(module, "Plugin", None)
            
            if not plugin_class:
                raise PluginError(f"Plugin class not found in {plugin_name}")
            
            # Store the plugin class
            self.loaded_plugins[plugin_name] = plugin_class
            
            # Publish event
            await publish(PluginLoadedEvent(plugin_name=plugin_name))
            
            return plugin_class
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin {plugin_name}: {e}")
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        
        if plugin_name not in self.loaded_plugins:
            return False
        
        try:
            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]
            
            # Remove from configs
            if plugin_name in self.plugin_configs:
                del self.plugin_configs[plugin_name]
            
            # Publish event
            await publish(PluginUnloadedEvent(plugin_name=plugin_name))
            
            return True
            
        except Exception as e:
            raise PluginError(f"Failed to unload plugin {plugin_name}: {e}")
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin."""
        
        # Unload first
        await self.unload_plugin(plugin_name)
        
        # Load again
        try:
            await self.load_plugin(plugin_name)
            return True
        except Exception:
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get a loaded plugin class."""
        return self.loaded_plugins.get(plugin_name)
    
    def list_loaded_plugins(self) -> List[str]:
        """List all loaded plugin names."""
        return list(self.loaded_plugins.keys())
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self.loaded_plugins
    
    async def check_for_updates(self) -> List[str]:
        """Check for plugin updates and reload if necessary."""
        
        updated_plugins = []
        
        # This is a simplified implementation
        # In a real system, you'd check file modification times,
        # version numbers, or use a more sophisticated update mechanism
        
        for plugin_name in self.loaded_plugins.keys():
            # For now, just return empty list
            # In the future, implement actual update checking
            pass
        
        return updated_plugins
    
    async def _load_builtin_plugins(self) -> None:
        """Load built-in plugins."""
        
        builtin_plugins = [
            "dummy_model",
            "openai_plugin", 
            "huggingface_plugin"
        ]
        
        for plugin_name in builtin_plugins:
            try:
                await self.load_plugin(plugin_name)
            except Exception as e:
                print(f"Failed to load built-in plugin {plugin_name}: {e}")
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Configure a plugin with settings."""
        self.plugin_configs[plugin_name] = config
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a plugin."""
        return self.plugin_configs.get(plugin_name, {})
