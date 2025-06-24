"""
Event system for the Agaip framework.

This module provides an asynchronous event bus for decoupled communication
between different components of the framework.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from agaip.core.exceptions import AgaipException

T = TypeVar('T', bound='Event')


@dataclass
class Event:
    """Base event class."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__


@dataclass
class AgentEvent(Event):
    """Base class for agent-related events."""
    agent_id: str = ""


@dataclass
class AgentStartedEvent(AgentEvent):
    """Event fired when an agent starts."""
    pass


@dataclass
class AgentStoppedEvent(AgentEvent):
    """Event fired when an agent stops."""
    reason: Optional[str] = None


@dataclass
class AgentErrorEvent(AgentEvent):
    """Event fired when an agent encounters an error."""
    error: str = ""
    error_type: str = ""


@dataclass
class TaskEvent(Event):
    """Base class for task-related events."""
    task_id: str = ""
    agent_id: str = ""


@dataclass
class TaskStartedEvent(TaskEvent):
    """Event fired when a task starts processing."""
    pass


@dataclass
class TaskCompletedEvent(TaskEvent):
    """Event fired when a task completes successfully."""
    result: Any = None
    duration: float = 0.0


@dataclass
class TaskFailedEvent(TaskEvent):
    """Event fired when a task fails."""
    error: str = ""
    error_type: str = ""


@dataclass
class PluginEvent(Event):
    """Base class for plugin-related events."""
    plugin_name: str = ""


@dataclass
class PluginLoadedEvent(PluginEvent):
    """Event fired when a plugin is loaded."""
    plugin_version: str = ""


@dataclass
class PluginUnloadedEvent(PluginEvent):
    """Event fired when a plugin is unloaded."""
    pass


@dataclass
class PluginErrorEvent(PluginEvent):
    """Event fired when a plugin encounters an error."""
    error: str = ""


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event."""
        pass


class EventBus:
    """Asynchronous event bus for decoupled communication."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._middleware: List[Callable] = []
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
    
    def subscribe(
        self, 
        event_type: Union[Type[Event], str], 
        handler: Union[Callable, EventHandler]
    ) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The event type to subscribe to
            handler: The handler function or EventHandler instance
        """
        event_name = self._get_event_name(event_type)
        
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        if isinstance(handler, EventHandler):
            self._handlers[event_name].append(handler.handle)
        else:
            self._handlers[event_name].append(handler)
    
    def unsubscribe(
        self, 
        event_type: Union[Type[Event], str], 
        handler: Union[Callable, EventHandler]
    ) -> bool:
        """
        Unsubscribe from an event type.
        
        Returns:
            True if handler was removed, False if not found
        """
        event_name = self._get_event_name(event_type)
        
        if event_name not in self._handlers:
            return False
        
        handler_func = handler.handle if isinstance(handler, EventHandler) else handler
        
        try:
            self._handlers[event_name].remove(handler_func)
            return True
        except ValueError:
            return False
    
    def add_middleware(self, middleware: Callable) -> None:
        """
        Add middleware to process events before handlers.
        
        Middleware should be an async function that takes an event
        and returns the (possibly modified) event or None to stop processing.
        """
        self._middleware.append(middleware)
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: The event to publish
        """
        if not self._running:
            await self.start()
        
        await self._queue.put(event)
    
    async def publish_and_wait(self, event: Event) -> None:
        """
        Publish an event and wait for all handlers to complete.
        
        Args:
            event: The event to publish
        """
        await self._process_event(event)
    
    async def start(self) -> None:
        """Start the event bus worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
    
    async def stop(self) -> None:
        """Stop the event bus worker."""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
    
    async def _worker(self) -> None:
        """Event processing worker."""
        while self._running:
            try:
                # Wait for event with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                # Log error but continue processing
                print(f"Error in event worker: {e}")
    
    async def _process_event(self, event: Event) -> None:
        """Process a single event through middleware and handlers."""
        try:
            # Process through middleware
            for middleware in self._middleware:
                event = await middleware(event)
                if event is None:
                    return  # Middleware stopped processing
            
            # Get handlers for this event type
            event_name = event.event_type
            handlers = self._handlers.get(event_name, [])
            
            # Also get handlers for base classes
            for base_class in event.__class__.__mro__[1:]:
                if issubclass(base_class, Event):
                    base_handlers = self._handlers.get(base_class.__name__, [])
                    handlers.extend(base_handlers)
            
            # Execute all handlers concurrently
            if handlers:
                tasks = [self._safe_handle(handler, event) for handler in handlers]
                await asyncio.gather(*tasks, return_exceptions=True)
        
        except Exception as e:
            # Log error but don't crash the event bus
            print(f"Error processing event {event.event_type}: {e}")
    
    async def _safe_handle(self, handler: Callable, event: Event) -> None:
        """Safely execute an event handler."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handler in thread pool
                await asyncio.get_event_loop().run_in_executor(None, handler, event)
        except Exception as e:
            # Log handler error but don't crash
            print(f"Error in event handler: {e}")
    
    def _get_event_name(self, event_type: Union[Type[Event], str]) -> str:
        """Get event name from type or string."""
        if isinstance(event_type, str):
            return event_type
        elif hasattr(event_type, '__name__'):
            return event_type.__name__
        else:
            return str(event_type)
    
    def get_handler_count(self, event_type: Union[Type[Event], str]) -> int:
        """Get the number of handlers for an event type."""
        event_name = self._get_event_name(event_type)
        return len(self._handlers.get(event_name, []))
    
    def clear_handlers(self, event_type: Optional[Union[Type[Event], str]] = None) -> None:
        """Clear handlers for a specific event type or all handlers."""
        if event_type is None:
            self._handlers.clear()
        else:
            event_name = self._get_event_name(event_type)
            self._handlers.pop(event_name, None)


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish(event: Event) -> None:
    """Convenience function to publish an event."""
    await get_event_bus().publish(event)


def subscribe(event_type: Union[Type[Event], str], handler: Union[Callable, EventHandler]) -> None:
    """Convenience function to subscribe to an event."""
    get_event_bus().subscribe(event_type, handler)
