"""
Application factory for the Agaip framework.

This module provides the main application class that coordinates
all framework components and manages the application lifecycle.
"""

import asyncio
import logging
from typing import Optional

from agaip.config.settings import Settings, get_settings
from agaip.core.container import Container, get_container
from agaip.core.events import EventBus, get_event_bus
from agaip.core.exceptions import AgaipException
from agaip.database.connection import DatabaseManager, get_database_manager

logger = logging.getLogger(__name__)


class AgaipApplication:
    """Main application class for the Agaip framework."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.container = get_container()
        self.event_bus = get_event_bus()
        self.database_manager = get_database_manager()
        self._initialized = False
        self._running = False

    async def initialize(self) -> None:
        """Initialize the application and all components."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Agaip application...")

            # Initialize database
            await self.database_manager.initialize()

            # Initialize event bus
            await self.event_bus.start()

            # Register core services in container
            await self._register_services()

            # Initialize plugins
            await self._initialize_plugins()

            # Initialize agents
            await self._initialize_agents()

            self._initialized = True
            logger.info("Agaip application initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise AgaipException(f"Application initialization failed: {e}")

    async def start(self) -> None:
        """Start the application."""
        if not self._initialized:
            await self.initialize()

        if self._running:
            return

        try:
            logger.info("Starting Agaip application...")

            # Start background services
            await self._start_background_services()

            self._running = True
            logger.info("Agaip application started successfully")

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            raise AgaipException(f"Application start failed: {e}")

    async def stop(self) -> None:
        """Stop the application gracefully."""
        if not self._running:
            return

        try:
            logger.info("Stopping Agaip application...")

            # Stop background services
            await self._stop_background_services()

            # Stop event bus
            await self.event_bus.stop()

            # Close database connections
            await self.database_manager.close()

            self._running = False
            logger.info("Agaip application stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping application: {e}")

    async def _register_services(self) -> None:
        """Register core services in the dependency injection container."""
        from agaip.database.repositories.agent import AgentRepository

        # Register repositories
        from agaip.database.repositories.task import TaskRepository
        from agaip.database.repositories.user import UserRepository
        from agaip.services.agent_service import AgentService
        from agaip.services.plugin_service import PluginService
        from agaip.services.task_service import TaskService

        self.container.register_singleton(TaskRepository, TaskRepository())
        self.container.register_singleton(AgentRepository, AgentRepository())
        self.container.register_singleton(UserRepository, UserRepository())

        # Register services
        self.container.register_singleton(AgentService, AgentService)
        self.container.register_singleton(TaskService, TaskService)
        self.container.register_singleton(PluginService, PluginService)

        # Register core components
        self.container.register_instance(Settings, self.settings)
        self.container.register_instance(EventBus, self.event_bus)
        self.container.register_instance(DatabaseManager, self.database_manager)

    async def _initialize_plugins(self) -> None:
        """Initialize the plugin system."""
        if not self.settings.plugins.enabled:
            return

        try:
            plugin_service = self.container.resolve(PluginService)
            await plugin_service.initialize()

            if self.settings.plugins.auto_discover:
                await plugin_service.discover_plugins()

        except Exception as e:
            logger.error(f"Failed to initialize plugins: {e}")
            if not self.settings.is_development:
                raise

    async def _initialize_agents(self) -> None:
        """Initialize agents from configuration."""
        try:
            agent_service = self.container.resolve(AgentService)
            await agent_service.initialize()

            # Load agents from configuration
            for agent_config in self.settings.agents.__dict__.items():
                if isinstance(agent_config[1], dict) and "plugin" in agent_config[1]:
                    await agent_service.register_agent_from_config(agent_config[1])

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            if not self.settings.is_development:
                raise

    async def _start_background_services(self) -> None:
        """Start background services and monitoring."""
        # Start health monitoring
        if self.settings.monitoring.health_check_enabled:
            asyncio.create_task(self._health_monitor_loop())

        # Start plugin hot reload if enabled
        if self.settings.plugins.hot_reload:
            asyncio.create_task(self._plugin_reload_loop())

    async def _stop_background_services(self) -> None:
        """Stop background services."""
        # Background tasks will be cancelled when the event loop stops
        pass

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Check database health
                db_health = await self.database_manager.health_check()
                if not db_health.get("healthy", False):
                    logger.warning("Database health check failed")

                # Check agent health
                agent_service = self.container.resolve(AgentService)
                await agent_service.health_check_all_agents()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    async def _plugin_reload_loop(self) -> None:
        """Background plugin reload monitoring."""
        while self._running:
            try:
                await asyncio.sleep(self.settings.plugins.reload_interval)

                plugin_service = self.container.resolve(PluginService)
                await plugin_service.check_for_updates()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in plugin reload: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if application is initialized."""
        return self._initialized

    @property
    def is_running(self) -> bool:
        """Check if application is running."""
        return self._running


# Global application instance
_application: Optional[AgaipApplication] = None


def get_application() -> AgaipApplication:
    """Get the global application instance."""
    global _application
    if _application is None:
        _application = AgaipApplication()
    return _application


async def create_application(settings: Optional[Settings] = None) -> AgaipApplication:
    """Create and initialize a new application instance."""
    app = AgaipApplication(settings)
    await app.initialize()
    return app
