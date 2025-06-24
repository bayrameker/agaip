"""
User model for the Agaip framework.

This module defines the User model for authentication,
authorization, and user management.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from tortoise import fields
from tortoise.exceptions import ValidationError
from passlib.context import CryptContext

from .base import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class UserStatus(str, Enum):
    """User status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """User model for authentication and authorization."""
    
    # Basic user information
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    full_name = fields.CharField(max_length=255, null=True)
    
    # Authentication
    password_hash = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    is_verified = fields.BooleanField(default=False)
    
    # Authorization
    role = fields.CharEnumField(UserRole, default=UserRole.USER)
    permissions = fields.JSONField(default=list)
    
    # Status and tracking
    status = fields.CharEnumField(UserStatus, default=UserStatus.PENDING)
    last_login = fields.DatetimeField(null=True)
    login_count = fields.IntField(default=0)
    
    # API access
    api_key = fields.CharField(max_length=255, null=True, unique=True)
    api_key_expires_at = fields.DatetimeField(null=True)
    rate_limit_per_minute = fields.IntField(default=100)
    
    # Profile information
    avatar_url = fields.CharField(max_length=500, null=True)
    timezone = fields.CharField(max_length=50, default="UTC")
    language = fields.CharField(max_length=10, default="en")
    
    # Security
    failed_login_attempts = fields.IntField(default=0)
    locked_until = fields.DatetimeField(null=True)
    password_changed_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "users"
        indexes = [
            ["username"],
            ["email"],
            ["api_key"],
            ["status", "is_active"],
        ]
    
    def set_password(self, password: str) -> None:
        """Set user password with hashing."""
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def verify_password(self, password: str) -> bool:
        """Verify user password."""
        return pwd_context.verify(password, self.password_hash)
    
    async def record_login(self) -> None:
        """Record successful login."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.failed_login_attempts = 0
        await self.save(update_fields=['last_login', 'login_count', 'failed_login_attempts'])
    
    async def record_failed_login(self) -> None:
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        await self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    async def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
        await self.save(update_fields=['locked_until', 'failed_login_attempts'])
    
    async def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.status = UserStatus.ACTIVE
        await self.save(update_fields=['is_active', 'status'])
    
    async def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.status = UserStatus.INACTIVE
        await self.save(update_fields=['is_active', 'status'])
    
    async def suspend(self) -> None:
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        await self.save(update_fields=['status'])
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the user."""
        if self.permissions is None:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str) -> bool:
        """Remove a permission from the user."""
        if self.permissions is None:
            return False
        if permission in self.permissions:
            self.permissions.remove(permission)
            return True
        return False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.role == UserRole.ADMIN:
            return True  # Admins have all permissions
        
        return self.permissions is not None and permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(self.has_permission(perm) for perm in permissions)
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def can_login(self) -> bool:
        """Check if user can login."""
        return (
            self.is_active and 
            not self.is_locked and 
            self.status in [UserStatus.ACTIVE, UserStatus.PENDING]
        )
    
    @property
    def display_name(self) -> str:
        """Get user display name."""
        return self.full_name or self.username
    
    def to_dict(self, exclude_fields: Optional[list] = None, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary."""
        exclude_fields = exclude_fields or []
        
        # Always exclude sensitive fields unless explicitly requested
        if not include_sensitive:
            exclude_fields.extend(['password_hash', 'api_key'])
        
        data = super().to_dict(exclude_fields)
        
        # Add computed fields
        data['is_locked'] = self.is_locked
        data['is_admin'] = self.is_admin
        data['can_login'] = self.can_login
        data['display_name'] = self.display_name
        
        return data
