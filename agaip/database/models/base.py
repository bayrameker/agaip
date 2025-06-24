"""
Base model class for the Agaip framework.

This module provides a base model class with common fields,
methods, and functionality for all database models.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from tortoise import fields, models
from tortoise.exceptions import ValidationError


class BaseModel(models.Model):
    """Base model class with common fields and methods."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Soft delete support
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)

    # Metadata
    metadata = fields.JSONField(default=dict)

    class Meta:
        abstract = True

    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        exclude_fields = exclude_fields or []
        data = {}

        for field_name in self._meta.fields:
            if field_name in exclude_fields:
                continue

            value = getattr(self, field_name)

            # Handle special types
            if isinstance(value, datetime):
                data[field_name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                data[field_name] = str(value)
            else:
                data[field_name] = value

        return data

    @classmethod
    async def get_or_none_by_id(cls, id: Any) -> Optional["BaseModel"]:
        """Get model by ID or return None if not found."""
        try:
            return await cls.get(id=id, is_deleted=False)
        except cls.DoesNotExist:
            return None

    @classmethod
    async def get_active(cls, **kwargs) -> "BaseModel":
        """Get active (non-deleted) model instance."""
        return await cls.get(is_deleted=False, **kwargs)

    @classmethod
    async def filter_active(cls, **kwargs):
        """Filter active (non-deleted) model instances."""
        return cls.filter(is_deleted=False, **kwargs)

    async def soft_delete(self) -> None:
        """Soft delete the model instance."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        await self.save(update_fields=["is_deleted", "deleted_at"])

    async def restore(self) -> None:
        """Restore a soft-deleted model instance."""
        self.is_deleted = False
        self.deleted_at = None
        await self.save(update_fields=["is_deleted", "deleted_at"])

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def remove_metadata(self, key: str) -> bool:
        """Remove a metadata key."""
        if self.metadata is None:
            return False

        if key in self.metadata:
            del self.metadata[key]
            return True
        return False

    async def refresh_from_db(self) -> None:
        """Refresh the model instance from database."""
        fresh_instance = await self.__class__.get(id=self.id)
        for field_name in self._meta.fields:
            setattr(self, field_name, getattr(fresh_instance, field_name))

    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(id={self.id})"

    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}(id={self.id}, created_at={self.created_at})"
