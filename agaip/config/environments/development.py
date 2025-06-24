"""
Development environment configuration.

This module provides configuration overrides specifically for
development environment with debugging enabled and relaxed security.
"""

from agaip.config.settings import Environment, LogLevel, Settings


class DevelopmentSettings(Settings):
    """Development-specific configuration settings."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Override environment-specific settings
        self.environment = Environment.DEVELOPMENT
        self.debug = True

        # API Settings
        self.api.reload = True
        self.api.workers = 1
        self.api.cors_origins = ["*"]

        # Database Settings
        self.database.url = "sqlite://./data/agaip_dev.db"
        self.database.migrate_on_startup = True
        self.database.generate_schemas = True

        # Security Settings (Relaxed for development)
        self.security.jwt_secret_key = "dev-secret-key-not-for-production"
        self.security.default_api_key = "dev-api-key"
        self.security.rate_limit_enabled = False

        # Monitoring Settings
        self.monitoring.log_level = LogLevel.DEBUG
        self.monitoring.log_format = "text"  # More readable in development
        self.monitoring.metrics_enabled = True
        self.monitoring.tracing_enabled = False

        # Plugin Settings
        self.plugins.hot_reload = True
        self.plugins.reload_interval = 10  # Faster reload in dev

        # Redis Settings (Local development)
        self.redis.url = "redis://localhost:6379/0"

        # Celery Settings (Local development)
        self.celery.broker_url = "redis://localhost:6379/1"
        self.celery.result_backend = "redis://localhost:6379/2"
