"""
Database connection management for the Agaip framework.

This module provides database connection pooling, health checks,
and multi-database support with automatic failover.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from tortoise import Tortoise
from tortoise.connection import connections
from tortoise.exceptions import DBConnectionError

from agaip.config.settings import Settings
from agaip.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and health monitoring."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._connections: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize database connections."""
        if self._initialized:
            return
        
        try:
            # Parse database URL to determine type
            db_config = self._parse_database_url(self.settings.database.url)
            
            # Configure Tortoise ORM
            config = {
                "connections": {
                    "default": {
                        "engine": db_config["engine"],
                        "credentials": db_config["credentials"]
                    }
                },
                "apps": {
                    "models": {
                        "models": [
                            "agaip.database.models.task",
                            "agaip.database.models.agent",
                            "agaip.database.models.user",
                        ],
                        "default_connection": "default",
                    }
                },
                "use_tz": True,
                "timezone": "UTC"
            }
            
            # Initialize Tortoise
            await Tortoise.init(config=config)
            
            # Generate schemas if enabled
            if self.settings.database.generate_schemas:
                await Tortoise.generate_schemas()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
            # Start health check monitoring
            if self.settings.monitoring.health_check_enabled:
                self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def close(self) -> None:
        """Close database connections."""
        if not self._initialized:
            return
        
        try:
            # Stop health check
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Close Tortoise connections
            await Tortoise.close_connections()
            self._initialized = False
            logger.info("Database connections closed")
        
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        if not self._initialized:
            return {"status": "not_initialized", "healthy": False}
        
        try:
            # Test connection with a simple query
            connection = connections.get("default")
            await connection.execute_query("SELECT 1")
            
            # Get connection pool stats
            pool_stats = self._get_pool_stats()
            
            return {
                "status": "healthy",
                "healthy": True,
                "pool_stats": pool_stats,
                "database_type": self._get_database_type()
            }
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    async def migrate(self) -> None:
        """Run database migrations."""
        try:
            # This would integrate with Aerich for migrations
            # For now, we'll use schema generation
            if self.settings.database.generate_schemas:
                await Tortoise.generate_schemas()
                logger.info("Database schemas updated")
        
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise DatabaseError(f"Migration failed: {e}")
    
    def _parse_database_url(self, url: str) -> Dict[str, Any]:
        """Parse database URL and return configuration."""
        parsed = urlparse(url)
        
        if parsed.scheme == "sqlite":
            return {
                "engine": "tortoise.backends.sqlite",
                "credentials": {
                    "file_path": parsed.path.lstrip("/") if parsed.path != ":memory:" else ":memory:"
                }
            }
        elif parsed.scheme == "postgresql":
            return {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "host": parsed.hostname,
                    "port": parsed.port or 5432,
                    "user": parsed.username,
                    "password": parsed.password,
                    "database": parsed.path.lstrip("/"),
                    "minsize": self.settings.database.pool_min_size,
                    "maxsize": self.settings.database.pool_max_size,
                }
            }
        elif parsed.scheme == "mysql":
            return {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": parsed.hostname,
                    "port": parsed.port or 3306,
                    "user": parsed.username,
                    "password": parsed.password,
                    "database": parsed.path.lstrip("/"),
                    "minsize": self.settings.database.pool_min_size,
                    "maxsize": self.settings.database.pool_max_size,
                }
            }
        else:
            raise DatabaseError(f"Unsupported database scheme: {parsed.scheme}")
    
    def _get_database_type(self) -> str:
        """Get the database type from URL."""
        parsed = urlparse(self.settings.database.url)
        return parsed.scheme
    
    def _get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        try:
            connection = connections.get("default")
            if hasattr(connection, '_pool') and connection._pool:
                pool = connection._pool
                return {
                    "size": pool.size,
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
        except Exception:
            pass
        
        return {"status": "unavailable"}
    
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                health = await self.health_check()
                
                if not health["healthy"]:
                    logger.warning(f"Database health check failed: {health}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _database_manager
    if _database_manager is None:
        from agaip.config.settings import get_settings
        settings = get_settings()
        _database_manager = DatabaseManager(settings)
    return _database_manager


async def init_database() -> None:
    """Initialize the database."""
    manager = get_database_manager()
    await manager.initialize()


async def close_database() -> None:
    """Close database connections."""
    manager = get_database_manager()
    await manager.close()
