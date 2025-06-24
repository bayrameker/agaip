"""
User repository for the Agaip framework.

This module provides specialized data access methods for User model
including authentication, authorization, and user management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import secrets

from agaip.database.models.user import User, UserRole, UserStatus
from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for User model with specialized operations."""
    
    def __init__(self):
        super().__init__(User)
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        **kwargs
    ) -> User:
        """Create a new user with hashed password."""
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": is_active,
            "status": UserStatus.ACTIVE if is_active else UserStatus.PENDING,
            **kwargs
        }
        
        user = User(**user_data)
        user.set_password(password)
        await user.save()
        
        return user
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by_field("username", username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by_field("email", email)
    
    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        return await self.get_by_field("api_key", api_key)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # Try to find user by username or email
        user = await self.get_by_username(username)
        if not user:
            user = await self.get_by_email(username)
        
        if not user:
            return None
        
        # Check if account is locked
        if user.is_locked:
            return None
        
        # Verify password
        if not user.verify_password(password):
            await user.record_failed_login()
            return None
        
        # Check if user can login
        if not user.can_login:
            return None
        
        # Record successful login
        await user.record_login()
        return user
    
    async def get_active_users(self, role: Optional[UserRole] = None) -> List[User]:
        """Get all active users, optionally filtered by role."""
        queryset = self.model_class.filter(
            is_active=True,
            status=UserStatus.ACTIVE
        )
        
        if role:
            queryset = queryset.filter(role=role)
        
        return await queryset.order_by("username")
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        return await self.model_class.filter(role=role)
    
    async def get_locked_users(self) -> List[User]:
        """Get all currently locked users."""
        now = datetime.utcnow()
        return await self.model_class.filter(
            locked_until__gt=now
        )
    
    async def generate_api_key(self, user_id: UUID, expires_in_days: int = 365) -> str:
        """Generate a new API key for user."""
        user = await self.get_by_id_or_raise(user_id)
        
        # Generate secure API key
        api_key = f"agaip_{secrets.token_urlsafe(32)}"
        
        # Set expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        user.api_key = api_key
        user.api_key_expires_at = expires_at
        await user.save(update_fields=['api_key', 'api_key_expires_at'])
        
        return api_key
    
    async def revoke_api_key(self, user_id: UUID) -> bool:
        """Revoke user's API key."""
        user = await self.get_by_id(user_id)
        if user and user.api_key:
            user.api_key = None
            user.api_key_expires_at = None
            await user.save(update_fields=['api_key', 'api_key_expires_at'])
            return True
        return False
    
    async def change_password(self, user_id: UUID, new_password: str) -> bool:
        """Change user password."""
        user = await self.get_by_id(user_id)
        if user:
            user.set_password(new_password)
            await user.save(update_fields=['password_hash', 'password_changed_at'])
            return True
        return False
    
    async def update_user_role(self, user_id: UUID, new_role: UserRole) -> bool:
        """Update user role."""
        user = await self.get_by_id(user_id)
        if user:
            user.role = new_role
            await user.save(update_fields=['role'])
            return True
        return False
    
    async def add_user_permission(self, user_id: UUID, permission: str) -> bool:
        """Add permission to user."""
        user = await self.get_by_id(user_id)
        if user:
            user.add_permission(permission)
            await user.save(update_fields=['permissions'])
            return True
        return False
    
    async def remove_user_permission(self, user_id: UUID, permission: str) -> bool:
        """Remove permission from user."""
        user = await self.get_by_id(user_id)
        if user:
            removed = user.remove_permission(permission)
            if removed:
                await user.save(update_fields=['permissions'])
            return removed
        return False
    
    async def unlock_user(self, user_id: UUID) -> bool:
        """Unlock a locked user account."""
        user = await self.get_by_id(user_id)
        if user and user.is_locked:
            await user.unlock_account()
            return True
        return False
    
    async def suspend_user(self, user_id: UUID) -> bool:
        """Suspend a user account."""
        user = await self.get_by_id(user_id)
        if user:
            await user.suspend()
            return True
        return False
    
    async def activate_user(self, user_id: UUID) -> bool:
        """Activate a user account."""
        user = await self.get_by_id(user_id)
        if user:
            await user.activate()
            return True
        return False
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics for admin dashboard."""
        total_users = await self.count()
        active_users = await self.count(is_active=True, status=UserStatus.ACTIVE)
        suspended_users = await self.count(status=UserStatus.SUSPENDED)
        pending_users = await self.count(status=UserStatus.PENDING)
        
        # Count by role
        admin_count = await self.count(role=UserRole.ADMIN)
        user_count = await self.count(role=UserRole.USER)
        viewer_count = await self.count(role=UserRole.VIEWER)
        api_client_count = await self.count(role=UserRole.API_CLIENT)
        
        # Recent activity
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_logins = await self.count(last_login__gte=last_week)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "suspended_users": suspended_users,
            "pending_users": pending_users,
            "admin_count": admin_count,
            "user_count": user_count,
            "viewer_count": viewer_count,
            "api_client_count": api_client_count,
            "recent_logins": recent_logins,
        }
    
    async def cleanup_expired_api_keys(self) -> int:
        """Clean up expired API keys."""
        now = datetime.utcnow()
        users_with_expired_keys = await self.model_class.filter(
            api_key__isnull=False,
            api_key_expires_at__lt=now
        )
        
        count = 0
        for user in users_with_expired_keys:
            user.api_key = None
            user.api_key_expires_at = None
            count += 1
        
        if users_with_expired_keys:
            await self.model_class.bulk_update(
                users_with_expired_keys, 
                ['api_key', 'api_key_expires_at']
            )
        
        return count
    
    async def get_recent_users(self, days: int = 7, limit: int = 10) -> List[User]:
        """Get recently registered users."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return await self.model_class.filter(
            created_at__gte=cutoff_date
        ).order_by("-created_at").limit(limit)
