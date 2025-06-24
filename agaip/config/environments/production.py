"""
Production environment configuration.

This module provides configuration overrides specifically for
production environment with security hardening and performance optimization.
"""

from agaip.config.settings import Settings, Environment, LogLevel


class ProductionSettings(Settings):
    """Production-specific configuration settings."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Override environment-specific settings
        self.environment = Environment.PRODUCTION
        self.debug = False
        
        # API Settings
        self.api.reload = False
        self.api.workers = 4  # Multiple workers for production
        self.api.docs_url = None  # Disable docs in production
        self.api.redoc_url = None
        self.api.openapi_url = None
        
        # Database Settings
        self.database.migrate_on_startup = False  # Manual migrations in prod
        self.database.pool_max_size = 20
        self.database.pool_min_size = 5
        
        # Security Settings (Hardened for production)
        self.security.rate_limit_enabled = True
        self.security.rate_limit_requests_per_minute = 60  # Stricter rate limiting
        self.security.jwt_access_token_expire_minutes = 15  # Shorter token lifetime
        
        # Monitoring Settings
        self.monitoring.log_level = LogLevel.INFO
        self.monitoring.log_format = "json"  # Structured logging for production
        self.monitoring.metrics_enabled = True
        self.monitoring.tracing_enabled = True
        self.monitoring.tracing_sample_rate = 0.01  # Lower sampling in production
        
        # Plugin Settings
        self.plugins.hot_reload = False  # No hot reload in production
        
        # Performance optimizations
        self.agents.max_concurrent = 50  # Higher concurrency in production
