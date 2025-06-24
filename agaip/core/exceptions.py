"""
Core exceptions for the Agaip framework.

This module defines custom exception classes used throughout the framework
to provide clear error handling and debugging information.
"""

from typing import Any, Dict, Optional


class AgaipException(Exception):
    """Base exception class for all Agaip framework exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class ConfigurationError(AgaipException):
    """Raised when there's an error in configuration."""

    pass


class PluginError(AgaipException):
    """Raised when there's an error with plugin operations."""

    pass


class AgentError(AgaipException):
    """Raised when there's an error with agent operations."""

    pass


class DatabaseError(AgaipException):
    """Raised when there's a database-related error."""

    pass


class AuthenticationError(AgaipException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AgaipException):
    """Raised when authorization fails."""

    pass


class ValidationError(AgaipException):
    """Raised when data validation fails."""

    pass


class TaskError(AgaipException):
    """Raised when there's an error with task processing."""

    pass


class ServiceUnavailableError(AgaipException):
    """Raised when a required service is unavailable."""

    pass


class RateLimitError(AgaipException):
    """Raised when rate limit is exceeded."""

    pass
