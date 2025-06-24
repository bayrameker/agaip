"""
Modern configuration management using Pydantic Settings.

This module provides type-safe, environment-aware configuration management
with validation, documentation, and IDE support.
"""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseSettings(PydanticBaseSettings):
    """Database configuration settings."""

    url: str = Field(
        default="sqlite://./data/agaip.db", description="Database connection URL"
    )
    pool_min_size: int = Field(default=1, ge=1)
    pool_max_size: int = Field(default=10, ge=1)
    pool_max_queries: int = Field(default=50000, ge=1)
    pool_max_inactive_connection_lifetime: int = Field(default=300, ge=1)
    migrate_on_startup: bool = Field(default=True)
    generate_schemas: bool = Field(default=True)

    class Config:
        env_prefix = "DATABASE_"


class APISettings(PydanticBaseSettings):
    """API configuration settings."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    reload: bool = Field(default=False)
    version: str = Field(default="v1")

    # Documentation
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")

    # CORS
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    class Config:
        env_prefix = "API_"


class SecuritySettings(PydanticBaseSettings):
    """Security configuration settings."""

    # JWT
    jwt_secret_key: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production",
        description="JWT secret key for token signing",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)

    # API Keys
    api_key_header: str = Field(default="X-API-Key")
    default_api_key: str = Field(default="your-default-api-key-change-this")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=100, ge=1)
    rate_limit_burst: int = Field(default=20, ge=1)

    # Password Hashing
    password_hash_algorithm: str = Field(default="bcrypt")
    password_hash_rounds: int = Field(default=12, ge=4, le=20)

    class Config:
        env_prefix = "SECURITY_"


class RedisSettings(PydanticBaseSettings):
    """Redis configuration settings."""

    url: str = Field(default="redis://localhost:6379/0")
    password: Optional[str] = Field(default=None)
    ssl: bool = Field(default=False)
    pool_max_connections: int = Field(default=10, ge=1)

    # Cache
    cache_ttl: int = Field(default=300, ge=1)
    cache_prefix: str = Field(default="agaip:cache:")

    class Config:
        env_prefix = "REDIS_"


class CelerySettings(PydanticBaseSettings):
    """Celery task queue configuration."""

    broker_url: str = Field(default="redis://localhost:6379/1")
    result_backend: str = Field(default="redis://localhost:6379/2")
    task_serializer: str = Field(default="json")
    result_serializer: str = Field(default="json")
    accept_content: List[str] = Field(default=["json"])
    timezone: str = Field(default="UTC")
    enable_utc: bool = Field(default=True)

    # Task Queue
    task_queue_default: str = Field(default="agaip.tasks")
    task_queue_priority: str = Field(default="agaip.priority")
    task_queue_retry_delay: int = Field(default=60, ge=1)
    task_queue_max_retries: int = Field(default=3, ge=0)

    class Config:
        env_prefix = "CELERY_"


class MonitoringSettings(PydanticBaseSettings):
    """Monitoring and observability settings."""

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: str = Field(default="json")
    log_file_path: Optional[str] = Field(default="./logs/agaip.log")
    log_file_max_size: str = Field(default="10MB")
    log_file_backup_count: int = Field(default=5, ge=1)
    log_request_id_header: str = Field(default="X-Request-ID")

    # Metrics
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1, le=65535)
    metrics_path: str = Field(default="/metrics")
    prometheus_multiproc_dir: str = Field(default="./metrics")

    # Tracing
    tracing_enabled: bool = Field(default=False)
    tracing_endpoint: str = Field(default="http://localhost:14268/api/traces")
    tracing_service_name: str = Field(default="agaip")
    tracing_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # Health Check
    health_check_enabled: bool = Field(default=True)
    health_check_path: str = Field(default="/health")
    health_check_timeout: int = Field(default=30, ge=1)

    class Config:
        env_prefix = "MONITORING_"


class PluginSettings(PydanticBaseSettings):
    """Plugin system configuration."""

    enabled: bool = Field(default=True)
    auto_discover: bool = Field(default=True)
    directory: str = Field(default="./plugins")
    config_file: str = Field(default="./config/plugins.yaml")

    # Hot Reload
    hot_reload: bool = Field(default=True)
    reload_interval: int = Field(default=60, ge=1)

    class Config:
        env_prefix = "PLUGINS_"


class AgentSettings(PydanticBaseSettings):
    """Agent management configuration."""

    max_concurrent: int = Field(default=10, ge=1)
    default_timeout: int = Field(default=300, ge=1)
    heartbeat_interval: int = Field(default=30, ge=1)
    auto_restart: bool = Field(default=True)

    # Agent Storage
    state_storage: str = Field(default="redis")
    state_ttl: int = Field(default=3600, ge=1)

    class Config:
        env_prefix = "AGENTS_"


class Settings(PydanticBaseSettings):
    """Main application settings."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # Application Info
    app_name: str = Field(default="Agaip Framework")
    app_version: str = Field(default="3.0.0")
    app_description: str = Field(
        default="Super Power Agentic AI Framework - Global, scalable, and modern AI agent framework"
    )

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    agents: AgentSettings = Field(default_factory=AgentSettings)

    @validator("environment", pre=True)
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.environment == Environment.TESTING

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
