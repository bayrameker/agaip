"""
Testing environment configuration.

This module provides configuration overrides specifically for
testing environment with isolated resources and fast execution.
"""

from agaip.config.settings import Environment, LogLevel, Settings


class TestingSettings(Settings):
    """Testing-specific configuration settings."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Override environment-specific settings
        self.environment = Environment.TESTING
        self.debug = True

        # API Settings
        self.api.reload = False
        self.api.workers = 1

        # Database Settings (In-memory for testing)
        self.database.url = "sqlite://:memory:"
        self.database.migrate_on_startup = True
        self.database.generate_schemas = True
        self.database.pool_min_size = 1
        self.database.pool_max_size = 1

        # Security Settings (Relaxed for testing)
        self.security.jwt_secret_key = "test-secret-key"
        self.security.default_api_key = "test-api-key"
        self.security.rate_limit_enabled = False
        self.security.jwt_access_token_expire_minutes = 5  # Short for testing

        # Monitoring Settings
        self.monitoring.log_level = LogLevel.WARNING  # Reduce noise in tests
        self.monitoring.log_format = "text"
        self.monitoring.metrics_enabled = False
        self.monitoring.tracing_enabled = False
        self.monitoring.health_check_enabled = False

        # Plugin Settings
        self.plugins.hot_reload = False
        self.plugins.auto_discover = False  # Manual plugin loading in tests

        # Redis Settings (Test database)
        self.redis.url = "redis://localhost:6379/15"
        self.redis.cache_ttl = 10  # Short TTL for testing

        # Celery Settings (Test queues)
        self.celery.broker_url = "redis://localhost:6379/14"
        self.celery.result_backend = "redis://localhost:6379/13"
        self.celery.task_queue_retry_delay = 1  # Fast retries in tests
        self.celery.task_queue_max_retries = 1

        # Agent Settings
        self.agents.max_concurrent = 2  # Limited for testing
        self.agents.default_timeout = 10  # Short timeout for tests
        self.agents.heartbeat_interval = 5
