"""
Environment-specific configuration module.

This module provides environment-specific configuration overrides
for development, testing, staging, and production environments.
"""

from enum import Enum

from .development import DevelopmentSettings
from .production import ProductionSettings
from .testing import TestingSettings


class Environment(str, Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


__all__ = [
    "Environment",
    "DevelopmentSettings",
    "ProductionSettings",
    "TestingSettings",
]
