"""
FastAPI dependencies for the Agaip framework.

This module provides dependency injection functions for
authentication, database access, and other common requirements.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agaip.config.settings import Settings, get_settings
from agaip.core.container import get_container
from agaip.database.connection import get_database_manager
from agaip.database.models.user import User
from agaip.database.repositories.user import UserRepository

security = HTTPBearer(auto_error=False)


async def get_database():
    """Get database manager dependency."""
    return get_database_manager()


def get_settings_dependency() -> Settings:
    """Get settings dependency."""
    return get_settings()


def get_container_dependency():
    """Get dependency injection container."""
    return get_container()


async def get_user_repository() -> UserRepository:
    """Get user repository dependency."""
    container = get_container_dependency()
    return container.resolve(UserRepository)


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings_dependency),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Optional[User]:
    """Verify API key authentication."""
    if not credentials:
        return None

    # Check if it's the default API key
    if credentials.credentials == settings.security.default_api_key:
        # Return a system user for default API key
        return User(
            username="system", email="system@agaip.local", role="admin", is_active=True
        )

    # Look up user by API key
    user = await user_repo.get_by_api_key(credentials.credentials)
    if not user or not user.can_login:
        return None

    return user


async def get_current_user(user: Optional[User] = Depends(verify_api_key)) -> User:
    """Get current authenticated user (required)."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_optional(
    user: Optional[User] = Depends(verify_api_key),
) -> Optional[User]:
    """Get current authenticated user (optional)."""
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def require_permission(permission: str):
    """Create a dependency that requires a specific permission."""

    async def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return current_user

    return permission_checker
