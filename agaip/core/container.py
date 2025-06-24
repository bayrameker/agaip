"""
Dependency Injection Container for the Agaip framework.

This module provides a lightweight dependency injection container
for managing service dependencies and promoting loose coupling.
"""

import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
from functools import wraps

from agaip.core.exceptions import ConfigurationError

T = TypeVar('T')


class Container:
    """Lightweight dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._aliases: Dict[str, str] = {}
    
    def register(
        self, 
        service_type: Union[Type[T], str], 
        implementation: Union[T, Callable[[], T], Type[T]], 
        singleton: bool = True,
        alias: Optional[str] = None
    ) -> 'Container':
        """
        Register a service in the container.
        
        Args:
            service_type: The service type or name to register
            implementation: The implementation, factory function, or class
            singleton: Whether to create a single instance (default: True)
            alias: Optional alias for the service
        
        Returns:
            Self for method chaining
        """
        service_name = self._get_service_name(service_type)
        
        if inspect.isclass(implementation):
            # Register class as factory
            self._factories[service_name] = implementation
        elif callable(implementation):
            # Register factory function
            self._factories[service_name] = implementation
        else:
            # Register instance directly
            if singleton:
                self._singletons[service_name] = implementation
            else:
                self._services[service_name] = implementation
        
        # Register alias if provided
        if alias:
            self._aliases[alias] = service_name
        
        return self
    
    def register_singleton(
        self, 
        service_type: Union[Type[T], str], 
        implementation: Union[T, Callable[[], T], Type[T]],
        alias: Optional[str] = None
    ) -> 'Container':
        """Register a service as singleton."""
        return self.register(service_type, implementation, singleton=True, alias=alias)
    
    def register_transient(
        self, 
        service_type: Union[Type[T], str], 
        implementation: Union[Callable[[], T], Type[T]],
        alias: Optional[str] = None
    ) -> 'Container':
        """Register a service as transient (new instance each time)."""
        return self.register(service_type, implementation, singleton=False, alias=alias)
    
    def register_instance(
        self, 
        service_type: Union[Type[T], str], 
        instance: T,
        alias: Optional[str] = None
    ) -> 'Container':
        """Register a specific instance."""
        service_name = self._get_service_name(service_type)
        self._singletons[service_name] = instance
        
        if alias:
            self._aliases[alias] = service_name
        
        return self
    
    def resolve(self, service_type: Union[Type[T], str]) -> T:
        """
        Resolve a service from the container.
        
        Args:
            service_type: The service type or name to resolve
        
        Returns:
            The resolved service instance
        
        Raises:
            ConfigurationError: If service is not registered
        """
        service_name = self._get_service_name(service_type)
        
        # Check for alias
        if service_name in self._aliases:
            service_name = self._aliases[service_name]
        
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Check direct services
        if service_name in self._services:
            return self._services[service_name]
        
        # Check factories
        if service_name in self._factories:
            factory = self._factories[service_name]
            instance = self._create_instance(factory)
            
            # Cache as singleton if it was registered as such
            if service_name not in self._services:
                self._singletons[service_name] = instance
            
            return instance
        
        raise ConfigurationError(f"Service '{service_name}' is not registered")
    
    def is_registered(self, service_type: Union[Type[T], str]) -> bool:
        """Check if a service is registered."""
        service_name = self._get_service_name(service_type)
        
        # Check for alias
        if service_name in self._aliases:
            service_name = self._aliases[service_name]
        
        return (
            service_name in self._singletons or 
            service_name in self._services or 
            service_name in self._factories
        )
    
    def unregister(self, service_type: Union[Type[T], str]) -> bool:
        """
        Unregister a service from the container.
        
        Returns:
            True if service was unregistered, False if not found
        """
        service_name = self._get_service_name(service_type)
        
        # Check for alias
        if service_name in self._aliases:
            actual_name = self._aliases[service_name]
            del self._aliases[service_name]
            service_name = actual_name
        
        removed = False
        
        if service_name in self._singletons:
            del self._singletons[service_name]
            removed = True
        
        if service_name in self._services:
            del self._services[service_name]
            removed = True
        
        if service_name in self._factories:
            del self._factories[service_name]
            removed = True
        
        return removed
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._aliases.clear()
    
    def _get_service_name(self, service_type: Union[Type[T], str]) -> str:
        """Get the service name from type or string."""
        if isinstance(service_type, str):
            return service_type
        elif hasattr(service_type, '__name__'):
            return service_type.__name__
        else:
            return str(service_type)
    
    def _create_instance(self, factory: Callable) -> Any:
        """Create an instance using dependency injection."""
        if inspect.isclass(factory):
            # Get constructor parameters
            sig = inspect.signature(factory.__init__)
            params = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # Try to resolve parameter by type annotation
                if param.annotation != inspect.Parameter.empty:
                    try:
                        params[param_name] = self.resolve(param.annotation)
                    except ConfigurationError:
                        # If can't resolve and no default, raise error
                        if param.default == inspect.Parameter.empty:
                            raise ConfigurationError(
                                f"Cannot resolve dependency '{param_name}' of type '{param.annotation}' "
                                f"for service '{factory.__name__}'"
                            )
            
            return factory(**params)
        else:
            # Call factory function
            sig = inspect.signature(factory)
            params = {}
            
            for param_name, param in sig.parameters.items():
                # Try to resolve parameter by type annotation
                if param.annotation != inspect.Parameter.empty:
                    try:
                        params[param_name] = self.resolve(param.annotation)
                    except ConfigurationError:
                        # If can't resolve and no default, raise error
                        if param.default == inspect.Parameter.empty:
                            raise ConfigurationError(
                                f"Cannot resolve dependency '{param_name}' of type '{param.annotation}' "
                                f"for factory function"
                            )
            
            return factory(**params)


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def inject(service_type: Union[Type[T], str]) -> Callable:
    """
    Decorator for dependency injection.
    
    Usage:
        @inject(SomeService)
        def my_function(service: SomeService):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            service = container.resolve(service_type)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator
